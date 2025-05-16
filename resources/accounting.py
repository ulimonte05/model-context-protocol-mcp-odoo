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

# Models for new request/response types
class SaleOrderFilter(BaseModel):
    """Filter parameters for sales order listing"""
    partner_id: Optional[int] = None
    state: Optional[str] = None  # e.g., 'draft', 'sent', 'sale', 'done', 'cancel'
    date_from: Optional[str] = None # Order date
    date_to: Optional[str] = None   # Order date
    limit: Optional[int] = 100

class SubscriptionFilter(BaseModel):
    """Filter parameters for subscription listing"""
    partner_id: Optional[int] = None
    state: Optional[str] = None # e.g., 'draft', 'open', 'pending', 'closed', 'cancelled'
    template_id: Optional[int] = None
    date_from: Optional[str] = None # Start date
    date_to: Optional[str] = None   # Start date
    limit: Optional[int] = 100

class ProjectFilter(BaseModel):
    """Filter parameters for project listing"""
    partner_id: Optional[int] = None
    user_id: Optional[int] = None # Project manager
    name: Optional[str] = None # Filter by project name (partial match)
    active: Optional[bool] = None # Filter by active status
    limit: Optional[int] = 100

class TaskFilter(BaseModel):
    """Filter parameters for task listing"""
    project_id: Optional[int] = None # Project ID to filter tasks for
    stage_id: Optional[int] = None
    user_id: Optional[int] = None # Assignee
    partner_id: Optional[int] = None
    date_deadline_from: Optional[str] = None
    date_deadline_to: Optional[str] = None
    active: Optional[bool] = None # Filter by active status
    limit: Optional[int] = 100

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

def format_sale_order(order: Dict[str, Any]) -> Dict[str, Any]:
    """Format sale order data for better presentation"""
    return {
        "id": order["id"],
        "name": order["name"],
        "partner": {
            "id": order["partner_id"][0],
            "name": order["partner_id"][1]
        } if order.get("partner_id") else None,
        "date_order": order.get("date_order", ""),
        "amount_total": order.get("amount_total", 0.0),
        "currency": order.get("currency_id", [False, ""])[1] if order.get("currency_id") else "",
        "state": order.get("state", ""),
        "commitment_date": order.get("commitment_date", None),
        "order_line_count": len(order.get("order_line", [])), # Number of lines based on provided IDs
        "salesperson": {
             "id": order["user_id"][0],
             "name": order["user_id"][1]
        } if order.get("user_id") else None,
        "team": {
            "id": order["team_id"][0],
            "name": order["team_id"][1]
        } if order.get("team_id") else None,
    }

def format_subscription(subscription: Dict[str, Any]) -> Dict[str, Any]:
    """Format subscription data for better presentation"""
    return {
        "id": subscription["id"],
        "name": subscription.get("name", subscription.get("code", "")),
        "code": subscription.get("code", ""),
        "partner": {
            "id": subscription["partner_id"][0],
            "name": subscription["partner_id"][1]
        } if subscription.get("partner_id") else None,
        "template": {
            "id": subscription["template_id"][0],
            "name": subscription["template_id"][1]
        } if subscription.get("template_id") else None,
        "date_start": subscription.get("date_start", ""),
        "date_end": subscription.get("date", None), # In Odoo 'sale.subscription', 'date' is often the end date
        "recurring_next_date": subscription.get("recurring_next_date", None),
        "stage": {
            "id": subscription["stage_id"][0],
            "name": subscription["stage_id"][1]
        } if subscription.get("stage_id") else None,
        "state": subscription.get("state", ""), # Fallback or specific state field
        "recurring_total": subscription.get("recurring_total", 0.0), # Or amount_total
        "currency": subscription.get("currency_id", [False, ""])[1] if subscription.get("currency_id") else "",
    }

def format_project(project: Dict[str, Any]) -> Dict[str, Any]:
    """Format project data for better presentation"""
    return {
        "id": project["id"],
        "name": project["name"],
        "partner": { # Customer
            "id": project["partner_id"][0],
            "name": project["partner_id"][1]
        } if project.get("partner_id") else None,
        "project_manager": {
            "id": project["user_id"][0],
            "name": project["user_id"][1]
        } if project.get("user_id") else None,
        "task_count": project.get("task_count", 0),
        "active": project.get("active", True),
        "date_start": project.get("date_start", None),
        "date_end": project.get("date", None), # In Odoo 'project.project', 'date' can be the end date
        "privacy_visibility": project.get("privacy_visibility"),
        "label_tasks": project.get("label_tasks", "Tasks"),
        # Projects might use stages or a specific state field; for now, returning what's common
        "allow_timesheets": project.get("allow_timesheets", False),
        "company": {
            "id": project["company_id"][0],
            "name": project["company_id"][1]
        } if project.get("company_id") else None,
    }

def format_task(task: Dict[str, Any]) -> Dict[str, Any]:
    """Format project task data for better presentation"""
    return {
        "id": task["id"],
        "name": task["name"],
        "project": {
            "id": task["project_id"][0],
            "name": task["project_id"][1]
        } if task.get("project_id") else None,
        "stage": {
            "id": task["stage_id"][0],
            "name": task["stage_id"][1]
        } if task.get("stage_id") else None,
        "assignees": [
            {"id": user[0], "name": user[1]} for user in task.get("user_ids", [])
        ] if task.get("user_ids") and isinstance(task.get("user_ids"), list) and task.get("user_ids")[0] is not False else [], # Ensure user_ids is a list of tuples/lists
        "partner": { # Customer associated with task
            "id": task["partner_id"][0],
            "name": task["partner_id"][1]
        } if task.get("partner_id") else None,
        "date_deadline": task.get("date_deadline", None),
        "date_assign": task.get("date_assign", None),
        "date_last_stage_update": task.get("date_last_stage_update", None),
        "progress": task.get("progress", 0.0),
        "description_text": task.get("description", ""), # Text version of description
        "priority": task.get("priority", ""), # '0' (Low), '1' (Normal), '2' (High), '3' (Urgent)
        "active": task.get("active", True),
        "parent_task": {
            "id": task["parent_id"][0],
            "name": task["parent_id"][1]
        } if task.get("parent_id") else None,
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

@mcp.tool()
async def list_sales_orders(ctx: Context, partner_id: Optional[int] = None,
                            state: Optional[str] = None,
                            date_from: Optional[str] = None,
                            date_to: Optional[str] = None,
                            limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List sales orders with optional filtering.
    
    Args:
        partner_id: Filter by specific customer ID
        state: Filter by sales order state (e.g., 'draft', 'sent', 'sale', 'done', 'cancel')
        date_from: Filter orders from this date (order date, format: YYYY-MM-DD)
        date_to: Filter orders until this date (order date, format: YYYY-MM-DD)
        limit: Maximum number of orders to return
        
    Returns:
        List of sales orders
    """
    domain = []
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if state:
        domain.append(("state", "=", state))
    if date_from:
        domain.append(("date_order", ">=", date_from))
    if date_to:
        domain.append(("date_order", "<=", date_to))
        
    odoo_client = await get_odoo_client_from_context(ctx)
    fields = [
        "id", "name", "partner_id", "date_order", "amount_total", "state", 
        "currency_id", "commitment_date", "order_line", "user_id", "team_id"
    ]
    
    try:
        await ctx.info(f"Fetching sales orders with domain: {domain}")
        orders = await odoo_client.execute_kw(
            "sale.order", "search_read",
            [domain],
            {"fields": fields, "limit": limit, "order": "date_order DESC"}
        )
        return [format_sale_order(order) for order in orders]
    except Exception as e:
        await ctx.error(f"Error fetching sales orders: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_subscriptions(ctx: Context, partner_id: Optional[int] = None,
                             state: Optional[str] = None, # e.g. sale.subscription stage code or state field
                             template_id: Optional[int] = None,
                             date_from: Optional[str] = None, # Start date
                             date_to: Optional[str] = None,   # Start date
                             limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List subscriptions (recurrent sales) with optional filtering.
    
    Args:
        partner_id: Filter by specific customer ID
        state: Filter by subscription state/stage code (e.g., 'draft', 'open', 'pending', 'closed')
        template_id: Filter by subscription template ID
        date_from: Filter subscriptions starting from this date (format: YYYY-MM-DD)
        date_to: Filter subscriptions starting until this date (format: YYYY-MM-DD)
        limit: Maximum number of subscriptions to return
        
    Returns:
        List of subscriptions
    """
    domain = []
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if state:
        # Odoo subscriptions often use stage_id.code or a 'state' field.
        # Assuming 'state' for simplicity, or client needs to know stage code.
        # A more robust filter might involve searching stage_id.code or name.
        domain.append(("state", "=", state)) 
    if template_id:
        domain.append(("template_id", "=", template_id))
    if date_from:
        domain.append(("date_start", ">=", date_from))
    if date_to:
        domain.append(("date_start", "<=", date_to))
        
    odoo_client = await get_odoo_client_from_context(ctx)
    fields = [
        "id", "name", "code", "partner_id", "template_id", "date_start", "date", # 'date' is end_date
        "recurring_next_date", "stage_id", "state", "recurring_total", "currency_id"
    ]
    
    try:
        await ctx.info(f"Fetching subscriptions with domain: {domain}")
        subscriptions = await odoo_client.execute_kw(
            "sale.subscription", "search_read", # Assumes 'sale.subscription' model exists
            [domain],
            {"fields": fields, "limit": limit, "order": "date_start DESC"}
        )
        return [format_subscription(sub) for sub in subscriptions]
    except Exception as e:
        # Check if the error is due to the model not existing
        if "sale.subscription" in str(e) and ("model" in str(e).lower() or "object" in str(e).lower()):
            await ctx.error(f"Error fetching subscriptions: {str(e)}. Model 'sale.subscription' might not be installed.")
            return {"error": f"Model 'sale.subscription' not found. Ensure the Subscriptions app is installed in Odoo. Details: {str(e)}"}
        await ctx.error(f"Error fetching subscriptions: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_projects(ctx: Context, partner_id: Optional[int] = None,
                        user_id: Optional[int] = None,
                        name: Optional[str] = None,
                        active: Optional[bool] = None,
                        limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List projects with optional filtering.
    
    Args:
        partner_id: Filter by customer ID associated with the project
        user_id: Filter by project manager (user ID)
        name: Filter by project name (partial match, case-insensitive)
        active: Filter by active status (True for active, False for archived)
        limit: Maximum number of projects to return
        
    Returns:
        List of projects
    """
    domain = []
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if user_id:
        domain.append(("user_id", "=", user_id))
    if name:
        domain.append(("name", "ilike", name))
    if active is not None:
        domain.append(("active", "=", active))
    else: # Default to active projects if not specified
        domain.append(("active", "=", True))


    odoo_client = await get_odoo_client_from_context(ctx)
    fields = [
        "id", "name", "partner_id", "user_id", "task_count", "active", 
        "date_start", "date", "privacy_visibility", "label_tasks", "allow_timesheets", "company_id"
    ]
    
    try:
        await ctx.info(f"Fetching projects with domain: {domain}")
        projects = await odoo_client.execute_kw(
            "project.project", "search_read",
            [domain],
            {"fields": fields, "limit": limit, "order": "name ASC"}
        )
        return [format_project(project) for project in projects]
    except Exception as e:
        await ctx.error(f"Error fetching projects: {str(e)}")
        return {"error": str(e)}

@mcp.tool()
async def list_project_tasks(ctx: Context, project_id: Optional[int] = None,
                             stage_id: Optional[int] = None,
                             user_id: Optional[int] = None, # Assignee
                             partner_id: Optional[int] = None,
                             date_deadline_from: Optional[str] = None,
                             date_deadline_to: Optional[str] = None,
                             active: Optional[bool] = None,
                             limit: Optional[int] = 100) -> List[Dict[str, Any]]:
    """
    List project tasks with optional filtering.
    
    Args:
        project_id: Filter tasks for a specific project ID. If None, lists tasks across all accessible projects.
        stage_id: Filter by task stage ID (project.task.type)
        user_id: Filter by assigned user ID (searches in user_ids many2many field)
        partner_id: Filter by customer ID associated with the task
        date_deadline_from: Filter tasks with deadline from this date (format: YYYY-MM-DD)
        date_deadline_to: Filter tasks with deadline until this date (format: YYYY-MM-DD)
        active: Filter by active status (True for active, False for archived)
        limit: Maximum number of tasks to return
        
    Returns:
        List of project tasks
    """
    domain = []
    if project_id:
        domain.append(("project_id", "=", project_id))
    if stage_id:
        domain.append(("stage_id", "=", stage_id))
    if user_id: # For many2many 'user_ids'
        domain.append(("user_ids", "in", [user_id]))
    if partner_id:
        domain.append(("partner_id", "=", partner_id))
    if date_deadline_from:
        domain.append(("date_deadline", ">=", date_deadline_from))
    if date_deadline_to:
        domain.append(("date_deadline", "<=", date_deadline_to))
    if active is not None:
        domain.append(("active", "=", active))
    else: # Default to active tasks if not specified
        domain.append(("active", "=", True))

    odoo_client = await get_odoo_client_from_context(ctx)
    fields = [
        "id", "name", "project_id", "stage_id", "user_ids", "partner_id", 
        "date_deadline", "date_assign", "date_last_stage_update",
        "progress", 
        "description", "priority", "active",
        "parent_id"
    ]
    
    try:
        await ctx.info(f"Fetching project tasks with domain: {domain}")
        tasks = await odoo_client.execute_kw(
            "project.task", "search_read",
            [domain],
            {"fields": fields, "limit": limit, "order": "priority DESC, date_deadline ASC, name ASC"}
        )
        return [format_task(task) for task in tasks]
    except Exception as e:
        await ctx.error(f"Error fetching project tasks: {str(e)}")
        return {"error": str(e)} 