# Alpha Vantage MCP Server

Official MCP server exposing Alpha Vantage financial data APIs (100+ endpoints) to LLMs.

## Project Structure

Monorepo using `uv` workspace:

- `api/` — Shared API client library (`alphavantage-core`): HTTP client, tool registry, context vars
- `mcp/` — MCP server (stdio + Lambda HTTP): progressive discovery, OAuth 2.0, meta-tools
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

### Progressive Discovery
Only 3 meta-tools exposed (not 50+): `TOOL_LIST`, `TOOL_GET`, `TOOL_CALL`. Reduces initial context from ~25K to ~500 tokens. Tools loaded on-demand.

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

- `mcp/src/av_mcp/tools/registry.py` — Tool registry and meta-tool registration
- `mcp/src/av_mcp/tools/meta_tools.py` — Progressive discovery (TOOL_LIST/GET/CALL)
- `mcp/src/av_mcp/decorators.py` — Custom @tool decorator
- `api/src/av_api/client.py` — HTTP client
- `api/src/av_api/registry.py` — Tool registry with lazy loading
- `api/src/av_api/tools/` — All tool definitions by category
