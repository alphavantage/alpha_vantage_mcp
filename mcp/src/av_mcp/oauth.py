"""OAuth 2.1 authorization server implementation for MCP server."""
import json
import secrets
import hashlib
import base64
import urllib.parse
from typing import Optional

def generate_authorization_code() -> str:
    """Generate a secure authorization code."""
    return secrets.token_urlsafe(32)

def generate_state() -> str:
    """Generate a secure state parameter."""
    return secrets.token_urlsafe(32)

def verify_pkce_challenge(code_verifier: str, code_challenge: str, code_challenge_method: str = "S256") -> bool:
    """Verify PKCE code challenge against code verifier.
    
    Args:
        code_verifier: The code verifier from token request
        code_challenge: The code challenge from authorization request
        code_challenge_method: Challenge method (S256 or plain)
        
    Returns:
        True if verification succeeds, False otherwise
    """
    if code_challenge_method == "S256":
        # Generate SHA256 hash of code_verifier, then base64url encode
        digest = hashlib.sha256(code_verifier.encode('ascii')).digest()
        expected_challenge = base64.urlsafe_b64encode(digest).decode('ascii').rstrip('=')
        return expected_challenge == code_challenge
    elif code_challenge_method == "plain":
        return code_verifier == code_challenge
    return False

def handle_metadata_discovery(event: dict) -> dict:
    """Handle OAuth 2.0 Authorization Server Metadata discovery.
    
    Returns metadata document according to RFC 8414.
    """
    import os
    
    # Use domain name from environment variable, fallback to request host
    domain_name = os.environ.get('DOMAIN_NAME')
    
    if domain_name:
        base_url = f"https://{domain_name}"
    else:
        # Fallback to extracting from request headers
        headers = event.get('headers', {})
        host = headers.get('Host') or headers.get('host')
        
        if not host:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "missing_host_header"})
            }
        
        # Validate that we're using HTTPS (except for localhost in development)
        if not host.startswith('localhost') and not headers.get('X-Forwarded-Proto') == 'https':
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "invalid_request", 
                    "error_description": "OAuth endpoints require HTTPS"
                })
            }
        
        # Enforce HTTPS for OAuth endpoints (required by OAuth 2.1)
        scheme = "https"  # Always use HTTPS for OAuth endpoints
        base_url = f"{scheme}://{host}"
    
    metadata = {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize", 
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": ["alphavantage:read"],
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "client_credentials"],
        "code_challenge_methods_supported": ["S256", "plain"],
        "token_endpoint_auth_methods_supported": ["client_secret_post", "none"],
        "subject_types_supported": ["public"]
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600"
        },
        "body": json.dumps(metadata)
    }

def handle_authorization_request(event: dict) -> dict:
    """Handle OAuth 2.1 authorization requests.
    
    Shows user consent UI where they can input their Alpha Vantage API key.
    """
    query_params = event.get('queryStringParameters') or {}
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method', 'GET')
    
    # Required OAuth parameters
    response_type = query_params.get('response_type')
    client_id = query_params.get('client_id') 
    redirect_uri = query_params.get('redirect_uri')
    state = query_params.get('state')
    
    # PKCE parameters
    code_challenge = query_params.get('code_challenge')
    code_challenge_method = query_params.get('code_challenge_method', 'S256')
    
    # Validate required parameters
    if response_type != 'code':
        return create_error_redirect(redirect_uri, 'unsupported_response_type', state)
    
    if not client_id or not redirect_uri:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Missing required parameters"})
        }
    
    # Validate redirect URI (basic validation)
    if not redirect_uri.startswith(('https://', 'http://localhost')):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Invalid redirect URI"})
        }
    
    # Handle POST request (form submission)
    if http_method == 'POST':
        return handle_authorization_form_submission(event, query_params)
    
    # Show authorization form (GET request)
    return show_authorization_form(query_params)

def show_authorization_form(query_params: dict) -> dict:
    """Show HTML form for API key input and authorization consent."""
    import os
    
    # Build query string to preserve OAuth parameters
    oauth_params = {
        'response_type': query_params.get('response_type', ''),
        'client_id': query_params.get('client_id', ''),
        'redirect_uri': query_params.get('redirect_uri', ''),
        'code_challenge': query_params.get('code_challenge', ''),
        'code_challenge_method': query_params.get('code_challenge_method', 'S256')
    }
    if query_params.get('state'):
        oauth_params['state'] = query_params.get('state')
    
    query_string = urllib.parse.urlencode(oauth_params)
    
    # Read the external HTML file
    html_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'authorization.html')
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            # Replace placeholder with actual form action
            html_content = html_content.replace('action="/authorize"', f'action="/authorize?{query_string}"')
    except FileNotFoundError:
        # Fallback to basic HTML if file not found
        html_content = f'''<!DOCTYPE html>
<html><head><title>Authorization</title></head>
<body><h1>Authorization form not found</h1>
<p>Please check that authorization.html exists in the project root.</p>
</body></html>'''
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache"
        },
        "body": html_content
    }

def handle_authorization_form_submission(event: dict, query_params: dict) -> dict:
    """Handle form submission with API key and complete OAuth flow."""
    
    # Parse form data from POST body
    body = event.get('body', '')
    if isinstance(body, str):
        try:
            if body.startswith('{'):
                # JSON body
                form_data = json.loads(body)
            else:
                # Form-encoded body
                form_data = dict(urllib.parse.parse_qsl(body))
        except (json.JSONDecodeError, ValueError):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "invalid_request", "error_description": "Malformed request body"})
            }
    else:
        form_data = body or {}
    
    api_key = form_data.get('api_key', '').strip()
    if not api_key:
        # Redirect back to form with error
        return show_authorization_form_with_error(query_params, "API key is required")
    
    # Extract OAuth parameters
    response_type = query_params.get('response_type')
    client_id = query_params.get('client_id') 
    redirect_uri = query_params.get('redirect_uri')
    state = query_params.get('state')
    code_challenge = query_params.get('code_challenge')
    code_challenge_method = query_params.get('code_challenge_method', 'S256')
    
    # Generate authorization code
    auth_code = generate_authorization_code()
    
    # Store API key with the authorization code for later token exchange
    # For this stateless approach, we'll encode both the OAuth params and the API key
    code_data = {
        "code": auth_code,
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "code_challenge": code_challenge,
        "code_challenge_method": code_challenge_method,
        "api_key": api_key  # Store the user's API key
    }
    
    # Simple encoding (in production, use JWT or encrypted storage)
    encoded_code = base64.urlsafe_b64encode(json.dumps(code_data).encode()).decode().rstrip('=')
    
    # Build redirect URL
    redirect_params = {'code': encoded_code}
    if state:
        redirect_params['state'] = state
        
    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(redirect_params)}"
    
    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url,
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        }
    }

def show_authorization_form_with_error(query_params: dict, error_message: str) -> dict:
    """Show authorization form with error message."""
    import os
    
    # Build query string to preserve OAuth parameters
    oauth_params = {
        'response_type': query_params.get('response_type', ''),
        'client_id': query_params.get('client_id', ''),
        'redirect_uri': query_params.get('redirect_uri', ''),
        'code_challenge': query_params.get('code_challenge', ''),
        'code_challenge_method': query_params.get('code_challenge_method', 'S256')
    }
    if query_params.get('state'):
        oauth_params['state'] = query_params.get('state')
    
    query_string = urllib.parse.urlencode(oauth_params)
    
    # Read the external HTML file
    html_file_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'authorization.html')
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            # Replace placeholder with actual form action and add error message
            html_content = html_content.replace('action="/authorize"', f'action="/authorize?{query_string}"')
            html_content = html_content.replace('error_message">', f'error_message">{error_message}')
            html_content = html_content.replace('class="hidden"', 'class=""', 1)  # Show error box
    except FileNotFoundError:
        # Fallback to basic HTML if file not found
        html_content = f'''<!DOCTYPE html>
<html><head><title>Authorization Error</title></head>
<body><h1>Authorization Error</h1>
<p>{error_message}</p>
<p>Please check that authorization.html exists in the project root.</p>
</body></html>'''
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Cache-Control": "no-store, no-cache, must-revalidate",
            "Pragma": "no-cache"
        },
        "body": html_content
    }

def handle_token_request(event: dict) -> dict:
    """Handle OAuth 2.1 token exchange requests."""
    
    # Parse request body
    body = event.get('body', '')
    if isinstance(body, str):
        try:
            if body.startswith('{'):
                # JSON body
                params = json.loads(body)
            else:
                # Form-encoded body
                params = dict(urllib.parse.parse_qsl(body))
        except (json.JSONDecodeError, ValueError):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "invalid_request", "error_description": "Malformed request body"})
            }
    else:
        params = body or {}
    
    grant_type = params.get('grant_type')
    
    if grant_type == 'authorization_code':
        return handle_authorization_code_grant(params)
    elif grant_type == 'client_credentials':
        return handle_client_credentials_grant(params)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "unsupported_grant_type"})
        }

def handle_authorization_code_grant(params: dict) -> dict:
    """Handle authorization code grant token request."""
    
    code = params.get('code')
    client_id = params.get('client_id')
    redirect_uri = params.get('redirect_uri')
    code_verifier = params.get('code_verifier')
    
    if not all([code, client_id, redirect_uri]):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Missing required parameters"})
        }
    
    # Decode authorization code (in production, lookup from secure storage)
    try:
        # Add padding if needed
        code += '=' * (4 - len(code) % 4)
        code_data = json.loads(base64.urlsafe_b64decode(code.encode()).decode())
    except (json.JSONDecodeError, ValueError):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_grant", "error_description": "Invalid authorization code"})
        }
    
    # Validate code data
    if (code_data.get('client_id') != client_id or 
        code_data.get('redirect_uri') != redirect_uri):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_grant", "error_description": "Code validation failed"})
        }
    
    # Verify PKCE if present
    code_challenge = code_data.get('code_challenge')
    if code_challenge and code_verifier:
        code_challenge_method = code_data.get('code_challenge_method', 'S256')
        if not verify_pkce_challenge(code_verifier, code_challenge, code_challenge_method):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "invalid_grant", "error_description": "PKCE verification failed"})
            }
    elif code_challenge:  # PKCE was used in auth request but no verifier provided
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Missing code_verifier"})
        }
    
    # Extract the API key that was provided during authorization
    api_key = code_data.get('api_key')
    if not api_key:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_grant", "error_description": "No API key found in authorization"})
        }
    
    # Return the Alpha Vantage API key as the access token
    access_token = api_key
    
    token_response = {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": 3600,  # 1 hour
        "scope": "alphavantage:read"
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        },
        "body": json.dumps(token_response)
    }

def handle_client_credentials_grant(params: dict) -> dict:
    """Handle client credentials grant for machine-to-machine auth."""
    
    client_id = params.get('client_id')
    client_secret = params.get('client_secret')
    
    if not client_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Missing client_id"})
        }
    
    # In this simplified implementation, the client_secret IS the Alpha Vantage API key
    if not client_secret:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_client", "error_description": "Missing client_secret"})
        }
    
    # Return the client_secret (Alpha Vantage API key) as the access token
    token_response = {
        "access_token": client_secret,  # Direct passthrough of Alpha Vantage API key
        "token_type": "Bearer",
        "expires_in": 3600,
        "scope": "alphavantage:read"
    }
    
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        },
        "body": json.dumps(token_response)
    }

def handle_registration_request(event: dict) -> dict:
    """Handle dynamic client registration requests."""
    
    try:
        body = event.get('body', '')
        if isinstance(body, str):
            registration_request = json.loads(body) if body else {}
        else:
            registration_request = body or {}
    except json.JSONDecodeError:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "invalid_request", "error_description": "Malformed JSON"})
        }
    
    # Generate client credentials
    client_id = f"mcp-client-{secrets.token_urlsafe(16)}"
    
    # Extract requested redirect URIs
    redirect_uris = registration_request.get('redirect_uris', [])
    
    # Validate redirect URIs
    for uri in redirect_uris:
        if not uri.startswith(('https://', 'http://localhost')):
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "invalid_redirect_uri", "error_description": f"Invalid redirect URI: {uri}"})
            }
    
    registration_response = {
        "client_id": client_id,
        "client_id_issued_at": int(secrets.randbits(32)),  # Unix timestamp
        "redirect_uris": redirect_uris or ["http://localhost:8080/callback"],
        "grant_types": ["authorization_code", "client_credentials"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none"  # Public client, no secret needed for auth code flow
    }
    
    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json",
            "Cache-Control": "no-store"
        },
        "body": json.dumps(registration_response)
    }

def create_error_redirect(redirect_uri: str, error: str, state: Optional[str] = None) -> dict:
    """Create error redirect response."""
    
    if not redirect_uri:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": error})
        }
    
    error_params = {'error': error}
    if state:
        error_params['state'] = state
        
    redirect_url = f"{redirect_uri}?{urllib.parse.urlencode(error_params)}"
    
    return {
        "statusCode": 302,
        "headers": {
            "Location": redirect_url,
            "Cache-Control": "no-store",
            "Pragma": "no-cache"
        }
    }