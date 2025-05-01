"""
Main MCP Server implementation for Odoo integration.

This module provides the MCP server implementation that exposes
Odoo data to AI agents via the Model Context Protocol.
"""
import logging
import asyncio
from typing import Literal, Optional
import os

from mcp.server.fastmcp import Context

# Import the MCP instance defined in mcp_instance.py
from .mcp_instance import mcp, AppContext

# Import all resources to ensure they are registered
from .resources import partners
from .resources import accounting

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Simple tool to verify connection
@mcp.tool()
async def odoo_version(ctx: Context) -> str:
    """Get the Odoo server version."""
    try:
        # Get Odoo client from the lifespan context
        # Add logging to debug the context type
        app_context = ctx.request_context.lifespan_context
        logger.info(f"Context type in odoo_version: {type(app_context)}")
        logger.info(f"Context content in odoo_version: {app_context}")
        
        # Handle the case when app_context is a dictionary
        if isinstance(app_context, dict):
            # Recreate AppContext if possible
            from .odoo.client import OdooClient
            from .config import config
            
            logger.info("Context is a dictionary, attempting to extract Odoo client...")
            
            # If the dictionary has an odoo_client as another dictionary, try to recreate it
            if "odoo_client" in app_context and isinstance(app_context["odoo_client"], dict):
                odoo_data = app_context["odoo_client"]
                client = OdooClient(
                    url=odoo_data.get("url"),
                    database=odoo_data.get("database"),
                    username=odoo_data.get("username"),
                    password=odoo_data.get("password")
                )
                if not client.is_connected:
                    await client.connect()
            else:
                # Create a new client using the configuration
                config_data = config.as_dict()
                odoo_config = config_data.get("odoo", {})
                client = OdooClient(
                    url=odoo_config.get("host") or odoo_config.get("url"),
                    database=odoo_config.get("database"),
                    username=odoo_config.get("username"),
                    password=odoo_config.get("password")
                )
                await client.connect()
        else:
            # Use the client directly from the AppContext
            client = app_context.odoo_client
        
        # Log activity
        await ctx.info("Executing odoo_version tool")
        
        # Check client connection status and reconnect if needed
        if not client.is_connected:
            await ctx.warning("Odoo client disconnected, reconnecting...")
            await client.connect()
        
        # Set a timeout for the operation
        version = await asyncio.wait_for(
            client.get_server_version(),
            timeout=5.0
        )
        
        return f"Connected to: {client.url}\nDatabase: {client.database}\nVersion: {version}"
    except asyncio.TimeoutError:
        logger.error("Timeout while executing odoo_version tool")
        await ctx.error("Operation timed out")
        return "Error: Connection to Odoo timed out"
    except Exception as e:
        logger.error(f"Error in odoo_version tool: {str(e)}", exc_info=True)
        await ctx.error(f"Error: {str(e)}")
        return f"Error: {str(e)}"


def run_server(transport: Literal["stdio", "sse"] = "stdio", 
               host: Optional[str] = None, 
               port: Optional[int] = None):
    """Run the MCP server with improved error handling and connection management.
    
    Args:
        transport: Transport type to use (stdio or sse)
        host: Host to bind to for SSE transport (overrides config)
        port: Port to bind to for SSE transport (overrides config)
    """
    # Import config here to avoid circular imports
    from .config import config
    
    # Override config with parameters if provided
    if host is not None:
        config.server.host = host
    if port is not None:
        config.server.port = port
    
    # Validate configuration
    if not config.validate():
        logger.error("Invalid configuration. Check environment variables.")
        raise ValueError("Invalid configuration. Check environment variables.")
    
    # Configure SSE server environment variables if using SSE transport
    if transport == "sse":
        # Set environment variables for the FastMCP SSE server
        os.environ["MCP_HOST"] = config.server.host
        os.environ["MCP_PORT"] = str(config.server.port)
        
        # Log startup information
        logger.info(f"Starting MCP Odoo server on {config.server.host}:{config.server.port}")
        logger.info(f"Connected to Odoo instance: {config.odoo.url}")
    else:
        logger.info(f"Starting MCP Odoo server with {transport} transport")
        logger.info(f"Connected to Odoo instance: {config.odoo.url}")
    
    try:
        # Log initialization info
        logger.info("Starting MCP server with Odoo integration")
        logger.info(f"Using {transport} transport")
        
        # Run the server with the configured transport
        # In 1.6.0, run() doesn't accept host/port directly
        mcp.run(transport=transport)
    except KeyboardInterrupt:
        logger.info("Server shutdown requested. Cleaning up...")
    except Exception as e:
        logger.error(f"Server error: {str(e)}")
        raise 