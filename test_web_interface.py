#!/usr/bin/env python3
"""
Test script for the web interface.

This script starts the web server and opens it in a browser for manual testing.
"""

import webbrowser
import time
import threading
from src.llm_context_exporter.web.app import create_app

def start_server():
    """Start the Flask development server."""
    app = create_app()
    app.run(host='127.0.0.1', port=8080, debug=False, use_reloader=False)

if __name__ == '__main__':
    print("Starting LLM Context Exporter Web Interface...")
    print("Server will be available at: http://127.0.0.1:8080")
    
    # Start server in a separate thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(2)
    
    # Open browser
    try:
        webbrowser.open('http://127.0.0.1:8080')
        print("Browser opened. Press Ctrl+C to stop the server.")
    except Exception as e:
        print(f"Could not open browser: {e}")
        print("Please manually navigate to http://127.0.0.1:8080")
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down server...")