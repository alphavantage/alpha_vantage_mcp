---
name: global-stock-analysis
description: Global stock market analysis (US, China & EU stock markets, forex, crypto, technicals, fundamentals, news, and more). 全球股票市场分析（包括美国、中国和欧洲股市、外汇、加密货币、技术面分析、基本面分析、新闻等）。
compatibility: Requires marketdata-cli installed (pip install marketdata-cli) and ALPHAVANTAGE_API_KEY set.
metadata:
  author: alphavantage
  version: "0.0.7"
  homepage: https://www.alphavantage.co
  source: https://github.com/alphavantage/alpha_vantage_mcp
  openclaw:
    requires:
      bins: ["marketdata-cli"]
      env: ["ALPHAVANTAGE_API_KEY"]
    install: "pip install marketdata-cli"
---

# Global Stock Analysis

Use these workflows to research stocks, evaluate companies, read technical signals, and monitor macro conditions — all from the terminal.

## Setup

1. Install: `pip install marketdata-cli` or `uv tool install marketdata-cli --force` or run directly with `uvx marketdata-cli`
2. Set API key (one of):
   - `export ALPHAVANTAGE_API_KEY=your_key`
   - Add `ALPHAVANTAGE_API_KEY=your_key` to a `.env` file
   - Pass `-k your_key` on each command

Get a free key at https://www.alphavantage.co/support/#api-key

## Workflows

### 1. Quick Stock Lookup

Get a snapshot of where a stock is right now — price, recent history, and news.

```bash
marketdata-cli global_quote AAPL
marketdata-cli time_series_daily AAPL
marketdata-cli news_sentiment --tickers AAPL
# Optional: intraday detail
marketdata-cli time_series_intraday AAPL --interval 5min
```

### 2. Fundamental Analysis

Evaluate a company's financial health: overview, financials, earnings, dividends, and insider activity.
See [fundamentals.md](references/fundamentals.md) for the full step-by-step guide.

### 3. Technical Analysis

Assess trend, momentum, volatility, and volume signals.
See [technicals.md](references/technicals.md) for the full step-by-step guide.

### 4. Macro & Market Overview

Check economic conditions, commodities, market movers, and upcoming events.
See [macro.md](references/macro.md) for the full step-by-step guide.

### 5. Sector / Multi-Stock Comparison

Compare fundamentals or technicals across multiple tickers by running the same commands for each symbol:

```bash
marketdata-cli company_overview AAPL
marketdata-cli company_overview MSFT
marketdata-cli company_overview GOOGL
```

See [comparison.md](references/comparison.md) for more examples.

### 6. Forex & Crypto

Exchange rates and price history for currencies and cryptocurrencies.
See [forex-crypto.md](references/forex-crypto.md) for the full step-by-step guide.

## Quick Reference

Run `marketdata-cli --help` for the full list of 100+ commands, or `marketdata-cli <command> --help` for any specific command.

| Flag | Description |
|------|-------------|
| `-k, --api-key` | API key (overrides env var) |
| `-v, --verbose` | Enable verbose logging |
| `-h, --help` | Show help for any command |

- Most stock commands accept a positional SYMBOL argument (e.g., `marketdata-cli global_quote AAPL`)
- Forex commands use `--from_symbol` / `--to_symbol` or `--from_currency` / `--to_currency`
- Technical indicators default to `daily` interval if not specified
