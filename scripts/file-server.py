#!/usr/bin/env python3
"""
Simple file server for dashboard file browser.
Serves files from ~/clawd/ with blocklist enforcement.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import os
import json
import fnmatch

PORT = 18790
ROOT = os.path.expanduser("~/clawd")
AUTH_TOKEN = os.environ.get("FILE_SERVER_TOKEN", "")

# Files/paths that should never be served
BLOCKLIST = [
    ".clawdbot/*",
    "**/cookies/*.json",
    "*.key",
    "*.pem",
    ".env*",
    "*-env",
    "**/*.gpg",
]

def is_blocked(path):
    for pattern in BLOCKLIST:
        if fnmatch.fnmatch(path, pattern):
            return True
        # Also check with ** expansion for nested paths
        if "**" in pattern:
            simple_pattern = pattern.replace("**/", "*/")
            if fnmatch.fnmatch(path, simple_pattern):
                return True
    return False

def is_text_file(path):
    text_ext = {'.md', '.txt', '.py', '.sh', '.json', '.yml', '.yaml', 
                '.js', '.ts', '.tsx', '.html', '.css', '.xml', '.log',
                '.toml', '.ini', '.cfg', '.conf'}
    ext = os.path.splitext(path)[1].lower()
    # Also treat extensionless files with known names as text
    basename = os.path.basename(path).lower()
    if basename in {'makefile', 'dockerfile', '.gitignore', '.dockerignore'}:
        return True
    return ext in text_ext

class FileHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress default logging
        pass
    
    def do_GET(self):
        # Auth check
        auth = self.headers.get("Authorization", "")
        if AUTH_TOKEN and auth != f"Bearer {AUTH_TOKEN}":
            self.send_error(401, "Unauthorized")
            return
        
        # Parse path
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        rel_path = params.get("path", [""])[0]
        rel_path = unquote(rel_path)
        
        # Strip leading "clawd/" if present (tree paths include it)
        if rel_path.startswith("clawd/"):
            rel_path = rel_path[6:]
        
        if not rel_path:
            self.send_error(400, "Missing path parameter")
            return
        
        # Security checks
        if ".." in rel_path or rel_path.startswith("/"):
            self.send_error(403, "Invalid path")
            return
        
        if is_blocked(rel_path):
            self.send_error(403, "Access denied")
            return
        
        full_path = os.path.join(ROOT, rel_path)
        
        if not os.path.exists(full_path):
            self.send_error(404, "File not found")
            return
        
        if not os.path.isfile(full_path):
            self.send_error(400, "Not a file")
            return
        
        # Read and return
        try:
            if is_text_file(rel_path):
                with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                response = {"path": rel_path, "fileType": "text", "content": content}
            else:
                response = {"path": rel_path, "fileType": "binary", "error": "Binary file — cannot preview"}
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == "__main__":
    print(f"File server starting on port {PORT}, serving {ROOT}")
    HTTPServer(("127.0.0.1", PORT), FileHandler).serve_forever()
