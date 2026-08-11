# Microsoft 365 Copilot Cowork connector package

This directory builds the connector-only Microsoft Teams v1.28 package for the production Alpha Vantage MCP endpoint.

The package is submission-ready only when the submission owner supplies:

- the final Teams app GUID;
- the Microsoft `OAuthPluginVault` authorization-config `referenceId`;
- an approved 192×192 color PNG and 32×32 transparent outline PNG; and
- the verified terms-of-use URL.

The committed `assets/dev-*.png` files are development placeholders. `--development` makes placeholder IDs explicit and validation rejects those IDs in normal mode.

## Build

```bash
uv run --project mcp python -m av_mcp.cowork_connector.package \
  --output dist/alpha-vantage-cowork.zip \
  --app-id <teams-app-guid> \
  --auth-config-id <oauth-plugin-vault-reference-id> \
  --terms-url <verified-terms-url> \
  --color-icon <approved-192x192-color-png> \
  --outline-icon <approved-32x32-outline-png>

uv run --project mcp python -m av_mcp.cowork_connector.validate dist/alpha-vantage-cowork.zip
```

For an end-to-end non-submission check, add `--development` and use `assets/dev-color.png` and `assets/dev-outline.png`.

## Verify the OAuth flow

`verify_oauth` drives the confidential-client flow over real HTTP: the Teams callback is reserved for the configured client, dynamic registration still refuses that callback, `client_secret_post`/`client_secret_basic` both work, and a wrong, missing, or rotated client credential is rejected. It exits non-zero on any failed check.

```bash
# Local: starts mcp/local_http_server.py with throwaway credentials, runs every check.
uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth

# Deployed: same checks against a configured deployment.
uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth \
  --base-url https://mcp.alphavantage.co --client-id <id> --client-secret <secret>
```

Run it against production once the Microsoft client credentials are configured there: that run is also what proves CloudFront forwards the `Authorization` header to `/token`. The three client-rotation checks change the server's own configuration, so they only run in local mode and are reported as skipped against a deployment.
