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
