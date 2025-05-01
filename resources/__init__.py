"""
Resources for the MCP-Odoo connector.

All resources should be imported here to ensure they are registered
with the MCP instance.
"""

# Partner resources
from .partners import partners_resource, partner_detail

# Accounting resources
from .accounting import (
    list_vendor_bills, 
    list_customer_invoices,
    list_payments,
    get_invoice_details,
    reconcile_invoices_and_payments,
    list_accounting_entries,
    list_suppliers,
    list_customers
)

__all__ = [
    # Partners
    "partners_resource", 
    "partner_detail",
    
    # Accounting
    "list_vendor_bills",
    "list_customer_invoices",
    "list_payments",
    "get_invoice_details",
    "reconcile_invoices_and_payments",
    "list_accounting_entries",
    "list_suppliers",
    "list_customers"
] 