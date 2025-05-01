"""
FastMCP instance for MCP-Odoo

This module defines the FastMCP instance and application context
for the MCP-Odoo connector, including lifespan management.
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any, Dict
from dataclasses import dataclass
import logging

from mcp.server.fastmcp import FastMCP, Context
from .odoo.client import OdooClient
from .config import config

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AppContext:
    """Application context for MCP-Odoo"""
    odoo_client: OdooClient
    config: Dict[str, Any]

# Create FastMCP instance with enhanced instructions
mcp = FastMCP(
    name="mcp-odoo",
    version="1.0.0",
    instructions=(
        "MCP server for Odoo accounting integration. "
        "This provides access to accounting data from Odoo, "
        "including invoices, payments, and reconciliation functionality. "
        "You can query vendor bills, customer invoices, and analyze payment reconciliations."
    ),
    dependencies=["xmlrpc", "pydantic"]
)

# Configure lifespan
@asynccontextmanager
async def app_lifespan() -> AsyncGenerator[AppContext, None]:
    """Lifespan context manager for MCP-Odoo
    
    Yields:
        AppContext: Application context with Odoo client
    """
    logger.info("Initializing MCP-Odoo lifespan...")
    
    # Get configuration
    config_data = config.as_dict()
    odoo_config = config_data.get("odoo", {})
    
    # Create Odoo client
    client = OdooClient(
        url=odoo_config.get("host"),
        database=odoo_config.get("database"),
        username=odoo_config.get("username"),
        password=odoo_config.get("password")
    )

    # Connect to Odoo
    try:
        await client.connect()
        
        # Create app context
        app_ctx = AppContext(
            odoo_client=client,
            config=config_data
        )
        
        # Log what we're returning
        logger.info(f"Yielding AppContext object to FastMCP: {type(app_ctx)}")
        logger.info(f"AppContext has odoo_client: {hasattr(app_ctx, 'odoo_client')}")
        
        # Yield context to FastMCP
        yield app_ctx  # Make sure we're yielding the AppContext object, not a dict
    finally:
        # Disconnect from Odoo
        if client.is_connected:
            await client.disconnect()

# Log that we're setting the lifespan
logger.info("Setting lifespan in FastMCP...")

# Set lifespan in FastMCP
mcp.lifespan = app_lifespan

# Log successful setup
logger.info("MCP-Odoo instance setup complete")