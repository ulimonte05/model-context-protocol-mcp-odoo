"""
Odoo XML-RPC client for accessing Odoo data.

This module provides a client for connecting to Odoo via XML-RPC,
with specific support for accounting operations.
"""
import xmlrpc.client
import logging
from typing import Any, Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse

from ..config import config
from .exceptions import OdooConnectionError, OdooAuthenticationError

# Configure logging
logger = logging.getLogger(__name__)

class OdooClient:
    """Client for connecting to Odoo via XML-RPC with accounting support."""
    
    def __init__(
        self, 
        url: Optional[str] = None,
        database: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        """Initialize client with connection parameters."""
        self.url = url or config.odoo.url
        self.database = database or config.odoo.database
        self.username = username or config.odoo.username
        self.password = password or config.odoo.password
        
        # Clean up URL if needed
        parsed_url = urlparse(self.url)
        if not parsed_url.scheme:
            self.url = f"https://{self.url}"
        
        # XML-RPC endpoints
        self.common_endpoint = f"{self.url}/xmlrpc/2/common"
        self.object_endpoint = f"{self.url}/xmlrpc/2/object"
        
        # User ID after authentication
        self.uid = None
        self._connected = False
        
    @property
    def is_connected(self) -> bool:
        """Check if client is connected to Odoo."""
        return self.uid is not None and self._connected
        
    async def connect(self) -> int:
        """
        Connect to Odoo and authenticate user.
        
        Returns:
            int: Authenticated user ID
            
        Raises:
            OdooConnectionError: If connection fails
            OdooAuthenticationError: If authentication fails
        """
        try:
            # In a real async environment, this should use an async HTTP client
            # For simplicity, we use the standard XML-RPC client synchronously
            common = xmlrpc.client.ServerProxy(self.common_endpoint)
            self.uid = common.authenticate(
                self.database, self.username, self.password, {}
            )
            if not self.uid:
                raise OdooAuthenticationError("Authentication failed with the provided credentials")
            
            self._connected = True
            logger.info(f"Connected to Odoo as {self.username} (uid: {self.uid})")
            
            # Get server version
            version_info = await self.get_server_version()
            logger.info(f"Odoo server version: {version_info}")
            
            return self.uid
            
        except Exception as e:
            self._connected = False
            raise OdooConnectionError(f"Error connecting to Odoo: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from Odoo."""
        self.uid = None
        self._connected = False
        logger.info("Disconnected from Odoo")
    
    async def reconnect_if_needed(self):
        """Reconnect to Odoo if connection lost."""
        if not self.is_connected:
            await self.connect()
    
    async def get_server_version(self) -> str:
        """
        Get Odoo server version information.
        
        Returns:
            str: Version information string
        """
        try:
            common = xmlrpc.client.ServerProxy(self.common_endpoint)
            return common.version()
        except Exception as e:
            raise OdooConnectionError(f"Error getting server version: {str(e)}")
    
    async def execute_kw(
        self, 
        model: str, 
        method: str, 
        args: List,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Execute method on model with arguments.
        
        Args:
            model: Model name (e.g., 'res.partner')
            method: Method name (e.g., 'search_read')
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            Result of the method call
            
        Raises:
            OdooConnectionError: If the call fails
        """
        if not self.uid:
            await self.connect()
            
        if kwargs is None:
            kwargs = {}
            
        try:
            models = xmlrpc.client.ServerProxy(self.object_endpoint)
            return models.execute_kw(
                self.database, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            # If the error might be due to session expiry, try reconnecting once
            if "session expired" in str(e).lower() or "not logged" in str(e).lower():
                await self.connect()
                models = xmlrpc.client.ServerProxy(self.object_endpoint)
                return models.execute_kw(
                    self.database, self.uid, self.password,
                    model, method, args, kwargs
                )
            raise OdooConnectionError(f"Error executing {method} on {model}: {str(e)}")
    
    async def search_read(
        self, 
        model: str, 
        domain: List, 
        fields: Optional[List[str]] = None, 
        limit: int = 100,
        offset: int = 0,
        order: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search and read records of a model.
        
        Args:
            model: Model name (e.g., 'res.partner')
            domain: Search domain (e.g., [('is_company', '=', True)])
            fields: Fields to retrieve, None for all
            limit: Maximum number of records to return
            offset: Offset for pagination
            order: Sorting order (e.g., 'id desc')
            
        Returns:
            List of dictionaries with found records
            
        Raises:
            OdooConnectionError: If the call fails
        """
        kwargs = {'fields': fields, 'limit': limit, 'offset': offset}
        if order:
            kwargs['order'] = order
            
        return await self.execute_kw(model, 'search_read', [domain], kwargs)
    
    async def get_fields(self, model: str) -> Dict[str, Dict[str, Any]]:
        """
        Get information about model fields.
        
        Args:
            model: Model name (e.g., 'res.partner')
            
        Returns:
            Dictionary with field information
            
        Raises:
            OdooConnectionError: If the call fails
        """
        return await self.execute_kw(
            model, 'fields_get', [], 
            {'attributes': ['string', 'help', 'type', 'relation']}
        )
        
    # === Accounting-specific methods ===
    
    async def get_invoice_by_id(self, invoice_id: int) -> Dict[str, Any]:
        """
        Get invoice by ID.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            Invoice information
            
        Raises:
            OdooConnectionError: If the call fails
        """
        invoices = await self.execute_kw(
            'account.move', 'read',
            [invoice_id],
            {'fields': [
                'id', 'name', 'amount_total', 'amount_residual',
                'invoice_date', 'invoice_date_due', 'state', 'payment_state',
                'partner_id', 'currency_id', 'move_type', 'ref', 'invoice_origin'
            ]}
        )
        
        if not invoices:
            return {}
            
        return invoices[0]
    
    async def get_invoice_lines(self, invoice_id: int) -> List[Dict[str, Any]]:
        """
        Get invoice line items.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            List of invoice lines
            
        Raises:
            OdooConnectionError: If the call fails
        """
        line_ids = await self.execute_kw(
            'account.move.line', 'search',
            [[('move_id', '=', invoice_id), ('exclude_from_invoice_tab', '=', False)]]
        )
        
        if not line_ids:
            return []
            
        return await self.execute_kw(
            'account.move.line', 'read',
            [line_ids],
            {'fields': [
                'name', 'quantity', 'price_unit', 'price_subtotal', 
                'price_total', 'product_id', 'account_id', 'tax_ids'
            ]}
        )
    
    async def get_payments_for_invoice(self, invoice_id: int) -> List[Dict[str, Any]]:
        """
        Get payments related to an invoice.
        
        Args:
            invoice_id: Invoice ID
            
        Returns:
            List of payments
            
        Raises:
            OdooConnectionError: If the call fails
        """
        return await self.search_read(
            'account.payment',
            [('reconciled_invoice_ids', 'in', [invoice_id])],
            [
                'id', 'name', 'amount', 'date', 'state',
                'payment_type', 'partner_id', 'journal_id',
                'currency_id', 'payment_method_id'
            ]
        )
    
    async def get_journal_entries(
        self, 
        date_from: Optional[str] = None, 
        date_to: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get journal entries for a date range.
        
        Args:
            date_from: Start date (format: YYYY-MM-DD)
            date_to: End date (format: YYYY-MM-DD)
            limit: Maximum number of entries to return
            
        Returns:
            List of journal entries
            
        Raises:
            OdooConnectionError: If the call fails
        """
        domain = [('move_type', '=', 'entry')]
        
        if date_from:
            domain.append(('date', '>=', date_from))
        if date_to:
            domain.append(('date', '<=', date_to))
            
        return await self.search_read(
            'account.move',
            domain,
            ['id', 'name', 'date', 'ref', 'journal_id', 'state'],
            limit=limit
        )
    
    async def get_account_move_lines(self, move_id: int) -> List[Dict[str, Any]]:
        """
        Get account move lines for a journal entry.
        
        Args:
            move_id: Journal entry ID
            
        Returns:
            List of account move lines
            
        Raises:
            OdooConnectionError: If the call fails
        """
        return await self.search_read(
            'account.move.line',
            [('move_id', '=', move_id)],
            [
                'name', 'account_id', 'partner_id', 'debit', 'credit', 
                'balance', 'matching_number', 'full_reconcile_id'
            ]
        ) 