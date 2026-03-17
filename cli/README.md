# marketdata-cli

CLI wrapper for Alpha Vantage Financial Data APIs — built & optimized for AI agents. Access 100+ endpoints for stocks, forex, crypto, commodities, economic indicators, and technical analysis directly from your terminal.

## Install

```bash
# pip
pip install marketdata-cli

# uv
uv tool install marketdata-cli

# or run directly without installing
uvx marketdata-cli --help
```

## Setup

Get a free API key at https://www.alphavantage.co/support/#api-key, then either:

```bash
# Option 1: environment variable (recommended)
export ALPHAVANTAGE_API_KEY=your_key

# Option 2: .env file in your working directory
echo "ALPHAVANTAGE_API_KEY=your_key" > .env

# Option 3: pass inline with -k
marketdata-cli global_quote AAPL -k your_key
```

## View All Commands

Run `marketdata-cli --help` to see all available commands, or `marketdata-cli <command> --help` for details on a specific command.

## Example Uses

```bash
# Get latest quote
marketdata-cli global_quote AAPL

# Daily OHLCV data
marketdata-cli time_series_daily MSFT

# Intraday prices (1min, 5min, 15min, 30min, 60min)
marketdata-cli time_series_intraday TSLA --interval 5min

# Search for a ticker symbol
marketdata-cli symbol_search "berkshire"
```

### Fundamental Data

```bash
marketdata-cli company_overview AAPL
marketdata-cli income_statement AAPL
marketdata-cli balance_sheet AAPL
marketdata-cli cash_flow AAPL
marketdata-cli earnings AAPL
```

### Technical Indicators

```bash
marketdata-cli sma AAPL --interval daily --time_period 50 --series_type close
marketdata-cli rsi AAPL --interval daily --time_period 14 --series_type close
marketdata-cli macd AAPL --interval daily --series_type close
marketdata-cli bbands AAPL --interval daily --time_period 20 --series_type close
```

### Forex & Crypto

```bash
marketdata-cli currency_exchange_rate --from_currency USD --to_currency JPY
marketdata-cli fx_daily --from_symbol EUR --to_symbol USD
marketdata-cli digital_currency_daily SYMBOL=BTC --market USD
marketdata-cli crypto_intraday SYMBOL=ETH --market USD --interval 5min
```

### Commodities & Economic Indicators

```bash
marketdata-cli wti
marketdata-cli natural_gas
marketdata-cli gold_silver_spot
marketdata-cli real_gdp
marketdata-cli inflation
marketdata-cli cpi
marketdata-cli federal_funds_rate
marketdata-cli unemployment
```

### News & Market Info

```bash
marketdata-cli news_sentiment --tickers AAPL
marketdata-cli top_gainers_losers
marketdata-cli market_status
marketdata-cli earnings_calendar
marketdata-cli ipo_calendar
```

### Options

```bash
marketdata-cli realtime_options AAPL
marketdata-cli historical_options AAPL
```

