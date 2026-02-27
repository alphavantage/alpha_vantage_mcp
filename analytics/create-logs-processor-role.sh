#!/bin/bash

# Create IAM role for CloudWatch Logs processor Lambda
# This script creates the necessary IAM role and policy for the Lambda function

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

# Get AWS account ID and region
ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query Account --output text)
REGION=$(aws configure get region $AWS_PROFILE_OPTION || echo "us-east-1")

echo "🔑 Creating IAM role for CloudWatch Logs processor Lambda..."
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo ""

ROLE_NAME="LogsProcessorRole-mcp"
BASIC_EXECUTION_POLICY_ARN="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
S3_POLICY_ARN="arn:aws:iam::aws:policy/AmazonS3FullAccess"

# Check for existing role
echo "Checking for existing role..."
EXISTING_ROLE=$(aws iam get-role $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --query "Role.Arn" --output text 2>/dev/null || echo "")

if [ ! -z "$EXISTING_ROLE" ] && [ "$EXISTING_ROLE" != "None" ]; then
    echo "Found existing role:"
    echo "Role ARN: $EXISTING_ROLE"

    # Check if policies are attached
    echo "Checking policy attachments..."
    BASIC_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$BASIC_EXECUTION_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")
    S3_POLICY_ATTACHED=$(aws iam list-attached-role-policies $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --query "AttachedPolicies[?PolicyArn=='$S3_POLICY_ARN'].PolicyArn" --output text 2>/dev/null || echo "")

    if [ ! -z "$BASIC_POLICY_ATTACHED" ] && [ ! -z "$S3_POLICY_ATTACHED" ]; then
        echo "✅ Role already exists with all policies attached!"
        echo "Role ARN: $EXISTING_ROLE"
        echo ""
        echo "This role provides:"
        echo "- Basic Lambda execution permissions"
        echo "- S3 full access for log delivery"
        echo "- CloudWatch Logs access"
        echo ""
        echo "Role is ready to use in your Lambda functions."
        exit 0
    else
        echo "Role exists but some policies not attached. Attaching missing policies..."
        if [ -z "$BASIC_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --policy-arn "$BASIC_EXECUTION_POLICY_ARN"
            echo "✅ AWSLambdaBasicExecutionRole attached!"
        fi
        if [ -z "$S3_POLICY_ATTACHED" ]; then
            aws iam attach-role-policy $AWS_PROFILE_OPTION --role-name "$ROLE_NAME" --policy-arn "$S3_POLICY_ARN"
            echo "✅ AmazonS3FullAccess attached!"
        fi
        echo "Role ARN: $EXISTING_ROLE"
        echo ""
        echo "This role provides:"
        echo "- Basic Lambda execution permissions"
        echo "- S3 full access for log delivery"
        echo "- CloudWatch Logs access"
        echo ""
        echo "Role is ready to use in your Lambda functions."
        exit 0
    fi
fi

echo "No existing role found. Creating new role..."

# Trust policy document
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

# Create role (ignore if it already exists)
if ROLE_ARN=$(aws iam create-role $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$TRUST_POLICY" \
    --query "Role.Arn" \
    --output text 2>/dev/null); then
    echo "Role created successfully!"
    echo "Role ARN: $ROLE_ARN"
else
    echo "Role already exists, continuing with policy attachment..."
    # Construct the expected ARN format
    ROLE_ARN="arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME"
    echo "Using role ARN: $ROLE_ARN"
fi
echo ""

# Attach managed policies to role
echo "📎 Attaching managed policies..."

# Attach basic Lambda execution role policy
echo "Attaching AWSLambdaBasicExecutionRole..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --policy-arn "$BASIC_EXECUTION_POLICY_ARN"

# Attach S3 full access for log delivery
echo "Attaching AmazonS3FullAccess policy..."
aws iam attach-role-policy $AWS_PROFILE_OPTION \
    --role-name "$ROLE_NAME" \
    --policy-arn "$S3_POLICY_ARN"

echo "✅ CloudWatch Logs processor IAM role setup complete!"
echo "Role ARN: $ROLE_ARN"
echo ""
echo "This role provides:"
echo "- Basic Lambda execution permissions"
echo "- S3 full access for log delivery"
echo "- CloudWatch Logs access"
echo ""
echo "Role is ready to use in your CloudFormation templates and Lambda functions."
