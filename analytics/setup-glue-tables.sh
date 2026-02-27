#!/bin/bash

# Setup Glue database and table for MCP analytics
# This script creates the Glue resources needed for Athena queries

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

set -e

# Configuration
DATABASE_NAME="mcp_analytics"
TABLE_NAME="mcp_logs"
ANALYTICS_BUCKET_NAME="${ANALYTICS_LOGS_BUCKET:-alphavantage-mcp-analytics-logs}"
S3_LOCATION="s3://${ANALYTICS_BUCKET_NAME}/jsonl/"

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

echo "🔄 Setting up Glue database and table for MCP analytics..."
echo "Database: $DATABASE_NAME"
echo "Table: $TABLE_NAME"
echo "S3 Location: $S3_LOCATION"
echo ""

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity $AWS_PROFILE_OPTION --query Account --output text)
echo "Account ID: $ACCOUNT_ID"

# Create or update Glue database
echo "📊 Creating/updating Glue database..."
aws glue create-database $AWS_PROFILE_OPTION \
    --database-input Name="$DATABASE_NAME",Description="Database for MCP analytics logs" \
    2>/dev/null || echo "Database $DATABASE_NAME already exists"

# Check if table exists and drop it if it does
echo "🗃️ Checking for existing table..."
if aws glue get-table $AWS_PROFILE_OPTION --database-name "$DATABASE_NAME" --name "$TABLE_NAME" >/dev/null 2>&1; then
    echo "Table $TABLE_NAME exists, dropping it..."
    aws glue delete-table $AWS_PROFILE_OPTION \
        --database-name "$DATABASE_NAME" \
        --name "$TABLE_NAME"
fi

# Create table with JSON SerDe for structured MCP analytics fields
echo "📋 Creating Glue table with JSON SerDe..."
cat > /tmp/glue-table-input.json << ENDOFJSON
{
  "Name": "mcp_logs",
  "Description": "MCP analytics logs (JSON lines format)",
  "StorageDescriptor": {
    "Columns": [
      {"Name": "created_at", "Type": "string", "Comment": "Timestamp from log"},
      {"Name": "method", "Type": "string", "Comment": "MCP method called"},
      {"Name": "api_key", "Type": "string", "Comment": "API key used"},
      {"Name": "platform", "Type": "string", "Comment": "Platform making the request"},
      {"Name": "tool_name", "Type": "string", "Comment": "Tool name called"},
      {"Name": "arguments", "Type": "string", "Comment": "Arguments passed to the tool"}
    ],
    "Location": "${S3_LOCATION}",
    "InputFormat": "org.apache.hadoop.mapred.TextInputFormat",
    "OutputFormat": "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
    "Compressed": false,
    "SerdeInfo": {
      "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe"
    }
  },
  "Parameters": {
    "has_encrypted_data": "false",
    "typeOfData": "file"
  }
}
ENDOFJSON

aws glue create-table $AWS_PROFILE_OPTION \
    --database-name "$DATABASE_NAME" \
    --table-input file:///tmp/glue-table-input.json

# Clean up temp file
rm -f /tmp/glue-table-input.json

echo "✅ Glue database and table setup complete!"
echo ""
echo "📊 Resources created:"
echo "- Database: $DATABASE_NAME"
echo "- Table: $TABLE_NAME (JSON SerDe)"
echo "- S3 Location: $S3_LOCATION"
echo ""
echo "🔍 Query examples:"
echo "  SELECT created_at, method, api_key, platform, tool_name, arguments"
echo "  FROM mcp_analytics.mcp_logs LIMIT 10;"
