#!/bin/bash

# Create/patch the IAM role for the mcp-s3-ingest Lambda function (todo 2842, rounds 6-7).
#
# Same out-of-band pattern as scripts/create-lambda-role.sh and
# analytics/create-logs-processor-role.sh: an account admin (or, in prod, the SSO
# principal that can CreateRole/CreatePolicy/AttachRolePolicy) runs this once per
# AWS account, and template.yaml's S3IngestFunction references the resulting role
# by name (default mcp-s3-ingest-role, overridable via S3IngestRoleName) rather
# than owning it as a CloudFormation resource: the CI deploy role only has
# iam:PassRole, not iam:CreateRole.
#
# Deliberately a dedicated role instead of reusing mcp-server-lambda-execution-role:
# its only job is PutObject into the two allowlisted prefixes below, so it carries
# nothing like that role's broader AWSLambdaExecute (s3:PutObject on arn:aws:s3:::*)
# grant, and its permissions are asserted here instead of assumed. Run once per
# account with that account's own bucket names (prod and staging use different
# buckets in both ANALYTICS_LOGS_BUCKET and CDN_BUCKET_NAME).
#
# POLICY_MODE selects how the least-privilege grant is bound:
#   inline  (default)  iam:PutRolePolicy with the JSON below. Works in staging;
#                      denied in prod (custom SSO permission set).
#   managed            iam:CreatePolicy + iam:AttachRolePolicy with the same JSON
#                      as a customer-managed policy named MCPS3IngestAccess.
#                      Create-only: iam:CreatePolicyVersion is denied in prod, so
#                      re-runs tolerate EntityAlreadyExists and never update.
# Optional S3_POLICY_ARN (managed mode only): skip CreatePolicy and attach that
# ARN instead (fallback: arn:aws:iam::aws:policy/AmazonS3FullAccess). No IAM
# *read* appears on the managed path (prod denies GetPolicy/List* etc.).

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

ROLE_NAME="mcp-s3-ingest-role"
BASIC_EXECUTION_POLICY_ARN="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
POLICY_NAME="MCPS3IngestAccess"
POLICY_MODE="${POLICY_MODE:-inline}"

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

case "$POLICY_MODE" in
    inline|managed) ;;
    *)
        echo "❌ Error: POLICY_MODE must be 'inline' or 'managed' (got: $POLICY_MODE)"
        exit 1
        ;;
esac

echo "🔑 Managing Lambda execution role: $ROLE_NAME"
echo "Analytics bucket: $ANALYTICS_LOGS_BUCKET"
echo "CDN bucket: $CDN_BUCKET_NAME"
echo "Policy mode: $POLICY_MODE"
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

# Single least-privilege document for both modes (and for the S3_POLICY_ARN skip path
# we still print the intended grant so the operator knows what was intended).
INGEST_POLICY=$(cat <<JSON
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

if [ "$POLICY_MODE" = "inline" ]; then
    echo "📎 Putting inline least-privilege S3 write policy ($POLICY_NAME)..."
    aws iam put-role-policy $AWS_PROFILE_OPTION \
        --role-name "$ROLE_NAME" \
        --policy-name "$POLICY_NAME" \
        --policy-document "$INGEST_POLICY"
    GRANT_DESC="inline policy $POLICY_NAME"
elif [ -n "$S3_POLICY_ARN" ]; then
    echo "📎 Attaching override managed policy ($S3_POLICY_ARN)..."
    aws iam attach-role-policy $AWS_PROFILE_OPTION \
        --role-name "$ROLE_NAME" \
        --policy-arn "$S3_POLICY_ARN"
    GRANT_DESC="override managed policy $S3_POLICY_ARN"
else
    # Create-only customer-managed policy. No pre-check reads (GetPolicy/ListPolicies
    # are denied in prod); tolerate EntityAlreadyExists on re-run. Never call
    # CreatePolicyVersion: that action is denied in prod and would also mutate a
    # policy that other accounts may already depend on.
    echo "📎 Creating customer-managed least-privilege policy ($POLICY_NAME)..."
    if POLICY_ARN=$(aws iam create-policy $AWS_PROFILE_OPTION \
        --policy-name "$POLICY_NAME" \
        --policy-document "$INGEST_POLICY" \
        --query "Policy.Arn" \
        --output text 2>/dev/null); then
        echo "Policy created successfully!"
    else
        echo "Policy already exists (EntityAlreadyExists), attaching existing ARN..."
        if [ -z "$AWS_ACCOUNT_ID" ]; then
            AWS_ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query "Account" --output text)
        fi
        POLICY_ARN="arn:aws:iam::${AWS_ACCOUNT_ID}:policy/${POLICY_NAME}"
    fi
    echo "Policy ARN: $POLICY_ARN"
    echo "📎 Attaching managed policy to role..."
    aws iam attach-role-policy $AWS_PROFILE_OPTION \
        --role-name "$ROLE_NAME" \
        --policy-arn "$POLICY_ARN"
    GRANT_DESC="customer-managed policy $POLICY_NAME ($POLICY_ARN)"
fi

echo ""
echo "✅ mcp-s3-ingest IAM role setup complete!"
echo "Role ARN: $ROLE_ARN"
echo "Grant: $GRANT_DESC"
echo ""
echo "This role provides:"
echo "- Basic Lambda execution permissions (CloudWatch Logs)"
echo "- s3:PutObject on arn:aws:s3:::${ANALYTICS_LOGS_BUCKET}/jsonl/*"
echo "- s3:PutObject + s3:PutObjectTagging on arn:aws:s3:::${CDN_BUCKET_NAME}/mcp-responses/*"
if [ "$POLICY_MODE" = "managed" ] && [ -z "$S3_POLICY_ARN" ]; then
    echo ""
    echo "Note (managed mode): the customer-managed policy is create-only. Changing"
    echo "the grant later requires a new policy name (e.g. ${POLICY_NAME}-v2) and a"
    echo "fresh attach; this script never calls CreatePolicyVersion."
fi
echo ""
echo "Run once per AWS account (staging and prod each pass their own bucket names)"
echo "before the first deploy that includes S3IngestFunction; template.yaml references"
echo "this role by name (S3IngestRoleName, default mcp-s3-ingest-role) and does not create it."
