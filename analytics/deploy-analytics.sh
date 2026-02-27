#!/bin/bash

# AWS SAM deployment script for MCP Analytics (CloudWatch Logs + Lambda)
AWS_PROFILE=${AWS_PROFILE:-default}

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

echo "🚀 Starting deployment of MCP Analytics CloudWatch Logs stack..."

echo "🏗️  Building SAM application..."
sam build --template analytics/analytics.yaml --build-dir .aws-sam/build-analytics

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
if [ -f "analytics/samconfig-analytics.toml" ]; then
    echo "📋 Using analytics-specific configuration..."
    PARAM_OVERRIDES=""
    
    # Add parameters if environment variables are set
    add_param "AnalyticsLogsBucket" "ANALYTICS_LOGS_BUCKET"
    add_param "LambdaLogGroupName" "LAMBDA_LOG_GROUP_NAME"
    
    if [ -n "$PARAM_OVERRIDES" ]; then
        sam deploy --template-file .aws-sam/build-analytics/template.yaml --config-file $(pwd)/analytics/samconfig-analytics.toml --profile $AWS_PROFILE --parameter-overrides $PARAM_OVERRIDES
    else
        sam deploy --template-file .aws-sam/build-analytics/template.yaml --config-file $(pwd)/analytics/samconfig-analytics.toml --profile $AWS_PROFILE
    fi
else
    echo "📋 Running guided deployment (first time)..."
    sam deploy --template-file .aws-sam/build-analytics/template.yaml --guided --profile $AWS_PROFILE
fi

echo "✅ Analytics deployment complete!"
echo "🔗 CloudWatch Logs pipeline created for MCP analytics logs."