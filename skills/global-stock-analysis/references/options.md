# Options Chain

**Goal:** Inspect a US options chain, narrow down to the contracts you care about, read greeks and sentiment, and compare against historical conditions.

Realtime endpoints cover the current session; historical endpoints cover 15+ years (back to 2008-01-01) and always include greeks & implied volatility.

## 1. Chain snapshot

Pull the full realtime option chain — all expirations, all strikes, calls and puts. Sorted by expiration ascending, then by strike low-to-high.

```bash
marketdata-cli realtime_options AAPL
```

Use `realtime_options_fmv` instead when you want fair-market-value mark prices (smoothed mid quotes) rather than raw bid/ask:

```bash
marketdata-cli realtime_options_fmv AAPL
```

## 2. Filter by expiration

The full chain is large. Narrow to a single expiration date (`YYYY-MM-DD`, must be on or after today):

```bash
marketdata-cli realtime_options AAPL --expiration 2026-06-19
```

To zoom in on a single contract, pass its OCC contract ID:

```bash
marketdata-cli realtime_options AAPL --contract AAPL260619C00200000
```

## 3. Greeks & implied volatility

Add `--require_greeks` to surface delta, gamma, theta, vega, rho, and IV alongside the price fields. Off by default to keep payloads small.

```bash
marketdata-cli realtime_options AAPL --require_greeks --expiration 2026-06-19
marketdata-cli realtime_options_fmv AAPL --require_greeks --expiration 2026-06-19
```

## 4. Put/call sentiment

Quick directional read — bearish vs. bullish positioning across the chain.

```bash
marketdata-cli realtime_put_call_ratio SPY
marketdata-cli realtime_volume_open_interest_ratio SPY
```

Rules of thumb:
- Put/call ratio ≤ 0.6 → bullish sentiment.
- Put/call ratio ≥ 1.0 → bearish sentiment.
- Volume/OI ratio high → heavy fresh trading vs. existing positions (speculation, possible regime change).
- Volume/OI ratio low → most positions held, more stable conditions.

The realtime endpoints return ratios for the entire chain *and* per expiration date.

## 5. Historical comparison

Pull the same option chain or sentiment ratios as of any past trading day. Greeks and IV are always included for `historical_options`. Defaults to the previous trading session if `--date` is omitted. Optionally narrow to a single contract expiration with `--expiration` (`YYYY-MM-DD`); omit it to return contracts across all expiration dates.

```bash
marketdata-cli historical_options AAPL --date 2024-01-15
marketdata-cli historical_options AAPL --date 2024-01-15 --expiration 2024-06-21
marketdata-cli historical_put_call_ratio SPY --date 2024-01-15
marketdata-cli historical_volume_open_interest_ratio SPY --date 2024-01-15
```

Use these to answer questions like "what did the IV surface look like the day before earnings?" or "how did put/call sentiment evolve through the 2022 drawdown?"

## Output format

All chain commands default to CSV (compact, easy to pipe). Pass `--datatype json` for structured JSON when feeding another tool.

```bash
marketdata-cli realtime_options AAPL --datatype json
marketdata-cli historical_options AAPL --date 2024-01-15 --datatype json
```

Note: `historical_options` uses `-a` as the short flag for `--datatype` (not `-d`, which is `--date`).
