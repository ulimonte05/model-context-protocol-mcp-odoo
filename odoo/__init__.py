"""
Odoo integration module for MCP server.
"""

from .client import OdooClient
from .exceptions import OdooConnectionError, OdooAuthenticationError

__all__ = ["OdooClient", "OdooConnectionError", "OdooAuthenticationError"] 