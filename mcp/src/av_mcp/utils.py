"""Common utility functions shared across modules."""
import json
import hashlib
import time
from typing import Any
from loguru import logger

def parse_token_from_request(event: dict) -> str:
    """Parse API key from request body, query params, or Authorization header. Priority: body > query > header."""
    # Check request body first (highest priority)
    if event.get("body"):
        try:
            body = json.loads(event["body"]) if isinstance(event["body"], str) else event["body"]
            if isinstance(body, dict) and "apikey" in body and body["apikey"]:
                return body["apikey"]
        except (json.JSONDecodeError, TypeError):
            pass
    
    # Check query parameters second
    query_params = event.get("queryStringParameters") or {}
    if "apikey" in query_params and query_params["apikey"]:
        return query_params["apikey"]
    
    # Fallback to Authorization header
    headers = event.get("headers", {})
    auth_header = headers.get("Authorization") or headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove 'Bearer ' prefix
    return ""

def extract_client_platform(event: dict) -> str:
    """Extract client platform information from request headers."""
    headers = event.get("headers", {})
    
    # Check User-Agent header (case-insensitive)
    user_agent = headers.get("User-Agent") or headers.get("user-agent") or ""
    
    # Map common patterns to platform names based on actual headers
    # TODO: we just get example of claude and claude_code, others pattern need to be set based on real data
    platform_patterns = {
        "claude": ["claude-user"],
        "claude_code": ["claude-code"],
        "vscode": ["vscode", "visual studio code"],
        "cursor": ["cursor"],
        "windsurf": ["windsurf", "codeium"],
        "chatgpt": ["chatgpt", "openai"],
        "gemini": ["gemini", "google"],
        "python": ["python", "requests", "urllib"],
        "javascript": ["node", "axios", "fetch"],
        "postman": ["postman"],
        "curl": ["curl"],
        "browser": ["mozilla", "webkit", "chrome", "firefox", "safari", "edge"]
    }
    
    user_agent_lower = user_agent.lower()
    
    for platform, patterns in platform_patterns.items():
        if any(pattern in user_agent_lower for pattern in patterns):
            return platform
    
    # Check other headers that might indicate platform
    if headers.get("X-Client-Name"):
        return headers.get("X-Client-Name").lower()
    
    # Fallback based on User-Agent content
    if user_agent_lower:
        return user_agent_lower
    else:
        return "no_user_agent"

def estimate_tokens(data: Any) -> int:
    """Estimate the number of tokens in a data structure.
    
    Uses a simple heuristic: ~4 characters per token.
    This is a rough estimate suitable for JSON/text data.
    """
    if isinstance(data, str):
        return len(data) // 4
    elif isinstance(data, (dict, list)):
        json_str = json.dumps(data, separators=(',', ':'))
        return len(json_str) // 4
    else:
        return len(str(data)) // 4

def generate_storage_key(data: str, datatype: str = "json") -> str:
    """Generate a unique storage key for temporary data storage."""
    data_hash = hashlib.sha256(data.encode()).hexdigest()[:8]
    timestamp = int(time.time())
    extension = "csv" if datatype == "csv" else "json"
    return f"mcp-responses/{timestamp}-{data_hash}.{extension}"

def upload_to_object_storage(data: str, datatype: str = "json") -> str | None:
    """Upload data to S3 object storage and return a CDN URL.

    Args:
        data: The data to upload (as string)
        datatype: Data format - "csv" or "json" (affects file extension and content type)

    Returns:
        CDN URL to access the data, or None if upload fails
    """
    import os
    import boto3

    try:
        bucket_name = os.getenv("CDN_BUCKET_NAME")
        cdn_domain = os.getenv("CDN_DOMAIN")

        if not bucket_name or not cdn_domain:
            logger.warning("CDN storage not configured: CDN_BUCKET_NAME or CDN_DOMAIN environment variable not set")
            return None

        s3_client = boto3.client('s3', region_name=os.getenv("AWS_REGION", "us-east-1"))
        key = generate_storage_key(data, datatype)
        content_type = "text/csv" if datatype == "csv" else "application/json"

        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=data.encode('utf-8'),
            ContentType=content_type,
            CacheControl='public, max-age=3600',
            Metadata={'created': str(int(time.time()))},
            Tagging='AutoDelete=true'
        )

        return f"https://{cdn_domain}/{key}"

    except Exception as e:
        logger.error(f"Failed to upload to object storage: {e}")
        return None

def parse_and_log_mcp_analytics(body: str, token: str, platform: str) -> None:
    """Parse and log MCP method and params for analytics."""
    if not body:
        return
        
    try:
        import json
        
        parsed_body = json.loads(body)
        if "method" in parsed_body:
            mcp_method = parsed_body.get("method")
            mcp_params = parsed_body.get("params", {})
            
            tool_name = mcp_params.get("name", "unknown")
            tool_args = mcp_params.get("arguments", {})
            logger.info(f"MCP_ANALYTICS: method={mcp_method}, api_key={token}, platform={platform}, tool_name={tool_name}, arguments={json.dumps(tool_args)}")
    except (json.JSONDecodeError, Exception) as e:
        logger.debug(f"Could not parse body for MCP analytics: {e}")

def create_oauth_error_response(error_dict: dict, status_code: int = 401) -> dict:
    """Create Lambda-compatible OAuth 2.1 error response.
    
    Args:
        error_dict: OAuth error dictionary from detect_alphavantage_auth_error
        status_code: HTTP status code (401 for auth errors, 429 for rate limits)
        
    Returns:
        Lambda response dict with proper headers and status
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "WWW-Authenticate": f'Bearer error="{error_dict["error"]}", error_description="{error_dict["error_description"]}"',
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS"
        },
        "body": json.dumps(error_dict)
    }

