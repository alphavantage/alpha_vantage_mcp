# Progressive Discovery

Both the Lambda and stdio servers use progressive discovery mode, exposing only 3 meta-tools instead of all Alpha Vantage API tools:

| Tool | Purpose |
|------|---------|
| `TOOL_LIST` | List available tools with names and descriptions |
| `TOOL_GET` | Get full schema for one or more tools (accepts single tool name or list of tool names) |
| `TOOL_CALL` | Execute a tool by name with arguments |

**Pros:**
- Reduces context window usage by loading tool schemas on-demand
- Faster initial connection (fewer tools to enumerate upfront)

**Cons:**
- Requires 2 additional LLM round trips (TOOL_LIST → TOOL_GET → TOOL_CALL)

## Example: Three Round Trips in Action

User request: "give me aapl price"

### Step 1: TOOL_LIST
Discover available tools (only names and descriptions):
```
TOOL_LIST() → Returns list of 50+ tools with names like:
- TIME_SERIES_INTRADAY: Get intraday time series data
- GLOBAL_QUOTE: Returns the latest price and volume information for a ticker
- TIME_SERIES_DAILY: Get daily time series data
...
```

### Step 2: TOOL_GET
Get full schema for the relevant tool:
```json
TOOL_GET(tool_name: "GLOBAL_QUOTE") → {
  "name": "GLOBAL_QUOTE",
  "description": "Returns the latest price and volume information for a ticker.",
  "parameters": {
    "type": "object",
    "properties": {
      "symbol": {"type": "string", "description": "The symbol of the global ticker"},
      "datatype": {"type": "string", "description": "json or csv"}
    },
    "required": ["symbol"]
  }
}
```

### Step 3: TOOL_CALL
Execute the tool with appropriate arguments:
```json
TOOL_CALL(tool_name: "GLOBAL_QUOTE", arguments: {"symbol": "AAPL", "datatype": "json"}) → {
  "Global Quote": {
    "01. symbol": "AAPL",
    "02. open": "258.72",
    "03. high": "261.81",
    "04. low": "258.39",
    "05. price": "261.05",
    "06. volume": "45730847",
    "07. latest trading day": "2026-01-13",
    "08. previous close": "260.25",
    "09. change": "0.80",
    "10. change percent": "0.31%"
  }
}
```

**Result:** Only ~500 tokens used for GLOBAL_QUOTE schema instead of ~25,000 tokens if all 50+ tools were exposed upfront.

## Approach Comparison

### 1. Direct Mode (Not Used)
Expose all 50+ Alpha Vantage tools upfront.
- **Tokens:** ~25,000+ upfront
- **Round trips:** 1 (TOOL_CALL only)
- **Verdict:** Wasteful for large APIs; most users need only 1-3 tools per session

### 2. Three Round Trips (Current Implementation) ✓
Progressive discovery via TOOL_LIST → TOOL_GET → TOOL_CALL.
- **Tokens:** ~500 per tool (loaded on-demand)
- **Round trips:** 3
- **Verdict:** Best for APIs with uneven tool distribution. Scales efficiently regardless of API size.

### 3. Two Round Trips with Categories (Not Used)
Use CATEGORY_LIST → TOOL_CALL.
- **Tokens:** 2,500-15,000+ per category
- **Round trips:** 2
- **Problem:** TECHNICAL_INDICATORS category has 30+ tools (~15,000 tokens), defeating the purpose of progressive discovery
- **Verdict:** Doesn't work well when categories are unbalanced

**Recommendation:** Current approach (#2) provides optimal token efficiency for Alpha Vantage's API structure.
