# Alpha Vantage MCP Server

The official Alpha Vantage API MCP server enables LLMs and agentic workflows to seamlessly interact with real-time and historical stock market data through the Model Context Protocol (MCP). Add this server to your favorite apps such as Claude, Claude Code, Cursor, VS Code, and many more to give them access to comprehensive financial data.

## Quickstart

To use the server, <a href="https://www.alphavantage.co/support/#api-key" onclick="gtag('event', 'mcp_getKey')">get your free Alpha Vantage API key</a>, copy it to your clipboard, then follow the instructions below for the agentic tool/platform of your interest.

👉 Any questions? Please contact support@alphavantage.co

⭐ View MCP source code on [Github](https://github.com/alphavantage/alpha_vantage_mcp)


### Connection Examples

**Remote Server Connection:**
```
https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

**Local Server Connection:**
```
uvx av-mcp YOUR_API_KEY
```


### Setup Instructions by Platform

| Supported Platforms | How You Interact with Code | Setup Ease |
|---|---|---|
| **Recommended:**<br>• [Claude (Web & Desktop)](#claude-web--desktop)<br><br>**Additional:**<br>• [ChatGPT (Developer Mode)](#chatgpt-developer-mode)<br>• [Claude Code](#claude-code)<br>• [Cursor](#cursor)<br>• [Gemini CLI](#gemini-cli)<br>• [OpenAI Agents SDK](#openai-agents-sdk)<br>• [OpenAI Codex](#openai-codex)<br>• [Visual Studio Code](#visual-studio-code) | **AI Handles Everything**<br>Ask questions, and let the AI return market insights and financial answers automatically.<br>• [ChatGPT (Developer Mode)](#chatgpt-developer-mode)<br>• [Claude (Web & Desktop)](#claude-web--desktop)<br><br>**Coding Copilot**<br>Write or review code with AI suggestions, helping analyze stock data and build finance workflows.<br>• [Claude Code](#claude-code)<br>• [Cursor](#cursor)<br>• [Visual Studio Code](#visual-studio-code)<br><br>**Command Line Control**<br>Execute financial data queries and tasks from the command line.<br>• [Gemini CLI](#gemini-cli)<br><br>**Full Code Integration**<br>Build custom features in your codebase using the API, such as screeners, dashboards, or trading strategies.<br>• [OpenAI Agents SDK](#openai-agents-sdk)<br>• [OpenAI Codex](#openai-codex) | **Instant App Setup**<br>Adjust settings inside the app to connect instantly.<br>• [ChatGPT (Developer Mode)](#chatgpt-developer-mode)<br>• [Claude (Web & Desktop)](#claude-web--desktop)<br><br>**Config File Setup**<br>Paste a provided snippet into a project config file (e.g., JSON or TOML).<br>• [Cursor](#cursor)<br>• [OpenAI Codex](#openai-codex)<br>• [Visual Studio Code](#visual-studio-code)<br><br>**Terminal Command Setup**<br>Run setup commands in the terminal.<br>• [Claude Code](#claude-code)<br>• [Gemini CLI](#gemini-cli)<br><br>**Custom Code Setup**<br>Write custom code to connect and integrate with the API.<br>• [OpenAI Agents SDK](#openai-agents-sdk) |

<details>
<summary><b>Install in Claude</b></summary>

#### Remote Server Connection

To connect Claude (Web or Desktop) to this MCP server:

📺 Watch the **setup tutorial** - Click the image below to watch a step-by-step video guide:

[![Alpha Vantage MCP Setup Tutorial](https://img.youtube.com/vi/W69x2qJcYmI/maxresdefault.jpg)](https://www.youtube.com/watch?v=W69x2qJcYmI)


📺 Already have your Alpha Vantage MCP server set up? Below are a few examples of Claude performing various stock analysis & charting tasks:

[![Alpha Vantage MCP Example Prompts](https://img.youtube.com/vi/tyl9E7fddvU/maxresdefault.jpg)](https://www.youtube.com/watch?v=tyl9E7fddvU)

**Query Param Option (Recommended):**
1. Go to [claude.ai/settings/connectors](https://claude.ai/settings/connectors) (Web) or Settings → Connectors (Desktop)
2. Click "Add Custom Connector"
3. Add the MCP server URL with your API key: `https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key)
4. Click "Connect"

**OAuth Option:**
1. Go to [claude.ai/settings/connectors](https://claude.ai/settings/connectors) (Web) or Settings → Connectors (Desktop)
2. Click "Add Custom Connector"
3. Add the MCP server URL: `https://mcp.alphavantage.co/mcp`
4. Click "Connect"
5. Enter your Alpha Vantage API token
6. Click "Authorize Access"

#### Local Server Connection

Open Claude Desktop developer settings and edit your `claude_desktop_config.json` file to add the following configuration. See [Claude Desktop MCP docs](https://modelcontextprotocol.io/quickstart/user) for more info.

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

</details>

<details>
<summary><b>Install in OpenAI Agents SDK</b></summary>

To use the Alpha Vantage MCP server with OpenAI Agents SDK, see our [example agent](https://github.com/alphavantage/alpha_vantage_mcp/blob/main/examples/agent/README.md) that demonstrates:

- Interactive financial analysis agent
- Session management for conversation continuity
- Real-time tool execution with Alpha Vantage data
- Support for both HTTP and stdio MCP connections

The example includes a complete setup guide and configuration templates.

</details>


<details>
<summary><b>Install in ChatGPT</b></summary>

To connect ChatGPT to this MCP server using ChatGPT Developer mode:

**Requirements:**
- ChatGPT Pro or Plus account
- Developer mode enabled (beta feature) - see [OpenAI's Developer Mode documentation](https://platform.openai.com/docs/guides/developer-mode)

**Setup:**
1. Go to [ChatGPT Settings → Connectors](https://chatgpt.com/#settings/Connectors)
2. Enable **Advanced → Developer mode**
3. Add a remote MCP server with URL: `https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key)
4. In conversations, choose **Developer mode** from the Plus menu and select the Alpha Vantage connector

**Note:** While Developer mode is available for both Pro and Plus accounts, MCP tool execution is currently most reliable with Pro accounts. We're monitoring Plus plan functionality and will update this guide as improvements are made.

</details>


<details>
<summary><b>Install in Visual Studio Code</b></summary>

Add this to your VS Code MCP config file. See [VS Code MCP docs](https://code.visualstudio.com/docs/copilot/chat/mcp-servers) for more info.

#### VS Code Remote Server Connection

Create a `.vscode/mcp.json` file in your workspace and add this configuration (replace `YOUR_API_KEY` with your actual Alpha Vantage API key):

```json
{
  "servers": {
    "alphavantage": {
      "type": "http",
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

#### VS Code Local Server Connection

```json
{
  "servers": {
    "alphavantage": {
      "type": "stdio",
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Open the Chat view and select Agent mode

</details>


<details>
<summary><b>Install in Cursor</b></summary>

Pasting the following configuration into your Cursor `~/.cursor/mcp.json` file is the recommended approach. You may also install in a specific project by creating `.cursor/mcp.json` in your project folder. See [Cursor MCP docs](https://docs.cursor.com/context/model-context-protocol) for more info.

#### Cursor Remote Server Connection

Configure Cursor by editing `~/.cursor/mcp.json` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key):

```json
{
  "mcpServers": {
    "alphavantage": {
      "url": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

#### Cursor Local Server Connection

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

</details>


<details>
<summary><b>Install in Claude Code</b></summary>

Run this command. See [Claude Code MCP docs](https://docs.anthropic.com/en/docs/claude-code/mcp) for more info.

#### Claude Code Remote Server Connection

```bash
claude mcp add -t http alphavantage https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

#### Claude Code Local Server Connection

```bash
claude mcp add alphavantage -- uvx av-mcp YOUR_API_KEY
```

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

Run `claude` in your terminal from your project directory

Then connect with:
```
/mcp
```

</details>


<details>
<summary><b>Install in OpenAI Codex</b></summary>

See [OpenAI Codex](https://github.com/openai/codex) for more information.

Add the following configuration to your Codex MCP server settings by editing `~/.codex/config.toml` (replace `YOUR_API_KEY` with your actual Alpha Vantage API key):

```toml
[mcp_servers.alphavantage]
command = "uvx"
args = ["av-mcp", "YOUR_API_KEY"]
```

Run `codex` in your terminal from your project directory

Then connect with:
```
/mcp
```

</details>


<details>
<summary><b>Install in Gemini CLI</b></summary>

See [Gemini CLI Configuration](https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html) for details.

**CLI Command (Recommended):**
```bash
gemini mcp add -t http alphavantage https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY
```

**Local Server CLI Command:**
```bash
gemini mcp add alphavantage uvx av-mcp YOUR_API_KEY
```

**Manual Configuration:**
1. Open the Gemini CLI settings file. The location is `~/.gemini/settings.json` (where `~` is your home directory).
2. Add the following to the `mcpServers` object in your `settings.json` file:

```json
{
  "mcpServers": {
    "alphavantage": {
      "httpUrl": "https://mcp.alphavantage.co/mcp?apikey=YOUR_API_KEY"
    }
  }
}
```

Or, for a local server:

```json
{
  "mcpServers": {
    "alphavantage": {
      "command": "uvx",
      "args": ["av-mcp", "YOUR_API_KEY"]
    }
  }
}
```

If the `mcpServers` object does not exist, create it.

Replace `YOUR_API_KEY` with your actual Alpha Vantage API key.

</details>


### Category Filtering
Optionally filter available tools by category using:
- **Query parameter**: `?categories=core_stock_apis,alpha_intelligence`

Available categories:
- `core_stock_apis` - Core stock market data APIs
- `options_data_apis` - Options data APIs  
- `alpha_intelligence` - News sentiment and intelligence APIs
- `fundamental_data` - Company fundamentals and financial data
- `forex` - Foreign exchange rates and data
- `cryptocurrencies` - Digital and crypto currencies data
- `commodities` - Commodities and precious metals data
- `economic_indicators` - Economic indicators and market data
- `technical_indicators` - Technical analysis indicators and calculations
- `ping` - Health check and utility tools

If no categories are specified, all tools will be available.


## Tools Reference

| Category | Tools |
|----------|-------|
| core_stock_apis | `TIME_SERIES_INTRADAY`, `TIME_SERIES_DAILY`, `TIME_SERIES_DAILY_ADJUSTED`, `TIME_SERIES_WEEKLY`, `TIME_SERIES_WEEKLY_ADJUSTED`, `TIME_SERIES_MONTHLY`, `TIME_SERIES_MONTHLY_ADJUSTED`, `GLOBAL_QUOTE`, `REALTIME_BULK_QUOTES`, `SYMBOL_SEARCH`, `MARKET_STATUS` |
| options_data_apis | `REALTIME_OPTIONS`, `HISTORICAL_OPTIONS` |
| alpha_intelligence | `NEWS_SENTIMENT`, `EARNINGS_CALL_TRANSCRIPT`, `TOP_GAINERS_LOSERS`, `INSIDER_TRANSACTIONS`, `ANALYTICS_FIXED_WINDOW`, `ANALYTICS_SLIDING_WINDOW` |
| fundamental_data | `COMPANY_OVERVIEW`, `INCOME_STATEMENT`, `BALANCE_SHEET`, `CASH_FLOW`, `EARNINGS`, `LISTING_STATUS`, `EARNINGS_CALENDAR`, `IPO_CALENDAR` |
| forex | `FX_INTRADAY`, `FX_DAILY`, `FX_WEEKLY`, `FX_MONTHLY` |
| cryptocurrencies | `CURRENCY_EXCHANGE_RATE`, `DIGITAL_CURRENCY_INTRADAY`, `DIGITAL_CURRENCY_DAILY`, `DIGITAL_CURRENCY_WEEKLY`, `DIGITAL_CURRENCY_MONTHLY` |
| commodities | `WTI`, `BRENT`, `NATURAL_GAS`, `COPPER`, `ALUMINUM`, `WHEAT`, `CORN`, `COTTON`, `SUGAR`, `COFFEE`, `ALL_COMMODITIES` |
| economic_indicators | `REAL_GDP`, `REAL_GDP_PER_CAPITA`, `TREASURY_YIELD`, `FEDERAL_FUNDS_RATE`, `CPI`, `INFLATION`, `RETAIL_SALES`, `DURABLES`, `UNEMPLOYMENT`, `NONFARM_PAYROLL` |
| technical_indicators | `SMA`, `EMA`, `WMA`, `DEMA`, `TEMA`, `TRIMA`, `KAMA`, `MAMA`, `VWAP`, `T3`, `MACD`, `MACDEXT`, `STOCH`, `STOCHF`, `RSI`, `STOCHRSI`, `WILLR`, `ADX`, `ADXR`, `APO`, `PPO`, `MOM`, `BOP`, `CCI`, `CMO`, `ROC`, `ROCR`, `AROON`, `AROONOSC`, `MFI`, `TRIX`, `ULTOSC`, `DX`, `MINUS_DI`, `PLUS_DI`, `MINUS_DM`, `PLUS_DM`, `BBANDS`, `MIDPOINT`, `MIDPRICE`, `SAR`, `TRANGE`, `ATR`, `NATR`, `AD`, `ADOSC`, `OBV`, `HT_TRENDLINE`, `HT_SINE`, `HT_TRENDMODE`, `HT_DCPERIOD`, `HT_DCPHASE`, `HT_PHASOR` |
| ping | `PING`, `ADD_TWO_NUMBERS` |

### Table of Contents - API Tools
- [core_stock_apis](#core_stock_apis)
- [options_data_apis](#options_data_apis)
- [alpha_intelligence](#alpha_intelligence)
- [fundamental_data](#fundamental_data)
- [forex](#forex)
- [cryptocurrencies](#cryptocurrencies)
- [commodities](#commodities)
- [economic_indicators](#economic_indicators)
- [technical_indicators](#technical_indicators)
- [ping](#ping)

💡 Each of these MCP tools maps to a corresponding Alpha Vantage API endpoint. If you are interested in the full API specs (in addition to the brief tool descriptions below), please refer to the Alpha Vantage [API documentation](https://www.alphavantage.co/documentation/).  


### CORE_STOCK_APIS

| Category | Tool | Description |
|----------|------|-------------|
| core_stock_apis | `TIME_SERIES_INTRADAY` | Current and 20+ years of historical intraday OHLCV data |
| core_stock_apis | `TIME_SERIES_DAILY` | Daily time series (OHLCV) covering 20+ years |
| core_stock_apis | `TIME_SERIES_DAILY_ADJUSTED` | Daily adjusted OHLCV with split/dividend events |
| core_stock_apis | `TIME_SERIES_WEEKLY` | Weekly time series (last trading day of week) |
| core_stock_apis | `TIME_SERIES_WEEKLY_ADJUSTED` | Weekly adjusted time series with dividends |
| core_stock_apis | `TIME_SERIES_MONTHLY` | Monthly time series (last trading day of month) |
| core_stock_apis | `TIME_SERIES_MONTHLY_ADJUSTED` | Monthly adjusted time series with dividends |
| core_stock_apis | `GLOBAL_QUOTE` | Latest price and volume for a ticker |
| core_stock_apis | `REALTIME_BULK_QUOTES` | Realtime quotes for up to 100 symbols |
| core_stock_apis | `SYMBOL_SEARCH` | Search for symbols by keywords |
| core_stock_apis | `MARKET_STATUS` | Current market status worldwide |

### OPTIONS_DATA_APIS

| Category | Tool | Description |
|----------|------|-------------|
| options_data_apis | `REALTIME_OPTIONS` | Realtime US options data with Greeks |
| options_data_apis | `HISTORICAL_OPTIONS` | Historical options chain for 15+ years |

### ALPHA_INTELLIGENCE

| Category | Tool | Description |
|----------|------|-------------|
| alpha_intelligence | `NEWS_SENTIMENT` | Live and historical market news & sentiment |
| alpha_intelligence | `EARNINGS_CALL_TRANSCRIPT` | Earnings call transcripts with LLM sentiment |
| alpha_intelligence | `TOP_GAINERS_LOSERS` | Top 20 gainers, losers, and most active |
| alpha_intelligence | `INSIDER_TRANSACTIONS` | Latest and historical insider transactions |
| alpha_intelligence | `ANALYTICS_FIXED_WINDOW` | Advanced analytics over fixed windows |
| alpha_intelligence | `ANALYTICS_SLIDING_WINDOW` | Advanced analytics over sliding windows |

### FUNDAMENTAL_DATA

| Category | Tool | Description |
|----------|------|-------------|
| fundamental_data | `COMPANY_OVERVIEW` | Company information, financial ratios, and metrics |
| fundamental_data | `INCOME_STATEMENT` | Annual and quarterly income statements |
| fundamental_data | `BALANCE_SHEET` | Annual and quarterly balance sheets |
| fundamental_data | `CASH_FLOW` | Annual and quarterly cash flow statements |
| fundamental_data | `EARNINGS` | Annual and quarterly earnings data |
| fundamental_data | `LISTING_STATUS` | Listing and delisting data for equities |
| fundamental_data | `EARNINGS_CALENDAR` | Earnings calendar for upcoming earnings |
| fundamental_data | `IPO_CALENDAR` | Initial public offering calendar |

### FOREX

| Category | Tool | Description |
|----------|------|-------------|
| forex | `FX_INTRADAY` | Intraday foreign exchange rates |
| forex | `FX_DAILY` | Daily foreign exchange rates |
| forex | `FX_WEEKLY` | Weekly foreign exchange rates |
| forex | `FX_MONTHLY` | Monthly foreign exchange rates |

### CRYPTOCURRENCIES

| Category | Tool | Description |
|----------|------|-------------|
| cryptocurrencies | `CURRENCY_EXCHANGE_RATE` | Exchange rate between digital/crypto currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_INTRADAY` | Intraday time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_DAILY` | Daily time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_WEEKLY` | Weekly time series for digital currencies |
| cryptocurrencies | `DIGITAL_CURRENCY_MONTHLY` | Monthly time series for digital currencies |

### COMMODITIES

| Category | Tool | Description |
|----------|------|-------------|
| commodities | `WTI` | West Texas Intermediate (WTI) crude oil prices |
| commodities | `BRENT` | Brent crude oil prices |
| commodities | `NATURAL_GAS` | Henry Hub natural gas spot prices |
| commodities | `COPPER` | Global copper prices |
| commodities | `ALUMINUM` | Global aluminum prices |
| commodities | `WHEAT` | Global wheat prices |
| commodities | `CORN` | Global corn prices |
| commodities | `COTTON` | Global cotton prices |
| commodities | `SUGAR` | Global sugar prices |
| commodities | `COFFEE` | Global coffee prices |
| commodities | `ALL_COMMODITIES` | All commodities prices |

### ECONOMIC_INDICATORS

| Category | Tool | Description |
|----------|------|-------------|
| economic_indicators | `REAL_GDP` | Real Gross Domestic Product |
| economic_indicators | `REAL_GDP_PER_CAPITA` | Real GDP per capita |
| economic_indicators | `TREASURY_YIELD` | Daily treasury yield rates |
| economic_indicators | `FEDERAL_FUNDS_RATE` | Federal funds rate (interest rates) |
| economic_indicators | `CPI` | Consumer Price Index |
| economic_indicators | `INFLATION` | Inflation rates |
| economic_indicators | `RETAIL_SALES` | Retail sales data |
| economic_indicators | `DURABLES` | Durable goods orders |
| economic_indicators | `UNEMPLOYMENT` | Unemployment rate |
| economic_indicators | `NONFARM_PAYROLL` | Non-farm payroll data |

### TECHNICAL_INDICATORS

| Category | Tool | Description |
|----------|------|-------------|
| technical_indicators | `SMA` | Simple moving average (SMA) values |
| technical_indicators | `EMA` | Exponential moving average (EMA) values |
| technical_indicators | `WMA` | Weighted moving average (WMA) values |
| technical_indicators | `DEMA` | Double exponential moving average (DEMA) values |
| technical_indicators | `TEMA` | Triple exponential moving average (TEMA) values |
| technical_indicators | `TRIMA` | Triangular moving average (TRIMA) values |
| technical_indicators | `KAMA` | Kaufman adaptive moving average (KAMA) values |
| technical_indicators | `MAMA` | MESA adaptive moving average (MAMA) values |
| technical_indicators | `VWAP` | Volume weighted average price (VWAP) for intraday time series |
| technical_indicators | `T3` | Triple exponential moving average (T3) values |
| technical_indicators | `MACD` | Moving average convergence / divergence (MACD) values |
| technical_indicators | `MACDEXT` | Moving average convergence / divergence values with controllable moving average type |
| technical_indicators | `STOCH` | Stochastic oscillator (STOCH) values |
| technical_indicators | `STOCHF` | Stochastic fast (STOCHF) values |
| technical_indicators | `RSI` | Relative strength index (RSI) values |
| technical_indicators | `STOCHRSI` | Stochastic relative strength index (STOCHRSI) values |
| technical_indicators | `WILLR` | Williams' %R (WILLR) values |
| technical_indicators | `ADX` | Average directional movement index (ADX) values |
| technical_indicators | `ADXR` | Average directional movement index rating (ADXR) values |
| technical_indicators | `APO` | Absolute price oscillator (APO) values |
| technical_indicators | `PPO` | Percentage price oscillator (PPO) values |
| technical_indicators | `MOM` | Momentum (MOM) values |
| technical_indicators | `BOP` | Balance of power (BOP) values |
| technical_indicators | `CCI` | Commodity channel index (CCI) values |
| technical_indicators | `CMO` | Chande momentum oscillator (CMO) values |
| technical_indicators | `ROC` | Rate of change (ROC) values |
| technical_indicators | `ROCR` | Rate of change ratio (ROCR) values |
| technical_indicators | `AROON` | Aroon (AROON) values |
| technical_indicators | `AROONOSC` | Aroon oscillator (AROONOSC) values |
| technical_indicators | `MFI` | Money flow index (MFI) values |
| technical_indicators | `TRIX` | 1-day rate of change of a triple smooth exponential moving average (TRIX) values |
| technical_indicators | `ULTOSC` | Ultimate oscillator (ULTOSC) values |
| technical_indicators | `DX` | Directional movement index (DX) values |
| technical_indicators | `MINUS_DI` | Minus directional indicator (MINUS_DI) values |
| technical_indicators | `PLUS_DI` | Plus directional indicator (PLUS_DI) values |
| technical_indicators | `MINUS_DM` | Minus directional movement (MINUS_DM) values |
| technical_indicators | `PLUS_DM` | Plus directional movement (PLUS_DM) values |
| technical_indicators | `BBANDS` | Bollinger bands (BBANDS) values |
| technical_indicators | `MIDPOINT` | Midpoint values - (highest value + lowest value)/2 |
| technical_indicators | `MIDPRICE` | Midpoint price values - (highest high + lowest low)/2 |
| technical_indicators | `SAR` | Parabolic SAR (SAR) values |
| technical_indicators | `TRANGE` | True range (TRANGE) values |
| technical_indicators | `ATR` | Average true range (ATR) values |
| technical_indicators | `NATR` | Normalized average true range (NATR) values |
| technical_indicators | `AD` | Chaikin A/D line (AD) values |
| technical_indicators | `ADOSC` | Chaikin A/D oscillator (ADOSC) values |
| technical_indicators | `OBV` | On balance volume (OBV) values |
| technical_indicators | `HT_TRENDLINE` | Hilbert transform, instantaneous trendline (HT_TRENDLINE) values |
| technical_indicators | `HT_SINE` | Hilbert transform, sine wave (HT_SINE) values |
| technical_indicators | `HT_TRENDMODE` | Hilbert transform, trend vs cycle mode (HT_TRENDMODE) values |
| technical_indicators | `HT_DCPERIOD` | Hilbert transform, dominant cycle period (HT_DCPERIOD) values |
| technical_indicators | `HT_DCPHASE` | Hilbert transform, dominant cycle phase (HT_DCPHASE) values |
| technical_indicators | `HT_PHASOR` | Hilbert transform, phasor components (HT_PHASOR) values |

### PING

| Category | Tool | Description |
|----------|------|-------------|
| ping | `PING` | Health check tool that returns 'pong' |
| ping | `ADD_TWO_NUMBERS` | Example tool for adding two numbers |
