#!/bin/bash

# Simple Athena query script that handles the full workflow
# Usage: ./query-athena.sh "SELECT COUNT(*) FROM mcp_analytics.mcp_logs"

set -e

# Load environment variables from .env if it exists
if [ -f ".env" ]; then
    echo "🔧 Loading environment variables from .env..."
    export $(grep -v '^#' .env | xargs)
fi

QUERY_INPUT="$1"
REGION="us-east-1"
ANALYTICS_BUCKET_NAME="${ANALYTICS_LOGS_BUCKET:-alphavantage-mcp-analytics-logs}"
OUTPUT_LOCATION="s3://$ANALYTICS_BUCKET_NAME/athena-results/"

# Set AWS profile options if specified
AWS_PROFILE_OPTION=""
if [ ! -z "$AWS_PROFILE" ]; then
    AWS_PROFILE_OPTION="--profile $AWS_PROFILE"
    echo "Using AWS profile: $AWS_PROFILE"
fi

if [ -z "$QUERY_INPUT" ]; then
    echo "Usage: $0 \"SQL_QUERY\""
    echo "       $0 sql/query-file.sql"
    echo "Example: $0 \"SELECT COUNT(*) FROM mcp_analytics.mcp_logs\""
    exit 1
fi

# If input is a .sql file, read its contents
if [[ "$QUERY_INPUT" == *.sql ]] && [ -f "$QUERY_INPUT" ]; then
    QUERY=$(cat "$QUERY_INPUT")
    echo "📄 Reading query from: $QUERY_INPUT"
else
    QUERY="$QUERY_INPUT"
fi

echo "🔍 Executing query: $QUERY"
echo

# Start query execution
QUERY_ID=$(aws athena start-query-execution $AWS_PROFILE_OPTION \
    --query-string "$QUERY" \
    --result-configuration OutputLocation="$OUTPUT_LOCATION" \
    --region "$REGION" \
    --query 'QueryExecutionId' \
    --output text \
    --no-cli-pager)

echo "📋 Query ID: $QUERY_ID"
echo "⏳ Waiting for query to complete..."

# Wait for query to complete
while true; do
    STATUS=$(aws athena get-query-execution $AWS_PROFILE_OPTION \
        --query-execution-id "$QUERY_ID" \
        --region "$REGION" \
        --query 'QueryExecution.Status.State' \
        --output text \
        --no-cli-pager)
    
    if [ "$STATUS" = "SUCCEEDED" ]; then
        echo "✅ Query completed successfully"
        break
    elif [ "$STATUS" = "FAILED" ] || [ "$STATUS" = "CANCELLED" ]; then
        echo "❌ Query failed with status: $STATUS"
        # Get error message
        aws athena get-query-execution $AWS_PROFILE_OPTION \
            --query-execution-id "$QUERY_ID" \
            --region "$REGION" \
            --query 'QueryExecution.Status.StateChangeReason' \
            --output text \
            --no-cli-pager
        exit 1
    else
        echo "⏳ Status: $STATUS"
        sleep 2
    fi
done

# Get execution stats
echo
echo "📊 Query Statistics:"
aws athena get-query-execution $AWS_PROFILE_OPTION \
    --query-execution-id "$QUERY_ID" \
    --region "$REGION" \
    --query 'QueryExecution.Statistics.{DataScanned:DataScannedInBytes,ExecutionTime:EngineExecutionTimeInMillis}' \
    --output table \
    --no-cli-pager

# Get and display results
echo
echo "📋 Results:"
aws athena get-query-results $AWS_PROFILE_OPTION \
    --query-execution-id "$QUERY_ID" \
    --region "$REGION" \
    --query 'ResultSet.Rows[*].Data[*].VarCharValue' \
    --output table \
    --no-cli-pager

echo
echo "🔗 Query ID for reference: $QUERY_ID"