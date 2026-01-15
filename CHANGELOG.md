# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-15

### Added
- Progressive discovery mode with meta-tools (TOOL_LIST, TOOL_GET, TOOL_CALL)
- New meta-tools implementation in `server/src/tools/meta_tools.py`
- Comprehensive documentation in `docs/progressive-discovery.md` with practical examples
- Support for retrieving multiple tool schemas in a single TOOL_GET call

### Changed
- **BREAKING**: Replaced category-based tool filtering with progressive discovery
- Lambda and stdio servers now expose only 3 meta-tools instead of all 50+ API tools
- Reduced MAX_RESPONSE_TOKENS from 50,000 to 8,192 for better token efficiency
- Updated stdio server to use progressive discovery by default
- Removed `--categories` and `--list-categories` CLI options from stdio server

### Removed
- **BREAKING**: Category-based filtering system (query parameter `?categories=...`)
- Category filtering from Lambda handler (`parse_tool_categories_from_request`)
- Path-based category routing (e.g., `/mcp/core_stock_apis`)
- Outdated deployment documentation (`docs/DEPLOYMENT.md`, `docs/DEPLOYMENT-STATIC.md`)

### Performance
- Reduced initial context window usage from ~25,000 tokens to minimal meta-tool overhead
- Tool schemas loaded on-demand (~500 tokens per tool instead of all tools upfront)
- Faster server initialization (no need to load all tool modules at startup)

### Migration Guide

#### For Lambda Users
Previously:
```
https://mcp.alphavantage.co/mcp?categories=core_stock_apis,forex
```

Now (progressive discovery - automatic):
```
https://mcp.alphavantage.co/mcp
```

The LLM will automatically discover and use tools via:
1. `TOOL_LIST` - discover available tools
2. `TOOL_GET` - get schema for specific tool(s)
3. `TOOL_CALL` - execute the tool

#### For stdio Server Users
Previously:
```bash
av-mcp YOUR_API_KEY --categories core_stock_apis forex
```

Now:
```bash
av-mcp YOUR_API_KEY
```

The `--categories` flag has been removed. All tools are discoverable via meta-tools.

## [0.2.1] - 2025-10-21

bump version

## [0.2.0] - 2025-09-28

### Added
- Category-based tool filtering via query parameters
- Support for 100+ Alpha Vantage API tools across 9 categories
- Lambda and stdio server implementations
- OAuth 2.0 authentication
- Large response handling with object storage
