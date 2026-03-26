#!/usr/bin/env python3
"""
Simple Dashboard Server
Serves the web dashboard on port 5000
Can be run alongside the AI Brain API (port 8000)
"""

import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

class DashboardHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Disable caching for development
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        super().end_headers()

    def do_GET(self):
        # Serve index.html for root path
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

def run_server(port=5000):
    # Change to dashboard directory
    dashboard_dir = Path(__file__).parent
    os.chdir(dashboard_dir)
    
    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    print(f"\n{'='*60}")
    print(f"🚀 Dashboard Server Running")
    print(f"{'='*60}")
    print(f"📊 Access at: http://localhost:{port}")
    print(f"📍 Host: {server_address[0]}:{server_address[1]}")
    print(f"📁 Serving from: {dashboard_dir}")
    print(f"\nDemo Credentials:")
    print(f"  Admin:  admin / admin123")
    print(f"  Client: user1 / pass123")
    print(f"\nPress CTRL+C to stop")
    print(f"{'='*60}\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✋ Server stopped")
        sys.exit(0)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    run_server(port)
