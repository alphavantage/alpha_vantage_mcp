#!/usr/bin/env python3
"""Local development server to test the lambda function."""

import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from lambda_function import lambda_handler
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class LambdaRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.handle_request('GET')
    
    def do_POST(self):
        self.handle_request('POST')
    
    def do_OPTIONS(self):
        self.handle_request('OPTIONS')
    
    def handle_request(self, method):
        # Parse the URL
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        query_params = parse_qs(parsed_url.query)
        
        # Convert query params to the format expected by lambda
        query_string_params = {}
        for key, values in query_params.items():
            query_string_params[key] = values[0] if values else ''
        
        # Get request body for POST requests
        body = None
        if method == 'POST':
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                body = self.rfile.read(content_length).decode('utf-8')
        
        # Create Lambda-style event
        event = {
            'httpMethod': method,
            'path': path,
            'queryStringParameters': query_string_params if query_string_params else None,
            'headers': dict(self.headers),
            'body': body
        }
        
        # Create Lambda-style context (minimal)
        context = {}
        
        try:
            # Call the lambda handler
            response = lambda_handler(event, context)
            
            # Send response
            status_code = response.get('statusCode', 200)
            headers = response.get('headers', {})
            body = response.get('body', '')
            is_base64 = response.get('isBase64Encoded', False)
            
            self.send_response(status_code)
            
            # Set headers
            for header_name, header_value in headers.items():
                self.send_header(header_name, header_value)
            
            self.end_headers()
            
            # Send body
            if is_base64:
                import base64
                self.wfile.write(base64.b64decode(body))
            else:
                if isinstance(body, str):
                    self.wfile.write(body.encode('utf-8'))
                else:
                    self.wfile.write(body)
                    
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Internal Server Error: {str(e)}".encode('utf-8'))
    
    def log_message(self, format, *args):
        # Custom log format
        print(f"[{self.date_time_string()}] {format % args}")

def run_server(port=8000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, LambdaRequestHandler)
    print(f"Starting local server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Local development server for Alpha Vantage MCP Lambda')
    parser.add_argument('--port', '-p', type=int, default=8000, help='Port to run the server on (default: 8000)')
    args = parser.parse_args()
    
    run_server(args.port)