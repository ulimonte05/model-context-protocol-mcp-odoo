"""
Entry point for MCP Odoo server.
"""
import argparse
import sys
from typing import Literal

from .config import config
from .server import run_server


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="MCP Odoo Integration Server")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="sse",
        help="Transport to use: stdio (local agents) or sse (remote HTTP clients)"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host to bind to for SSE transport (default: from config or 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Port to bind to for SSE transport (default: from config or 8080)"
    )
    args = parser.parse_args()
    
    # Validate configuration
    if not config.validate():
        print("ERROR: Invalid configuration. Please check your .env file or environment variables.")
        print("Required: ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD")
        sys.exit(1)
    
    # Run the server
    try:
        print(f"Starting MCP-Odoo server with {args.transport} transport...")
        if args.transport == "sse":
            host_info = args.host or config.server.host
            port_info = args.port or config.server.port
            print(f"Server will listen on http://{host_info}:{port_info}")
            print("To connect, use:")
            print(f"  - SSE endpoint: http://{host_info}:{port_info}/sse")
            print(f"  - POST endpoint: http://{host_info}:{port_info}/messages")
        
        run_server(
            transport=args.transport,
            host=args.host,
            port=args.port
        )
    except Exception as e:
        print(f"ERROR starting server: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()