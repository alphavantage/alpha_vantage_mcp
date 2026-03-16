# Macro & Market Overview

**Goal:** Understand the economic backdrop and overall market conditions.

## 1. Economic health

GDP growth, inflation, and employment:

```bash
marketdata-cli real_gdp
marketdata-cli cpi
marketdata-cli unemployment
marketdata-cli nonfarm_payroll
```

## 2. Monetary policy

Rates and yields:

```bash
marketdata-cli federal_funds_rate
marketdata-cli treasury_yield
```

## 3. Commodities

Oil, gold, and other raw materials:

```bash
marketdata-cli wti
marketdata-cli brent
marketdata-cli natural_gas
marketdata-cli gold_silver_spot
```

## 4. Market movers & status

Today's biggest gainers/losers and exchange hours:

```bash
marketdata-cli top_gainers_losers
marketdata-cli market_status
```

## 5. Upcoming events

Earnings and IPO calendars:

```bash
marketdata-cli earnings_calendar
marketdata-cli ipo_calendar
```

## Additional commands

- Macro: `real_gdp_per_capita`, `inflation`, `retail_sales`, `durables`
- Commodities: `copper`, `aluminum`, `wheat`, `corn`, `cotton`, `sugar`, `coffee`
