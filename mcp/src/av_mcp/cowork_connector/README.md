# Microsoft 365 Copilot Cowork connector package

This directory builds the connector-only Microsoft Teams v1.28 package for the production Alpha Vantage MCP endpoint.

Authentication uses **Cowork-managed Dynamic Client Registration (DCR)**. The package omits `remoteMcpServer.authorization` entirely; on install, Cowork registers its own confidential OAuth client against the server's advertised `/register` endpoint and stores the issued credentials in Microsoft's Enterprise token store. No Agents Toolkit auth-config, `OAuthPluginVault` reference, or pre-provisioned client secret is required.

The package is submission-ready only when the submission owner supplies:

- the final Teams app GUID;
- an approved 192×192 color PNG and 32×32 transparent outline PNG; and
- the verified terms-of-use URL.

The committed `assets/dev-*.png` files are development placeholders. `--development` makes the placeholder app ID explicit and validation rejects that ID (and the placeholder icons) in normal mode.

## Build

```bash
uv run --project mcp python -m av_mcp.cowork_connector.package \
  --output dist/alpha-vantage-cowork.zip \
  --app-id <teams-app-guid> \
  --terms-url <verified-terms-url> \
  --color-icon <approved-192x192-color-png> \
  --outline-icon <approved-32x32-outline-png>

uv run --project mcp python -m av_mcp.cowork_connector.validate dist/alpha-vantage-cowork.zip
```

For an end-to-end non-submission check, add `--development` and use `assets/dev-color.png` and `assets/dev-outline.png`:

```bash
uv run --project mcp python -m av_mcp.cowork_connector.package \
  --output dist/alpha-vantage-cowork-dev.zip \
  --development \
  --color-icon mcp/src/av_mcp/cowork_connector/assets/dev-color.png \
  --outline-icon mcp/src/av_mcp/cowork_connector/assets/dev-outline.png

uv run --project mcp python -m av_mcp.cowork_connector.validate \
  --development dist/alpha-vantage-cowork-dev.zip
```

The generated manifest's `agentConnectors[].toolSource.remoteMcpServer` contains only `mcpServerUrl` and `mcpToolDescription` — no `authorization` key.

## Verify the OAuth flow

`verify_oauth` drives the full confidential-DCR lifecycle over real HTTP: register (capture the issued secret), authorize against the Cowork callback, exchange and refresh with both `client_secret_post` and `client_secret_basic`, reject wrong/missing secrets, isolate the Cowork callback from legacy public clients, and confirm the legacy public-client path still works. It exits non-zero on any failed check. No Microsoft client credentials or environment variables are required.

```bash
# Local: starts mcp/local_http_server.py with throwaway signing keys, runs every check.
uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth

# Deployed: same checks against a live server that already has JWT_SECRET_KEY configured.
uv run --project mcp python -m av_mcp.cowork_connector.verify_oauth \
  --base-url https://mcp.alphavantage.co
```

Run it against production after the confidential-DCR registration endpoint is deployed: that run also proves CloudFront forwards the `Authorization` header to `/token`.

## Partner Center handoff

The submission owner needs only package metadata (app GUID, approved icons, verified legal URLs). Install the connector in a personal-scope Cowork tenant and let Cowork complete DCR + authorization-code exchange against `https://mcp.alphavantage.co/mcp`. Do not provision an Agents Toolkit auth config or paste a client secret into the package.
