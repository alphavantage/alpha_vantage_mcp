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

The Manufact container delivers MCP analytics to this bucket over one of two
transports, selected by `AnalyticsEmitter.from_environment()`
(`mcp/src/av_mcp/analytics_emitter.py`), which is only called from
`mcp/local_http_server.py`'s `run_server()`. The Lambda deployment
(`mcp/lambda_function.py`) never calls `from_environment()`, so the Lambda
process cannot ship these events under either transport even if the variables
below were present in its environment: double counting is structurally
impossible, not just coincidentally avoided.

**Manufact holds no AWS credentials and never will** (todo 2842, round 6:
production access is SSO `PowerUserAccess`, which cannot mint an IAM user), so
the transport that actually runs on Manufact is the proxy:

- **Proxy (production, Manufact)**: `S3_INGEST_URL` + `S3_INGEST_SECRET` set ->
  events POST through the `mcp-s3-ingest` Lambda's `/internal/s3-put` endpoint,
  which performs the S3 PutObject with its own execution role. See
  `ingest/README.md` for the wire contract, per-account URLs, and the two-account
  (staging/prod) bucket topology. `template.yaml` gained an `AnalyticsLogsBucket`
  parameter for this in round 6, but it is wired **only** into the `mcp-s3-ingest`
  function's environment, never the MCP function's: the paragraph above still
  holds verbatim.
- **Direct (local/dev only)**: `ANALYTICS_LOGS_BUCKET` set (and no
  `S3_INGEST_URL`) -> the container's own boto3 client PutObjects straight into
  this bucket. This is the transport a local/dev environment with real AWS
  credentials on hand should use; it is not viable on Manufact.

Both transports share everything below:

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
  hour a missed schedule tick left uncompacted. (As of round 6 this fix is
  deployed to staging only; the prod compactor redeploy is a deferred follow-up.)
- Manufact/Docker `SIGTERM` and normal interpreter exit synchronously flush the
  remaining queue. A hard kill can still lose at most the in-memory batch.

**Two AWS accounts, two buckets** (round 6 correction: everything above this
note in earlier revisions assumed a single account): production is account
`<PROD_AWS_ACCOUNT_ID>` / bucket `alphavantage-mcp-analytics-logs-prod`, serving
`mcp.alphavantage.co`; staging is account `<STAGING_AWS_ACCOUNT_ID>` / bucket
`alphavantage-mcp-analytics-logs-test` (despite the name, this is the live
staging bucket, not a throwaway), serving `mcp.alphavantage.dev`. Each account
needs its own `ingest/` role (`scripts/create-ingest-role.sh`), its own
`S3_INGEST_SECRET`, and its own `ANALYTICS_LOGS_BUCKET` value. See
`ingest/README.md`'s "Two accounts, two endpoints" table for the full
per-account variable list; the actual account IDs live in each GitHub
Environment's `CONFIG` secret, not in this repo.

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
