-- Daily tools/call count
-- Shows total MCP tool calls by date
SELECT
    SUBSTR(created_at, 1, 10) as date,
    COUNT(*) as daily_tool_calls
FROM mcp_analytics.mcp_logs
WHERE method = 'tools/call'
GROUP BY SUBSTR(created_at, 1, 10)
ORDER BY date DESC;