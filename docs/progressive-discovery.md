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
