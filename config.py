"""
Configuration management for MCP Odoo integration.

This module handles loading and validating configuration from environment
variables or .env files for the MCP-Odoo connector.
"""
import os
import logging
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

# Configure logging
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


class OdooConfig(BaseModel):
    """Odoo connection configuration."""
    url: str = Field(default_factory=lambda: os.environ.get("ODOO_URL", ""))
    database: str = Field(default_factory=lambda: os.environ.get("ODOO_DB", ""))
    username: str = Field(default_factory=lambda: os.environ.get("ODOO_USERNAME", ""))
    password: str = Field(default_factory=lambda: os.environ.get("ODOO_PASSWORD", ""))
    api_key: Optional[str] = Field(default_factory=lambda: os.environ.get("ODOO_API_KEY"))
    
    # Accounting-specific settings
    accounting_enabled: bool = Field(default_factory=lambda: os.environ.get("ODOO_ACCOUNTING_ENABLED", "true").lower() == "true")
    default_date_range_days: int = Field(default_factory=lambda: int(os.environ.get("ODOO_DEFAULT_DATE_RANGE", "90")))
    
    @validator('url')
    def validate_url(cls, v):
        """Validate and normalize URL."""
        if not v:
            return v
        
        # Ensure URL has a protocol
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        # Remove trailing slash
        if v.endswith('/'):
            v = v[:-1]
            
        return v


class ServerConfig(BaseModel):
    """MCP server configuration."""
    host: str = Field(default_factory=lambda: os.environ.get("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.environ.get("PORT", "8080")))
    debug: bool = Field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    log_level: str = Field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))
    request_timeout: int = Field(default_factory=lambda: int(os.environ.get("REQUEST_TIMEOUT", "60")))
    server_url: str = Field(default_factory=lambda: os.environ.get("MCP_SERVER_URL", "http://localhost:8080"))


class Config:
    """Global configuration manager."""
    
    def __init__(self):
        self.odoo = OdooConfig()
        self.server = ServerConfig()
        
    def validate(self) -> bool:
        """Validate that all required configuration is present."""
        required_odoo_fields = ["url", "database", "username", "password"]
        for field in required_odoo_fields:
            if not getattr(self.odoo, field):
                logger.error(f"Missing required Odoo configuration: {field}")
                return False
        return True
    
    def as_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary for lifespan context."""
        return {
            "odoo": {
                "host": self.odoo.url,
                "database": self.odoo.database,
                "username": self.odoo.username,
                "password": self.odoo.password,
                "accounting_enabled": self.odoo.accounting_enabled,
                "default_date_range_days": self.odoo.default_date_range_days
            },
            "server": {
                "host": self.server.host,
                "port": self.server.port,
                "debug": self.server.debug,
                "request_timeout": self.server.request_timeout
            }
        }


# Global configuration instance
config = Config() 