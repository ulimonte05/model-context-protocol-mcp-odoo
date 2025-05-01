"""
Context handler for MCP-Odoo tools

This module provides utility functions to handle context-related issues
with MCP 1.6.0, particularly the case where AppContext is passed as a dictionary
instead of as a proper object.
"""
import logging
from typing import Any, Dict, Optional, Union
import asyncio

from mcp.server.fastmcp import Context

from .odoo.client import OdooClient
from .config import config

# Configure logging
logger = logging.getLogger(__name__)

async def get_odoo_client_from_context(ctx: Context) -> OdooClient:
    """
    Safely extract Odoo client from context or recreate it if needed.
    
    This function handles the common issue in MCP 1.6.0 where AppContext
    might be passed as a dictionary instead of a proper object.
    
    Args:
        ctx: The MCP Context object from the tool function
        
    Returns:
        A connected OdooClient instance
    """
    try:
        # Get lifespan context (AppContext) from request context
        app_context = ctx.request_context.lifespan_context
        logger.debug(f"Context type: {type(app_context)}")
        
        # Handle the case when app_context is a dictionary
        if isinstance(app_context, dict):
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
        
        # Check client connection status and reconnect if needed
        if not client.is_connected:
            logger.warning("Odoo client disconnected, reconnecting...")
            await client.connect()
            
        return client
    except Exception as e:
        logger.error(f"Error getting Odoo client from context: {str(e)}", exc_info=True)
        # Create a new client as fallback
        logger.info("Creating new Odoo client as fallback...")
        config_data = config.as_dict()
        odoo_config = config_data.get("odoo", {})
        client = OdooClient(
            url=odoo_config.get("host") or odoo_config.get("url"),
            database=odoo_config.get("database"),
            username=odoo_config.get("username"),
            password=odoo_config.get("password")
        )
        await client.connect()
        return client 