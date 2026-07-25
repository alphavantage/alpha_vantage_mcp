# mcp-s3-ingest: Manufact bucket-put proxy

A dedicated Lambda function (`app.py`, `FunctionName: mcp-s3-ingest`) that lets a
Manufact container write to S3 without holding any AWS credentials of its own
(todo 2842, round 6). Manufact runs the MCP server on
[mcp-use](https://mcp-use.com) cloud instead of AWS Lambda; its account there has
no AWS identity to federate, and no IAM user can be created for it in production
(SSO `PowerUserAccess` cannot mint one). This function performs the PutObject on
the container's behalf, authenticated by a shared secret instead of AWS
credentials.

It is deliberately **not** a new branch inside `mcp/lambda_function.py`: a
separate function skips that handler's ~126-tool cold start, and gets its own
CloudWatch log group, which keeps its logs structurally outside the
`"MCP_ANALYTICS"` subscription filter that feeds the analytics pipeline (see
`analytics/README.md`) no matter what this function ever logs.

## Two callers

| Caller | Purpose | See |
|---|---|---|
| `mcp/src/av_mcp/analytics_emitter.py` (`IngestProxyWriter`) | Ship batched MCP usage events | `analytics/README.md` "Manufact Direct Ingestion" |
| `mcp/src/av_mcp/utils.py` (`upload_to_object_storage`) | Upload large tool responses for the CDN preview link | `mcp/src/av_mcp/common.py`'s `_server_response_processor` |

Both go through `mcp/src/av_mcp/s3_ingest_client.py` (`is_configured()` /
`put_object()`), which is the single place that knows the wire contract below.

## Wire contract

```
POST https://<api-id>.execute-api.us-east-1.amazonaws.com/Prod/internal/s3-put
X-Ingest-Secret: <shared secret>
X-Ingest-Target: analytics | cdn
X-Ingest-Key: <key suffix, relative to the target's prefix>
Content-Type: application/jsonlines | application/json | text/csv
<object bytes as the raw request body>

200 {"ok": true, "bucket": "...", "key": "...", "public_url": "https://cdn.../..."}
```

`public_url` is present only for the `cdn` target (built server-side from
`CDN_DOMAIN`); the caller never needs to know the CDN domain itself. The bucket
and key prefix are always resolved server-side from `X-Ingest-Target`: the
caller can never name a bucket or escape its target's prefix. `X-Ingest-Key`
must match `^[A-Za-z0-9._/-]{1,256}$`, with no leading `/`, no `//`, and no
`..`.

## Targets

| Target | Bucket (env) | Forced key prefix | Allowed `Content-Type` | Extra PUT args |
|---|---|---|---|---|
| `analytics` | `ANALYTICS_LOGS_BUCKET` | `jsonl/` | `application/jsonlines` | none |
| `cdn` | `CDN_BUCKET_NAME` | `mcp-responses/` | `application/json`, `text/csv` | `Tagging=AutoDelete=true`, `CacheControl=public, max-age=3600`, `Metadata={created}` |

`Tagging=AutoDelete=true` matters: the CDN buckets have a lifecycle rule that
expires tagged objects after 7 days.

## Errors

| Status | Cause |
|---|---|
| `405` | non-`POST` |
| `503` | `S3_INGEST_SECRET` unset, or the resolved target's bucket env var is unset (fail closed either way) |
| `401` | `X-Ingest-Secret` mismatch (`hmac.compare_digest`) |
| `400` | unknown `X-Ingest-Target`, invalid `X-Ingest-Key`, or disallowed `Content-Type` |
| `413` | body larger than 5 MiB (comfortably under the 6 MB Lambda proxy-integration ceiling) |
| `500` | the S3 PutObject itself failed |

The endpoint exposes PutObject only: no read, list, delete, or copy. Logs
record target, key, and byte count; never the secret or the object body.

## Two accounts, two endpoints

| | Staging | **Production** |
|---|---|---|
| Manufact domain | `mcp.alphavantage.dev` | `mcp.alphavantage.co` |
| Branch | `test` | `main` |
| AWS account | `<STAGING_AWS_ACCOUNT_ID>` | `<PROD_AWS_ACCOUNT_ID>` |
| Endpoint | `https://<staging-api-id>.execute-api.us-east-1.amazonaws.com/Prod/internal/s3-put` | `https://<prod-api-id>.execute-api.us-east-1.amazonaws.com/Prod/internal/s3-put` |
| `ANALYTICS_LOGS_BUCKET` | `alphavantage-mcp-analytics-logs-test` | `alphavantage-mcp-analytics-logs-prod` |
| `CDN_BUCKET_NAME` | `alphavantage-cdn-<STAGING_AWS_ACCOUNT_ID>` | `alphavantage-cdn-<PROD_AWS_ACCOUNT_ID>` |

Each Manufact deployment calls its own account's endpoint directly (not
through CloudFront: both MCP domains now front Manufact via Cloudflare, and
CloudFront's default cache behavior rejects `POST` with `403`). The real
account IDs, API IDs, and bucket names live in each GitHub Environment's
`CONFIG` JSON secret (see `.github/workflows/deploy.yml`); the endpoint's
`api-id` is whatever API Gateway assigns to that account's REST API.

## Deployment

Mounted as an explicit `POST /internal/s3-put` resource on the same REST API
the MCP function already uses (`template.yaml`'s `S3IngestFunction`); no
CloudFront or routing change is needed since API Gateway prefers an explicit
resource over the MCP function's greedy `/{proxy+}`.

It runs under its own IAM role, `mcp-s3-ingest-role`, created out-of-band by
`scripts/create-ingest-role.sh` (the same "admin runs a script once, then the
role is referenced by ARN" pattern as `scripts/create-lambda-role.sh` and
`analytics/create-logs-processor-role.sh`) rather than reusing
`mcp-server-lambda-execution-role`: its permissions are scoped to exactly
`s3:PutObject` on `<analytics bucket>/jsonl/*` and `s3:PutObject` +
`s3:PutObjectTagging` on `<cdn bucket>/mcp-responses/*`, instead of that role's
broader `AWSLambdaExecute` grant (`s3:PutObject` on `arn:aws:s3:::*`). Run the
script once per account, with that account's own bucket names, **before** the
first deploy that includes `S3IngestFunction`: the CI deploy role can
`iam:PassRole` to `lambda.amazonaws.com` but cannot create or patch IAM
resources itself.

`S3_INGEST_SECRET` and `ANALYTICS_LOGS_BUCKET` come from each GitHub
Environment's `CONFIG` JSON secret (see `.github/workflows/deploy.yml`), with a
different secret per account. An empty secret makes the endpoint fail closed
(`503`) rather than deploy silently open.

## Payload ceiling

API Gateway REST caps a request body at 10 MB, but the Lambda proxy
integration is a synchronous invoke, so the practical cap is the 6 MB Lambda
invocation payload. Analytics batches are single-digit KB and never approach
it. The CDN path is the real exposure (large tool responses can be low
single-digit MB); this function returns an explicit `413` in that case, and
the MCP server surfaces it as a *visible* preview error (see
`mcp/src/av_mcp/common.py`) instead of a silently null `data_url`. A presigned
PUT URL variant (bytes go straight from the container to S3, bypassing this
6 MB ceiling) is a named follow-up if `413`s start appearing in practice.
