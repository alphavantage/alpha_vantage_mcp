# Sector / Multi-Stock Comparison

**Goal:** Compare fundamentals or technicals across several companies to find the strongest pick.

Run the same commands for each ticker.

## Side-by-side fundamentals

```bash
marketdata-cli company_overview AAPL
marketdata-cli company_overview MSFT
marketdata-cli company_overview GOOGL
```

## Side-by-side technicals

```bash
marketdata-cli rsi AAPL --interval daily --time_period 14 --series_type close
marketdata-cli rsi MSFT --interval daily --time_period 14 --series_type close
marketdata-cli rsi GOOGL --interval daily --time_period 14 --series_type close
```

## Longer-term comparison

Use weekly or monthly series:

```bash
marketdata-cli time_series_weekly AAPL
marketdata-cli time_series_weekly MSFT
marketdata-cli time_series_weekly GOOGL
```
