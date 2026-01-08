#!/bin/bash

# AWS SAM deployment script for Streamable HTTP MCP Lambda function
AWS_PROFILE=${AWS_PROFILE:-default}

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

echo "🚀 Starting deployment of MCP Lambda function..."

# Check if uv is available for dependency resolution (required)
if command -v uv &> /dev/null; then
    echo "📦 Using uv for package management..."
    # Export without the editable package for Lambda deployment
    cd server && uv export --format=requirements-txt --no-hashes | grep -v "^-e \." > requirements.txt && cd ..
else
    echo "❌ Error: uv is required for deployment but not found in PATH"
    echo "Please install uv: https://github.com/astral-sh/uv"
    exit 1
fi

echo "🏗️  Building SAM application..."
sam build

# Function to add parameter overrides
add_param() {
    local param_name="$1"
    local env_var="$2"
    if [ -n "${!env_var}" ]; then
        if [ -n "$PARAM_OVERRIDES" ]; then
            PARAM_OVERRIDES="$PARAM_OVERRIDES $param_name=${!env_var}"
        else
            PARAM_OVERRIDES="$param_name=${!env_var}"
        fi
    fi
}

echo "🚀 Deploying SAM application..."
if [ -f "samconfig.toml" ]; then
    echo "📋 Using existing configuration..."
    PARAM_OVERRIDES=""
    
    # Add parameters if environment variables are set
    add_param "CertificateArn" "CERTIFICATE_ARN"
    add_param "DomainName" "DOMAIN_NAME"
    add_param "CdnBucketName" "CDN_BUCKET_NAME"
    add_param "CdnDomain" "CDN_DOMAIN"
    add_param "StaticFilesBucket" "STATIC_FILES_BUCKET"
    add_param "AnalyticsLogsBucket" "ANALYTICS_LOGS_BUCKET"
    add_param "SubnetIds" "SUBNET_IDS"
    add_param "LambdaSecurityGroupId" "LAMBDA_SECURITY_GROUP_ID"
    if [ -n "$PARAM_OVERRIDES" ]; then
        sam deploy --profile $AWS_PROFILE --parameter-overrides $PARAM_OVERRIDES
    else
        sam deploy --profile $AWS_PROFILE
    fi
else
    echo "📋 Running guided deployment (first time)..."
    sam deploy --guided --profile $AWS_PROFILE
fi

echo "✅ Deployment complete!"
echo "🔗 Your MCP server endpoint will be shown above."
echo "📝 Test with: curl -X POST <endpoint-url> -H 'Content-Type: application/json' -d '{\"method\":\"initialize\"}'"