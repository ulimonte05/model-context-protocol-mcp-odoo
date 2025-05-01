"""
Specific exceptions for Odoo integration.
"""


class OdooError(Exception):
    """Base exception for Odoo-related errors."""
    pass


class OdooConnectionError(OdooError):
    """Connection error with the Odoo server."""
    pass


class OdooAuthenticationError(OdooError):
    """Authentication error with the Odoo server."""
    pass


class OdooRequestError(OdooError):
    """Error in a request to the Odoo server."""
    pass 