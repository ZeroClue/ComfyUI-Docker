#!/usr/bin/env python3
"""
Simple HTTP server for design playgrounds.
Serves the playgrounds directory and outputs the URL.
"""
import http.server
import socketserver
import os
import sys
import webbrowser
from pathlib import Path

DEFAULT_PORT = 8889


def find_available_port(start_port: int, max_tries: int = 10) -> int:
    """Find an available port starting from start_port."""
    import socket
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    raise RuntimeError(f"No available ports found between {start_port} and {start_port + max_tries}")


def main():
    # Change to playgrounds directory
    script_dir = Path(__file__).parent.resolve()
    os.chdir(script_dir)

    # Find available port
    port = find_available_port(DEFAULT_PORT)

    # List available playgrounds
    playgrounds = list(script_dir.glob("*.html"))
    playground_files = [p.name for p in playgrounds]

    # Create server
    handler = http.server.SimpleHTTPRequestHandler

    # Print banner
    print(f"\n{'='*60}")
    print("  ComfyUI Design Playground Server")
    print(f"{'='*60}")
    print(f"\n  Serving at: http://localhost:{port}")
    print(f"\n  Available playgrounds:")

    for pf in sorted(playground_files):
        print(f"    - http://localhost:{port}/{pf}")

    if not playground_files:
        print("    (No .html files found)")

    print(f"\n  Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")

    # Try to open browser (may fail in WSL/headless environments)
    if playground_files:
        first_playground = f"http://localhost:{port}/{playground_files[0]}"
        try:
            webbrowser.open(first_playground)
        except Exception:
            pass  # Silently fail if no browser available

    # Start server
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\nServer stopped.")


if __name__ == "__main__":
    main()
