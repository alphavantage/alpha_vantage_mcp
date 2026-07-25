# Log Analytics Pipeline

Set up autonomous log analytics for your Alpha Vantage MCP server deployment.

## Setup Steps

Run these scripts in order to set up the complete pipeline:

1. **Create IAM role for Lambda logs processor:**
   ```bash
   ./create-logs-processor-role.sh
   ```

2. **Deploy the analytics infrastructure:**
   ```bash
   ./deploy-analytics.sh
   ```

3. **Set up Glue tables for querying:**
   ```bash
   ./setup-glue-tables.sh
   ```

4. **Query analytics data:**
   ```bash
   ./query-athena.sh
   ```

## Environment Configuration

The scripts use the following environment variables (can be set in `.env` file):

- `ANALYTICS_LOGS_BUCKET` - S3 bucket for analytics logs (default: `alphavantage-mcp-analytics-logs`)
- `LAMBDA_LOG_GROUP_NAME` - CloudWatch Log Group name for Lambda functions
- `AWS_PROFILE` - AWS profile to use (optional)

## Manufact Direct Ingestion

The Manufact container can deliver MCP analytics directly to this bucket when
`ANALYTICS_LOGS_BUCKET` is set, using the same variable this pipeline already
uses above. Double counting is structurally impossible, not just
coincidentally avoided: `AnalyticsEmitter.from_environment()` is only called
from `mcp/local_http_server.py`'s `run_server()`, and the Lambda deployment
(`template.yaml`, `.github/workflows/deploy.yml`) never sets this variable or
constructs an emitter, so the Lambda process cannot ship these events even if
the variable were present in its environment.

- Set `ANALYTICS_LOGS_BUCKET` in the Manufact service to the bucket backing
  this pipeline (currently `alphavantage-mcp-analytics-logs-test`, the live
  bucket despite its `-test` suffix). `AWS_REGION` is optional and defaults to
  `us-east-1`.
- The container identity needs `s3:PutObject` for
  `arn:aws:s3:::<analytics-bucket>/jsonl/*`; retain bucket encryption and block
  public access. Confirm this separately because credentials that can write the
  response-CDN bucket may not have access to the analytics bucket.
- The emitter batches asynchronously every 30 seconds or 100 events by default.
  `ANALYTICS_S3_FLUSH_INTERVAL_SECONDS`, `ANALYTICS_S3_BATCH_SIZE`, and
  `ANALYTICS_S3_MAX_QUEUE_SIZE` can tune those bounds. Queue overflow drops the
  oldest event rather than delaying MCP requests.
- Each object uses `jsonl/YYYY/MM/DD/HH/...jsonl` and the existing Glue schema:
  `created_at`, `method`, `api_key`, `platform`, `tool_name`, and `arguments`.
  The `api_key` field is the raw credential by the owner-approved private-data
  design. Do not log, copy into error reports, or expose these objects publicly.
- The emitter itself is a pure append-only writer: it never produces the
  hourly `compacted.jsonl` file. That invariant is maintained by the separate
  `mcp-logs-compactor` Lambda (`src/compactor.py`), which runs hourly, merges
  the just-closed hour's per-flush objects into one `compacted.jsonl`, and
  deletes the parts it merged. A ~24 hour lookback sweep lets it self-heal any
  hour a missed schedule tick left uncompacted.
- Manufact/Docker `SIGTERM` and normal interpreter exit synchronously flush the
  remaining queue. A hard kill can still lose at most the in-memory batch.

Paid/free classification, payment-source lookups, aggregation, and new-versus-
existing-user logic remain outside this public repository.

## Pipeline Components

- **CloudWatch Logs**: `/aws/lambda/[function-name]`
- **IAM Roles**:
  - `LogsProcessorRole-mcp` - For Lambda logs processor function
- **S3 Destination**: `s3://[bucket]/logs/`
- **Glue Database**: `mcp_analytics`
- **Glue Table**: `mcp_logs`

## Features

- **IAM Role Management**: Automated creation and configuration of required IAM roles
- **Policy Attachment**: Automatic attachment of necessary AWS managed policies
- **Environment Support**: Uses `.env` file for configuration
- **AWS Profile Support**: Works with named AWS profiles
- **Idempotent Scripts**: Safe to run multiple times - checks for existing resources

## Available Scripts

- **`create-logs-processor-role.sh`**: Creates IAM role for Lambda logs processor with S3 and CloudWatch access
- **`deploy-analytics.sh`**: Deploys the AWS SAM analytics infrastructure (CloudWatch Logs + Lambda)
- **`setup-glue-tables.sh`**: Sets up AWS Glue database and tables for analytics querying
- **`query-athena.sh`**: Queries the analytics data using Amazon Athena

## Monitoring & Querying

- **Query data**: Run `./query-athena.sh` to analyze your MCP server logs
