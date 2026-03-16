# Technical Analysis

**Goal:** Read trend, momentum, volatility, and volume signals to time entries and exits.

All technical indicator commands take a SYMBOL and common flags: `--interval`, `--time_period`, `--series_type`.

## 1. Trend — Moving Averages

Is the stock trending up or down?

```bash
marketdata-cli sma AAPL --interval daily --time_period 50 --series_type close
marketdata-cli ema AAPL --interval daily --time_period 20 --series_type close
```

## 2. Momentum — RSI & MACD

Is it overbought/oversold? Is momentum shifting?

```bash
marketdata-cli rsi AAPL --interval daily --time_period 14 --series_type close
marketdata-cli macd AAPL --interval daily --series_type close
marketdata-cli stoch AAPL --interval daily
```

## 3. Volatility — Bollinger Bands & ATR

How wide are the swings?

```bash
marketdata-cli bbands AAPL --interval daily --time_period 20 --series_type close
marketdata-cli atr AAPL --interval daily --time_period 14
```

## 4. Volume — OBV, VWAP, MFI

Is volume confirming the move?

```bash
marketdata-cli obv AAPL --interval daily
marketdata-cli vwap AAPL --interval 15min
marketdata-cli mfi AAPL --interval daily --time_period 14
```

Run `marketdata-cli --help` to see all 60+ technical indicator commands.
