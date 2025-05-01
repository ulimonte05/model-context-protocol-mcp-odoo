"""
Accounting resources for MCP-Odoo

This module provides MCP tools and resources for accessing accounting data from Odoo,
specifically focused on vendor bills, customer invoices, payments, and reconciliation.
"""
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from mcp.server.fastmcp import Context
from ..mcp_instance import mcp
from ..context_handler import get_odoo_client_from_context

# Models for request/response types
class InvoiceFilter(BaseModel):
    """Filter parameters for invoice listing"""
    partner_id: Optional[int] = None
    pending: Optional[bool] = False
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: Optional[int] = 100

class PaymentFilter(BaseModel):
    """Filter parameters for payment listing"""
    partner_id: Optional[int] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: Optional[int] = 100
    invoice_id: Optional[int] = None  # To filter payments for a specific invoice

# Helper formatting functions
def format_invoice(invoice: Dict[str, Any]) -> Dict[str, Any]:
    """Format invoice data for better presentation"""
    result = {
        "id": invoice["id"],
        "name": invoice["name"],
        "amount_total": invoice["amount_total"],
        "amount_residual": invoice.get("amount_residual", 0.0),
        "date": invoice.get("invoice_date", invoice.get("date", "")),
        "due_date": invoice.get("invoice_date_due", ""),
        "state": invoice.get("state", ""),
        "payment_state": invoice.get("payment_state", ""),
        "partner": {
            "id": invoice["partner_id"][0],
            "name": invoice["partner_id"][1]
        } if invoice.get("partner_id") else None,
        "currency": invoice.get("currency_id", [False, ""])[1],
    }
    
    # Add human-readable payment state
    payment_states = {
        "not_paid": "Not Paid",
        "in_payment": "In Payment",
        "paid": "Paid",
        "partial": "Partially Paid",
        "reversed": "Reversed",
        "invoicing_legacy": "Legacy"
    }
    result["payment_state_display"] = payment_states.get(result["payment_state"], result["payment_state"])
    
    return result

def format_payment(payment: Dict[str, Any]) -> Dict[str, Any]:
    """Format payment data for better presentation"""
    return {
        "id": payment["id"],
        "name": payment["name"],
        "amount": payment["amount"],
        "date": payment.get("date", ""),
        "state": payment.get("state", ""),
        "payment_type": payment.get("payment_type", ""),  # inbound/outbound
        "partner": {
            "id": payment["partner_id"][0],
            "name": payment["partner_id"][1]
        } if payment.get("partner_id") else None,
        "journal": payment.get("journal_id", [False, ""])[1],
        "currency": payment.get("currency_id", [False, ""])[1],
        "reconciled_invoice_ids": payment.get("reconciled_invoice_ids", []),
        "payment_method": payment.get("payment_method_id", [False, ""])[1]
    }

# MCP tools for accounting functionality
@mcp.tool()
async def list_vendor_bills(ctx: Context, partner_id: Optional[int] = None, 
                           pending: Optional[bool] = False, 
                           date_from: Optional[str] = None, 
                           date_to: Optional[str] = None, 
                           limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List vendor bills (supplier invoices) with optional filtering.
    
    Args:
        partner_id: Filter by specific supplier ID
        pending: If True, only show unpaid invoices
        date_from: Filter invoices from this date (format: YYYY-MM-DD)
        date_to: Filter invoices until this date (format: YYYY-MM-DD)
        limit: Maximum number of invoices to return
        
    Returns:
        List of vendor bills with their payment status
    """
    # Create domain filters for Odoo
    domain = [("move_type", "=", "in_invoice")]  # Vendor bills only
    
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    
    if pending:
        domain.append(("payment_state", "!=", "paid"))
    
    if date_from:
        domain.append(("invoice_date", ">=", date_from))
    
    if date_to:
        domain.append(("invoice_date", "<=", date_to))
    
    # Get Odoo client using the context handler
    odoo_client = await get_odoo_client_from_context(ctx)
    
    # Get fields we want to retrieve
    fields = [
        "id", "name", "amount_total", "amount_residual",
        "invoice_date", "invoice_date_due", "state", "payment_state",
        "partner_id", "currency_id"
    ]
    
    # Query Odoo
    try:
        await ctx.info(f"Fetching vendor bills with domain: {domain}")
        invoices = await odoo_client.execute_kw(
            "account.move", "search_read",
            [domain],
            {"fields": fields, "limit": limit}
        )
        
        # Format response
        return [format_invoice(invoice) for invoice in invoices]
    except Exception as e:
        await ctx.error(f"Error fetching vendor bills: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_customer_invoices(ctx: Context, partner_id: Optional[int] = None, 
                               pending: Optional[bool] = False, 
                               date_from: Optional[str] = None, 
                               date_to: Optional[str] = None, 
                               limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List customer invoices with optional filtering.
    
    Args:
        partner_id: Filter by specific customer ID
        pending: If True, only show unpaid invoices
        date_from: Filter invoices from this date (format: YYYY-MM-DD)
        date_to: Filter invoices until this date (format: YYYY-MM-DD)
        limit: Maximum number of invoices to return
        
    Returns:
        List of customer invoices with their payment status
    """
    # Create domain filters for Odoo
    domain = [("move_type", "=", "out_invoice")]  # Customer invoices only
    
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    
    if pending:
        domain.append(("payment_state", "!=", "paid"))
    
    if date_from:
        domain.append(("invoice_date", ">=", date_from))
    
    if date_to:
        domain.append(("invoice_date", "<=", date_to))
    
    # Get Odoo client using the context handler
    odoo_client = await get_odoo_client_from_context(ctx)
    
    # Get fields we want to retrieve
    fields = [
        "id", "name", "amount_total", "amount_residual",
        "invoice_date", "invoice_date_due", "state", "payment_state",
        "partner_id", "currency_id"
    ]
    
    # Query Odoo
    try:
        await ctx.info(f"Fetching customer invoices with domain: {domain}")
        invoices = await odoo_client.execute_kw(
            "account.move", "search_read",
            [domain],
            {"fields": fields, "limit": limit}
        )
        
        # Format response
        return [format_invoice(invoice) for invoice in invoices]
    except Exception as e:
        await ctx.error(f"Error fetching customer invoices: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_payments(ctx: Context, partner_id: Optional[int] = None, 
                      date_from: Optional[str] = None, 
                      date_to: Optional[str] = None, 
                      limit: Optional[int] = 100,
                      invoice_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    List payments with optional filtering.
    
    Args:
        partner_id: Filter by specific partner ID
        date_from: Filter payments from this date (format: YYYY-MM-DD)
        date_to: Filter payments until this date (format: YYYY-MM-DD)
        limit: Maximum number of payments to return
        invoice_id: Filter payments linked to a specific invoice
        
    Returns:
        List of payments with their details
    """
    # Create domain filters for Odoo
    domain = []
    
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    
    if date_from:
        domain.append(("date", ">=", date_from))
    
    if date_to:
        domain.append(("date", "<=", date_to))
    
    # Invoice filtering is more complex and might require a different approach
    # depending on how Odoo stores the relationship between payments and invoices
    
    # Get Odoo client using the context handler
    odoo_client = await get_odoo_client_from_context(ctx)
    
    # Get fields we want to retrieve
    fields = [
        "id", "name", "amount", "date", "state", 
        "payment_type", "partner_id", "journal_id", 
        "currency_id", "reconciled_invoice_ids", "payment_method_id"
    ]
    
    # Query Odoo
    try:
        await ctx.info(f"Fetching payments with domain: {domain}")
        payments = await odoo_client.execute_kw(
            "account.payment", "search_read",
            [domain],
            {"fields": fields, "limit": limit}
        )
        
        # If filtering by invoice_id, we need to do it here since
        # the relationship might not be easily queried in the domain
        if invoice_id and payments:
            payments = [
                p for p in payments 
                if invoice_id in p.get("reconciled_invoice_ids", [])
            ]
        
        # Format response
        return [format_payment(payment) for payment in payments]
    except Exception as e:
        await ctx.error(f"Error fetching payments: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def get_invoice_details(ctx: Context, invoice_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific invoice.
    
    Args:
        invoice_id: ID of the invoice to retrieve
        
    Returns:
        Detailed invoice information including line items
    """
    try:
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # First get the invoice header
        invoice_headers = await odoo_client.execute_kw(
            "account.move", "read",
            [invoice_id],
            {"fields": [
                "id", "name", "amount_total", "amount_residual",
                "invoice_date", "invoice_date_due", "state", "payment_state",
                "partner_id", "currency_id", "ref", "narration", "invoice_origin",
                "journal_id", "move_type"
            ]}
        )
        
        if not invoice_headers:
            return {"error": f"Invoice with ID {invoice_id} not found"}
        
        invoice = invoice_headers[0]
        
        # Get invoice line items
        line_ids = await odoo_client.execute_kw(
            "account.move.line", "search",
            [[("move_id", "=", invoice_id), ("exclude_from_invoice_tab", "=", False)]],
            {}
        )
        
        lines = []
        if line_ids:
            line_data = await odoo_client.execute_kw(
                "account.move.line", "read",
                [line_ids],
                {"fields": [
                    "name", "quantity", "price_unit", "price_subtotal", 
                    "price_total", "product_id", "account_id", "tax_ids"
                ]}
            )
            lines = line_data
        
        # Format the invoice with its lines
        result = format_invoice(invoice)
        result["lines"] = lines
        
        return result
    except Exception as e:
        await ctx.error(f"Error fetching invoice details: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def reconcile_invoices_and_payments(ctx: Context, date_from: Optional[str] = None, date_to: Optional[str] = None):
    """
    Generate a reconciliation report matching invoices with their corresponding payments.
    
    Args:
        date_from: Filter from this date (format: YYYY-MM-DD)
        date_to: Filter until this date (format: YYYY-MM-DD)
        
    Returns:
        List of invoices with their linked payments and reconciliation status
    """
    try:
        await ctx.info("Starting reconciliation of invoices and payments...")
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # Create filter domain for invoices
        invoice_domain = [("move_type", "in", ["in_invoice", "out_invoice"])]
        if date_from:
            invoice_domain.append(("invoice_date", ">=", date_from))
        if date_to:
            invoice_domain.append(("invoice_date", "<=", date_to))
        
        # Limit to 5 invoices to avoid long wait times
        limit = 5
        await ctx.info(f"Querying invoices with domain: {invoice_domain}, limit: {limit}")
        
        # Get invoices
        invoices = await odoo_client.execute_kw(
            "account.move", "search_read",
            [invoice_domain],
            {"fields": [
                "id", "name", "amount_total", "amount_residual",
                "invoice_date", "state", "payment_state",
                "partner_id", "currency_id", "move_type"
            ], "limit": limit}
        )
        
        await ctx.info(f"Found {len(invoices)} invoices")
        
        # Format results with reconciliation info
        reconciliation_data = []
        
        for i, invoice in enumerate(invoices):
            await ctx.info(f"Processing invoice {i+1}/{len(invoices)}: {invoice.get('name', 'No name')}")
            invoice_data = format_invoice(invoice)
            
            # Add invoice type info
            invoice_data["type"] = "vendor_bill" if invoice["move_type"] == "in_invoice" else "customer_invoice"
            
            # Get payments linked to this invoice
            # This is a simplified approach - a more accurate implementation
            # would need to check actual reconciliation records in Odoo
            payment_domain = [("reconciled_invoice_ids", "in", [invoice["id"]])]
            
            await ctx.info(f"Querying payments for invoice {invoice.get('name', 'No name')}")
            payments = await odoo_client.execute_kw(
                "account.payment", "search_read",
                [payment_domain],
                {"fields": [
                    "id", "name", "amount", "date", "state", 
                    "payment_type", "partner_id", "journal_id"
                ]}
            )
            
            await ctx.info(f"Found {len(payments)} payments for invoice {invoice.get('name', 'No name')}")
            
            # Format payments
            invoice_data["payments"] = [format_payment(payment) for payment in payments]
            
            # Calculate reconciliation status
            total_paid = sum(payment["amount"] for payment in payments)
            invoice_data["total_paid"] = total_paid
            invoice_data["outstanding"] = invoice_data["amount_total"] - total_paid
            
            # Determine if fully reconciled
            invoice_data["is_reconciled"] = (
                invoice_data["payment_state"] == "paid" or 
                abs(invoice_data["outstanding"]) < 0.01  # Allow for small rounding differences
            )
            
            reconciliation_data.append(invoice_data)
        
        await ctx.info("Reconciliation completed successfully")
        return reconciliation_data
    except Exception as e:
        await ctx.error(f"Error reconciling invoices and payments: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_accounting_entries(ctx: Context, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 100):
    """
    Get journal entries for accounting analysis.
    
    Args:
        date_from: Filter from this date (format: YYYY-MM-DD)
        date_to: Filter until this date (format: YYYY-MM-DD)
        limit: Maximum number of entries to return
        
    Returns:
        List of accounting entries with their line items
    """
    try:
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # Create filter domain for journal entries
        entry_domain = [("move_type", "=", "entry")]  # Only get pure accounting entries
        if date_from:
            entry_domain.append(("date", ">=", date_from))
        if date_to:
            entry_domain.append(("date", "<=", date_to))
        
        # Get journal entries
        entries = await odoo_client.execute_kw(
            "account.move", "search_read",
            [entry_domain],
            {"fields": [
                "id", "name", "date", "ref", "journal_id", "state"
            ], "limit": limit}
        )
        
        result = []
        for entry in entries:
            # Get lines for this entry
            line_ids = await odoo_client.execute_kw(
                "account.move.line", "search_read",
                [[("move_id", "=", entry["id"])]],
                {"fields": [
                    "name", "account_id", "partner_id", "debit", "credit", 
                    "balance", "matching_number"
                ]}
            )
            
            entry_data = {
                "id": entry["id"],
                "name": entry["name"],
                "date": entry["date"],
                "reference": entry.get("ref", ""),
                "journal": entry.get("journal_id", [False, ""])[1],
                "state": entry["state"],
                "lines": line_ids,
                "total_debit": sum(line["debit"] for line in line_ids),
                "total_credit": sum(line["credit"] for line in line_ids),
            }
            
            result.append(entry_data)
        
        return result
    except Exception as e:
        await ctx.error(f"Error fetching accounting entries: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_suppliers(ctx: Context, name: Optional[str] = None, limit: int = 100):
    """
    List suppliers (vendors) with optional name filtering.
    
    Args:
        name: Filter suppliers by name (partial match)
        limit: Maximum number of suppliers to return
        
    Returns:
        List of suppliers with their basic information
    """
    try:
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # Create domain filter
        domain = [("supplier_rank", ">", 0)]  # Only suppliers
        if name:
            domain.append(("name", "ilike", name))
        
        # Get supplier partners
        suppliers = await odoo_client.execute_kw(
            "res.partner", "search_read",
            [domain],
            {"fields": [
                "id", "name", "vat", "email", "phone", "supplier_rank",
                "street", "city", "zip", "country_id", "category_id"
            ], "limit": limit}
        )
        
        # Format the response
        result = []
        for supplier in suppliers:
            supplier_data = {
                "id": supplier["id"],
                "name": supplier["name"],
                "vat": supplier.get("vat", ""),
                "email": supplier.get("email", ""),
                "phone": supplier.get("phone", ""),
                "supplier_rank": supplier.get("supplier_rank", 0),
                "address": {
                    "street": supplier.get("street", ""),
                    "city": supplier.get("city", ""),
                    "zip": supplier.get("zip", ""),
                    "country": supplier.get("country_id", [False, ""])[1] if supplier.get("country_id") else "",
                },
                "categories": [
                    {"id": cat[0], "name": cat[1]} 
                    for cat in supplier.get("category_id", [])
                ] if isinstance(supplier.get("category_id"), list) else []
            }
            result.append(supplier_data)
        
        return result
    except Exception as e:
        await ctx.error(f"Error listing suppliers: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_customers(ctx: Context, name: Optional[str] = None, limit: int = 100):
    """
    List customers with optional name filtering.
    
    Args:
        name: Filter customers by name (partial match)
        limit: Maximum number of customers to return
        
    Returns:
        List of customers with their basic information
    """
    try:
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # Create domain filter
        domain = [("customer_rank", ">", 0)]  # Only customers
        if name:
            domain.append(("name", "ilike", name))
        
        # Get customer partners
        customers = await odoo_client.execute_kw(
            "res.partner", "search_read",
            [domain],
            {"fields": [
                "id", "name", "vat", "email", "phone", "customer_rank",
                "street", "city", "zip", "country_id", "category_id"
            ], "limit": limit}
        )
        
        # Format the response
        result = []
        for customer in customers:
            customer_data = {
                "id": customer["id"],
                "name": customer["name"],
                "vat": customer.get("vat", ""),
                "email": customer.get("email", ""),
                "phone": customer.get("phone", ""),
                "customer_rank": customer.get("customer_rank", 0),
                "address": {
                    "street": customer.get("street", ""),
                    "city": customer.get("city", ""),
                    "zip": customer.get("zip", ""),
                    "country": customer.get("country_id", [False, ""])[1] if customer.get("country_id") else "",
                },
                "categories": [
                    {"id": cat[0], "name": cat[1]} 
                    for cat in customer.get("category_id", [])
                ] if isinstance(customer.get("category_id"), list) else []
            }
            result.append(customer_data)
        
        return result
    except Exception as e:
        await ctx.error(f"Error listing customers: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def find_entries_by_account(ctx: Context, account_number: str, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 100):
    """
    Find accounting entries (moves) related to a specific account number.
    
    Args:
        account_number: Account number to search for (e.g. "570", "400")
        date_from: Filter from this date (format: YYYY-MM-DD)
        date_to: Filter until this date (format: YYYY-MM-DD)
        limit: Maximum number of entries to return
        
    Returns:
        List of accounting entries related to the specified account
    """
    try:
        await ctx.info(f"Looking for accounting entries with account {account_number}...")
        
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # First we search for account entries that match the account number
        account_domain = [("code", "like", account_number)]
        account_ids = await odoo_client.execute_kw(
            "account.account", "search",
            [account_domain],
            {}
        )
        
        if not account_ids:
            await ctx.info(f"No accounts found matching the number {account_number}")
            return {"error": f"No accounts found matching the number {account_number}"}
        
        await ctx.info(f"Found {len(account_ids)} accounts with the code {account_number}")
        
        # Search for move lines related to these accounts
        line_domain = [("account_id", "in", account_ids)]
        if date_from:
            line_domain.append(("date", ">=", date_from))
        if date_to:
            line_domain.append(("date", "<=", date_to))
        
        await ctx.info(f"Searching move lines with domain: {line_domain}")
        line_ids = await odoo_client.execute_kw(
            "account.move.line", "search",
            [line_domain],
            {"limit": limit}
        )
        
        if not line_ids:
            await ctx.info(f"No move lines found for accounts {account_number}")
            return {"error": f"No move lines found for accounts {account_number}"}
        
        await ctx.info(f"Found {len(line_ids)} move lines")
        
        # Get information about the lines
        line_data = await odoo_client.execute_kw(
            "account.move.line", "read",
            [line_ids],
            {"fields": [
                "name", "account_id", "partner_id", "debit", "credit", 
                "balance", "matching_number", "move_id", "date",
                "journal_id", "ref"
            ]}
        )
        
        # Group lines by accounting entry (move_id)
        move_ids = list(set(line["move_id"][0] for line in line_data if line.get("move_id")))
        
        # Get complete information about the moves
        move_data = await odoo_client.execute_kw(
            "account.move", "read",
            [move_ids],
            {"fields": [
                "id", "name", "date", "ref", "journal_id", 
                "state", "partner_id", "amount_total"
            ]}
        )
        
        # For each entry, get all its lines (including those not from the account being searched)
        result = []
        for move in move_data:
            # Get all lines for this entry
            all_lines = await odoo_client.execute_kw(
                "account.move.line", "search_read",
                [[("move_id", "=", move["id"])]],
                {"fields": [
                    "name", "account_id", "partner_id", "debit", "credit", 
                    "balance", "matching_number"
                ]}
            )
            
            # Add to the result as a complete entry with all its lines
            move_info = {
                "id": move["id"],
                "name": move["name"],
                "date": move["date"],
                "reference": move.get("ref", ""),
                "journal": move.get("journal_id", [False, ""])[1] if move.get("journal_id") else "",
                "state": move["state"],
                "partner": move.get("partner_id", [False, ""])[1] if move.get("partner_id") else "",
                "lines": all_lines,
                "has_account": account_number,
                "total_debit": sum(line["debit"] for line in all_lines),
                "total_credit": sum(line["credit"] for line in all_lines),
            }
            result.append(move_info)
        
        await ctx.info(f"Processed {len(result)} accounting entries related to account {account_number}")
        return result
    except Exception as e:
        await ctx.error(f"Error searching entries for account {account_number}: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def trace_account_flow(ctx: Context, from_account: str, to_account: str, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 10):
    """
    Trace the money flow between two account types, searching for the relationship between accounting entries.
    
    Args:
        from_account: Source account number (e.g. "572" for banks)
        to_account: Destination account number (e.g. "400" for suppliers)
        date_from: Filter from this date (format: YYYY-MM-DD)
        date_to: Filter until this date (format: YYYY-MM-DD)
        limit: Maximum number of flows to analyze
        
    Returns:
        List of relationships found between the specified accounts
    """
    try:
        await ctx.info(f"Analyzing accounting flow from account {from_account} to account {to_account}...")
        
        # Get Odoo client using the context handler
        odoo_client = await get_odoo_client_from_context(ctx)
        
        # First we search for account entries that match the provided numbers
        from_account_domain = [("code", "like", from_account)]
        from_account_ids = await odoo_client.execute_kw(
            "account.account", "search",
            [from_account_domain],
            {}
        )
        
        to_account_domain = [("code", "like", to_account)]
        to_account_ids = await odoo_client.execute_kw(
            "account.account", "search",
            [to_account_domain],
            {}
        )
        
        if not from_account_ids:
            return {"error": f"No accounts found matching the number {from_account}"}
        
        if not to_account_ids:
            return {"error": f"No accounts found matching the number {to_account}"}
        
        await ctx.info(f"Found {len(from_account_ids)} source accounts and {len(to_account_ids)} destination accounts")
        
        # Look for entries that contain both source and destination accounts
        # For this, first we search for lines with the source account
        from_line_domain = [("account_id", "in", from_account_ids)]
        if date_from:
            from_line_domain.append(("date", ">=", date_from))
        if date_to:
            from_line_domain.append(("date", "<=", date_to))
        
        from_lines = await odoo_client.execute_kw(
            "account.move.line", "search_read",
            [from_line_domain],
            {"fields": ["move_id", "partner_id", "date"], "limit": 100}
        )
        
        # Extract the IDs of entries and partners found
        move_ids = list(set(line["move_id"][0] for line in from_lines if line.get("move_id")))
        partner_ids = list(set(line["partner_id"][0] for line in from_lines if line.get("partner_id")))
        
        await ctx.info(f"Found {len(move_ids)} entries related to account {from_account}")
        
        # Look for directly related entries (same entry contains both accounts)
        direct_relations = []
        for move_id in move_ids:
            # Check if this entry also has lines with the destination account
            to_lines_in_move = await odoo_client.execute_kw(
                "account.move.line", "search_read",
                [[("move_id", "=", move_id), ("account_id", "in", to_account_ids)]],
                {"fields": ["name", "account_id", "debit", "credit", "balance"]}
            )
            
            if to_lines_in_move:
                # This entry contains both the source and destination account
                move_info = await odoo_client.execute_kw(
                    "account.move", "read",
                    [move_id],
                    {"fields": ["name", "date", "ref", "journal_id", "state", "partner_id"]}
                )
                
                # Get all lines for this entry
                all_lines = await odoo_client.execute_kw(
                    "account.move.line", "search_read",
                    [[("move_id", "=", move_id)]],
                    {"fields": ["name", "account_id", "debit", "credit", "balance"]}
                )
                
                direct_relations.append({
                    "type": "direct_relation",
                    "move": move_info[0] if move_info else {"id": move_id},
                    "lines": all_lines,
                })
        
        # If we haven't found enough direct relationships, look for indirect relationships
        indirect_relations = []
        if len(direct_relations) < limit and partner_ids:
            # Look for entries with the destination account that have the same partners
            to_line_domain = [
                ("account_id", "in", to_account_ids),
                ("partner_id", "in", partner_ids)
            ]
            if date_from:
                to_line_domain.append(("date", ">=", date_from))
            if date_to:
                to_line_domain.append(("date", "<=", date_to))
            
            to_lines = await odoo_client.execute_kw(
                "account.move.line", "search_read",
                [to_line_domain],
                {"fields": ["move_id", "partner_id", "date"], "limit": 100}
            )
            
            # Filter entries that are not in the direct relationships
            related_move_ids = list(set(line["move_id"][0] for line in to_lines if line.get("move_id")))
            new_move_ids = [m for m in related_move_ids if m not in move_ids]
            
            for move_id in new_move_ids[:limit - len(direct_relations)]:
                move_info = await odoo_client.execute_kw(
                    "account.move", "read",
                    [move_id],
                    {"fields": ["name", "date", "ref", "journal_id", "state", "partner_id"]}
                )
                
                # Get all lines for this entry
                all_lines = await odoo_client.execute_kw(
                    "account.move.line", "search_read",
                    [[("move_id", "=", move_id)]],
                    {"fields": ["name", "account_id", "debit", "credit", "balance"]}
                )
                
                # Find the specific line with the destination account
                to_account_lines = [l for l in all_lines if l.get("account_id") and l["account_id"][0] in to_account_ids]
                
                if to_account_lines and move_info:
                    # Find the relationship with the source entry
                    partner_id = move_info[0].get("partner_id", [False, ""])[0] if move_info[0].get("partner_id") else None
                    
                    # Find source entries related to this partner
                    related_from_moves = [
                        line["move_id"][0] for line in from_lines 
                        if line.get("partner_id") and line["partner_id"][0] == partner_id
                    ]
                    
                    if related_from_moves:
                        indirect_relations.append({
                            "type": "indirect_relation",
                            "to_move": move_info[0],
                            "to_lines": all_lines,
                            "related_from_moves": related_from_moves,
                            "partner": move_info[0].get("partner_id", [False, ""])[1] if move_info[0].get("partner_id") else "",
                        })
        
        # Combine results
        result = {
            "from_account": from_account,
            "to_account": to_account,
            "direct_relations": direct_relations,
            "indirect_relations": indirect_relations,
            "total_direct_relations": len(direct_relations),
            "total_indirect_relations": len(indirect_relations),
        }
        
        await ctx.info(f"Analysis completed. Found {len(direct_relations)} direct relationships and {len(indirect_relations)} indirect relationships")
        return result
    except Exception as e:
        await ctx.error(f"Error analyzing accounting flow: {str(e)}")
        return {"error": str(e)} 