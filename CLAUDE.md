# Alpha Vantage MCP Server

Official MCP server exposing Alpha Vantage financial data APIs (100+ endpoints) to LLMs.

## Project Structure

Monorepo using `uv` workspace:

- `api/` — Shared API client library (`alphavantage-core`): HTTP client, tool registry, context vars
- `mcp/` — MCP server (stdio + Lambda HTTP): direct tool exposure, OAuth 2.0
- `cli/` — CLI tool (`marketdata-cli`): terminal access via Click
- `analytics/` — AWS analytics pipeline: log compaction, CloudWatch → S3 → Athena
- `examples/agent/` — OpenAI Agents example with session persistence
- `web/` — Next.js 15 artifacts viewer site (S3 + CloudFront deployment)
- `skills/` — Y-Agent skill definitions
- `scripts/` — Deployment and infrastructure scripts

## Tech Stack

- **Python 3.13+**, async/await throughout
- **uv** package manager, **hatchling** build backend
- **AWS SAM** for Lambda deployment (us-east-1)
- **Next.js 15 + Tailwind 4** for web
- Key deps: `mcp>=1.12.3`, `httpx`, `click`, `loguru`, `python-dotenv`

## Development

```bash
uv sync                                    # Install all deps
uv run marketdata-mcp-server $API_KEY      # Run stdio server
uv run marketdata-cli global_quote AAPL    # Run CLI
uv run pytest                              # Run tests
```

## Key Patterns

### Direct Tool Exposure
All ~100 real Alpha Vantage tools are listed directly as normal MCP tools in both the stdio and Lambda paths, with direct `tools/call` dispatch. Clients do their own (client-side) discovery over the listed tools. Each tool carries behavior hints (readOnly/destructive/openWorld), a derived human-readable title, and a permissive outputSchema (with matching structuredContent). The legacy `TOOL_LIST`/`TOOL_GET`/`TOOL_CALL` meta-tools (`mcp/src/av_mcp/tools/meta_tools.py`) are additively registered alongside the flat catalog in both transports, for backward compatibility with historical clients that still have them cached.

### Tool Definition
- Tools defined with `@tool` decorator in `api/src/av_api/tools/` by category
- Names auto-converted to UPPERCASE_WITH_UNDERSCORES
- Entitlement parameter added dynamically for delayed vs. realtime data

### MCP Tool Annotations (hints)
All tools MUST have proper safety annotations:
- `readOnlyHint: true` — For tools that only read data (most tools)
- `destructiveHint: true` — For tools that modify data or have side effects

### API Key Management
Thread-safe via `contextvars.ContextVar`. Multiple input methods: env var, CLI arg, query param, OAuth token.

### Large Response Handling
Responses >8192 tokens uploaded to S3 CDN, returns preview + link.

## Coding Conventions

- Modules: `lowercase_underscores.py`
- Functions: `snake_case` in code, `UPPERCASE_WITH_UNDERSCORES` in MCP
- Classes: `PascalCase`
- Formatting: **black**, linting: **ruff**
- Async/await for all MCP and API code

## Deployment

```bash
sam deploy --guided --region us-east-1     # AWS Lambda
cd web && npm run deploy                   # Cloudflare (web)
```

## Key Files

- `mcp/src/av_mcp/tools/registry.py` — Tool registry and `register_all_tools` (Lambda path)
- `mcp/src/av_mcp/stdio_server.py` — stdio server; `build_tools()` lists the real tools
- `mcp/src/av_mcp/decorators.py` — Custom @tool decorator
- `api/src/av_api/client.py` — HTTP client
- `api/src/av_api/registry.py` — Tool registry with lazy loading
- `api/src/av_api/tools/` — All tool definitions by category
