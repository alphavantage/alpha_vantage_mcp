# Forex & Crypto

**Goal:** Check exchange rates and price history for currencies and cryptocurrencies.

## Forex

1. **Spot exchange rate:**
   ```bash
   marketdata-cli currency_exchange_rate --from_currency USD --to_currency JPY
   ```
2. **Daily price history:**
   ```bash
   marketdata-cli fx_daily --from_symbol EUR --to_symbol USD
   ```
3. **Intraday:**
   ```bash
   marketdata-cli fx_intraday --from_symbol EUR --to_symbol USD --interval 5min
   ```

## Crypto

1. **Daily prices:**
   ```bash
   marketdata-cli digital_currency_daily SYMBOL=BTC --market USD
   ```
2. **Intraday:**
   ```bash
   marketdata-cli crypto_intraday SYMBOL=ETH --market USD --interval 5min
   ```
