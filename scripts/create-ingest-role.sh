#!/bin/bash

# Create/patch the IAM role for the mcp-s3-ingest Lambda function (todo 2842, round 6).
#
# Same out-of-band pattern as scripts/create-lambda-role.sh and
# analytics/create-logs-processor-role.sh: an account admin runs this once per AWS
# account, and template.yaml's S3IngestFunction references the resulting role by name
# (mcp-s3-ingest-role) rather than owning it as a CloudFormation resource: the CI
# deploy role only has iam:PassRole, not iam:CreateRole/iam:PutRolePolicy.
#
# Deliberately a dedicated role instead of reusing mcp-server-lambda-execution-role:
# its only job is PutObject into the two allowlisted prefixes below, so it carries
# nothing like that role's broader AWSLambdaExecute (s3:PutObject on arn:aws:s3:::*)
# grant, and its permissions are asserted here instead of assumed. Run once per
# account with that account's own bucket names (prod and staging use different
# buckets in both ANALYTICS_LOGS_BUCKET and CDN_BUCKET_NAME).

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

ROLE_NAME="mcp-s3-ingest-role"
BASIC_EXECUTION_POLICY_ARN="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
INLINE_POLICY_NAME="MCPS3IngestAccess"

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

if [ -z "$ANALYTICS_LOGS_BUCKET" ] || [ -z "$CDN_BUCKET_NAME" ]; then
    echo "❌ Error: ANALYTICS_LOGS_BUCKET and CDN_BUCKET_NAME must both be set to this"
    echo "   account's bucket names (e.g. via .env) before running this script."
    exit 1
fi

echo "🔑 Managing Lambda execution role: $ROLE_NAME"
echo "Analytics bucket: $ANALYTICS_LOGS_BUCKET"
echo "CDN bucket: $CDN_BUCKET_NAME"
echo ""

TRUST_POLICY='{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}'

if ROLE_ARN=$(aws iam create-role $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --query "Role.Arn" \
    --output text 2>/dev/null); then
    echo "Role created successfully!"
else
    echo "Role already exists, continuing with policy attachment..."
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query "Account" --output text)
    ROLE_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:role/${ROLE_NAME}"
fi
echo "Role ARN: $ROLE_ARN"
echo ""

echo "📎 Attaching AWSLambdaBasicExecutionRole policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --policy-arn "$BASIC_EXECUTION_POLICY_ARN"

echo "📎 Putting inline least-privilege S3 write policy ($INLINE_POLICY_NAME)..."
INLINE_POLICY=$(cat <<JSON
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "WriteAnalyticsJsonl",
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::${ANALYTICS_LOGS_BUCKET}/jsonl/*"
    },
    {
      "Sid": "WriteCdnMcpResponses",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:PutObjectTagging"],
      "Resource": "arn:aws:s3:::${CDN_BUCKET_NAME}/mcp-responses/*"
    }
  ]
}
JSON
)
aws iam put-role-policy $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --policy-name "$INLINE_POLICY_NAME" \
    --policy-document "$INLINE_POLICY"

echo ""
echo "✅ mcp-s3-ingest IAM role setup complete!"
echo "Role ARN: $ROLE_ARN"
echo ""
echo "This role provides:"
echo "- Basic Lambda execution permissions (CloudWatch Logs)"
echo "- s3:PutObject on arn:aws:s3:::${ANALYTICS_LOGS_BUCKET}/jsonl/*"
echo "- s3:PutObject + s3:PutObjectTagging on arn:aws:s3:::${CDN_BUCKET_NAME}/mcp-responses/*"
echo ""
echo "Run once per AWS account (staging and prod each pass their own bucket names)"
echo "before the first deploy that includes S3IngestFunction; template.yaml references"
echo "this role by name and does not create it."
