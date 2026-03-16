# Fundamental Analysis

**Goal:** Evaluate a company's financial health, profitability, and shareholder returns.

1. **Company overview** — sector, market cap, P/E, EPS, dividend yield at a glance:
   ```bash
   marketdata-cli company_overview AAPL
   ```
2. **Income statement** — revenue, operating income, net income trends:
   ```bash
   marketdata-cli income_statement AAPL
   ```
3. **Balance sheet** — assets, liabilities, equity, debt levels:
   ```bash
   marketdata-cli balance_sheet AAPL
   ```
4. **Cash flow** — operating, investing, and financing cash flows:
   ```bash
   marketdata-cli cash_flow AAPL
   ```
5. **Earnings** — quarterly EPS actuals vs. estimates:
   ```bash
   marketdata-cli earnings AAPL
   ```
6. **Dividends & splits** — payout history and stock split events:
   ```bash
   marketdata-cli dividends AAPL
   marketdata-cli splits AAPL
   ```
7. **Insider transactions** — recent insider buys and sells:
   ```bash
   marketdata-cli insider_transactions AAPL
   ```

## Additional commands

- `earnings_estimates AAPL` — analyst EPS estimates
- `etf_profile SPY` — ETF holdings and profile
