---
name: marketdata-cli
description: Fetch market data from your terminal using marketdata-cli. Covers stocks, forex, crypto, commodities, economic indicators, technical analysis, fundamentals, news sentiment, and options. Use when the user wants to look up stock prices, financial data, technical indicators, or economic data via CLI.
compatibility: Requires marketdata-cli installed (pip install marketdata-cli) and ALPHAVANTAGE_API_KEY set.
metadata:
  author: alphavantage
  version: "0.1.8"
---

# marketdata-cli

A CLI for accessing 100+ market data endpoints — stocks, forex, crypto, commodities, economic indicators, and technical analysis.

## Setup

1. Install: `pip install marketdata-cli` or `uv tool install marketdata-cli --force` or run directly with `uvx marketdata-cli`
2. Set API key (one of):
   - `export ALPHAVANTAGE_API_KEY=your_key`
   - Add `ALPHAVANTAGE_API_KEY=your_key` to a `.env` file
   - Pass `-k your_key` on each command

Get a free key at https://www.alphavantage.co/support/#api-key

## Commands

### Stock Quotes & Time Series

```bash
# Latest quote
marketdata-cli global_quote AAPL

# Daily OHLCV
marketdata-cli time_series_daily MSFT

# Intraday (1min, 5min, 15min, 30min, 60min)
marketdata-cli time_series_intraday TSLA --interval 5min

# Weekly / Monthly
marketdata-cli time_series_weekly AAPL
marketdata-cli time_series_monthly AAPL

# Bulk quotes
marketdata-cli realtime_bulk_quotes AAPL

# Symbol search
marketdata-cli symbol_search "berkshire"
```

### Fundamental Data

```bash
marketdata-cli company_overview AAPL
marketdata-cli income_statement AAPL
marketdata-cli balance_sheet AAPL
marketdata-cli cash_flow AAPL
marketdata-cli earnings AAPL
marketdata-cli dividends AAPL
marketdata-cli splits AAPL
marketdata-cli earnings_estimates AAPL
marketdata-cli insider_transactions AAPL
marketdata-cli etf_profile SPY
```

### Technical Indicators

All technical indicator commands take a SYMBOL and common flags: `--interval`, `--time_period`, `--series_type`.

```bash
# Moving averages
marketdata-cli sma AAPL --interval daily --time_period 50 --series_type close
marketdata-cli ema AAPL --interval daily --time_period 20 --series_type close

# Momentum
marketdata-cli rsi AAPL --interval daily --time_period 14 --series_type close
marketdata-cli macd AAPL --interval daily --series_type close
marketdata-cli stoch AAPL --interval daily

# Volatility
marketdata-cli bbands AAPL --interval daily --time_period 20 --series_type close
marketdata-cli atr AAPL --interval daily --time_period 14

# Volume
marketdata-cli obv AAPL --interval daily
marketdata-cli vwap AAPL --interval 15min
marketdata-cli mfi AAPL --interval daily --time_period 14
```

Run `marketdata-cli --help` to see all 60+ technical indicator commands.

### Forex & Crypto

```bash
# Forex
marketdata-cli currency_exchange_rate --from_currency USD --to_currency JPY
marketdata-cli fx_daily --from_symbol EUR --to_symbol USD
marketdata-cli fx_intraday --from_symbol EUR --to_symbol USD --interval 5min

# Crypto
marketdata-cli digital_currency_daily SYMBOL=BTC --market USD
marketdata-cli crypto_intraday SYMBOL=ETH --market USD --interval 5min
```

### Commodities

```bash
marketdata-cli wti
marketdata-cli brent
marketdata-cli natural_gas
marketdata-cli gold_silver_spot
marketdata-cli copper
marketdata-cli aluminum
marketdata-cli wheat
marketdata-cli corn
marketdata-cli cotton
marketdata-cli sugar
marketdata-cli coffee
```

### Economic Indicators

```bash
marketdata-cli real_gdp
marketdata-cli real_gdp_per_capita
marketdata-cli inflation
marketdata-cli cpi
marketdata-cli federal_funds_rate
marketdata-cli treasury_yield
marketdata-cli unemployment
marketdata-cli nonfarm_payroll
marketdata-cli retail_sales
marketdata-cli durables
```

### News & Market Info

```bash
marketdata-cli news_sentiment --tickers AAPL
marketdata-cli top_gainers_losers
marketdata-cli market_status
marketdata-cli earnings_calendar
marketdata-cli ipo_calendar
marketdata-cli listing_status
```

### Options

```bash
marketdata-cli realtime_options AAPL
marketdata-cli historical_options AAPL
```

### Analytics

```bash
marketdata-cli analytics_fixed_window AAPL
marketdata-cli analytics_sliding_window AAPL
```

## Common Flags

| Flag | Description |
|------|-------------|
| `-k, --api-key` | API key (overrides env var) |
| `-v, --verbose` | Enable verbose logging |
| `-h, --help` | Show help for any command |

## Tips

- Use `marketdata-cli <command> --help` to see all options for a specific command
- Most stock commands accept a positional SYMBOL argument (e.g., `marketdata-cli global_quote AAPL`)
- Forex commands use `--from_symbol` / `--to_symbol` or `--from_currency` / `--to_currency`
- Technical indicators default to `daily` interval if not specified
