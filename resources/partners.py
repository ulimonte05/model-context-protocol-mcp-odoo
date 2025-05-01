"""
Partner resources for MCP-Odoo
"""
from typing import Optional
from pydantic import AnyUrl

from mcp.server.fastmcp import Context
from ..mcp_instance import AppContext, mcp
from ..context_handler import get_odoo_client_from_context

# Helper functions to format partner data in markdown
def format_partner_to_markdown(partner):
    """Format a partner as markdown"""
    response = f"# {partner['name']}\n\n"
    response += f"**{'Company' if partner['is_company'] else 'Individual'}**\n\n"
    
    # Contact information
    if partner.get("email"):
        response += f"- Email: {partner['email']}\n"
    if partner.get("phone"):
        response += f"- Phone: {partner['phone']}\n"
        
    # Address
    address = []
    if partner.get("street"):
        address.append(partner["street"])
    if partner.get("city"):
        address.append(partner["city"])
    if partner.get("zip"):
        address.append(partner["zip"])
    if partner.get("country_id"):
        address.append(partner["country_id"][1])  # Country name is second element
        
    if address:
        response += f"- Address: {', '.join(address)}\n"
    
    return response

# Direct resources
@mcp.resource("resource://partners")
async def partners_resource() -> str:
    """Get all partners (companies) from Odoo"""
    try:
        # Get context to access the Odoo client
        ctx = mcp.get_context()
        odoo_client = get_odoo_client_from_context(ctx)
        
        # Get partners from Odoo
        partners = await odoo_client.execute_kw(
            "res.partner",
            "search_read",
            [[["is_company", "=", True]]],
            {"fields": ["name", "email", "phone", "street", "city", "zip", "country_id", "child_ids", "is_company"]}
        )

        if not partners:
            return "No partners found."

        # Format response in markdown
        response = "# Partners\n\n"
        for partner in partners:
            response += f"## {partner['name']}\n"
            response += "**Company**\n\n"
            
            # Contact information
            if partner.get("email"):
                response += f"- Email: {partner['email']}\n"
            if partner.get("phone"):
                response += f"- Phone: {partner['phone']}\n"
            
            # Address
            address = []
            if partner.get("street"):
                address.append(partner["street"])
            if partner.get("city"):
                address.append(partner["city"])
            if partner.get("zip"):
                address.append(partner["zip"])
            if partner.get("country_id"):
                address.append(partner["country_id"][1])  # Country name is second element
            
            if address:
                response += f"- Address: {', '.join(address)}\n"
            
            # Related contacts
            if partner.get("child_ids"):
                contacts = await odoo_client.execute_kw(
                    "res.partner",
                    "read",
                    [partner["child_ids"]],
                    {"fields": ["name", "function"]}
                )
                if contacts:
                    response += "\n**Contacts:**\n"
                    for contact in contacts:
                        response += f"- {contact['name']}"
                        if contact.get("function"):
                            response += f" ({contact['function']})"
                        response += "\n"
        
            response += "\n"

        return response
    except Exception as e:
        logger.error(f"Error fetching partners: {e}")
        return f"Error fetching partners: {str(e)}"

# Resources with template
@mcp.resource("resource://partners/{partner_id}")
async def partner_detail(partner_id: int) -> str:
    """Get details of a specific partner by ID"""
    try:
        # Get context to access the Odoo client
        ctx = mcp.get_context()
        odoo_client = get_odoo_client_from_context(ctx)
        
        # Get partner from Odoo
        partners = await odoo_client.execute_kw(
            "res.partner",
            "read",
            [partner_id],
            {"fields": ["name", "email", "phone", "street", "city", "zip", "country_id", "child_ids", "is_company"]}
        )

        if not partners:
            return f"Partner with ID {partner_id} not found."

        partner = partners[0]
        
        # Format response in markdown
        response = format_partner_to_markdown(partner)
        
        # Related contacts (only for companies)
        if partner['is_company'] and partner.get("child_ids"):
            contacts = await odoo_client.execute_kw(
                "res.partner",
                "read",
                [partner["child_ids"]],
                {"fields": ["name", "function"]}
            )
            if contacts:
                response += "\n**Contacts:**\n"
                for contact in contacts:
                    response += f"- {contact['name']}"
                    if contact.get("function"):
                        response += f" ({contact['function']})"
                    response += "\n"

        return response
    except Exception as e:
        logger.error(f"Error fetching partner details: {e}")
        return f"Error fetching partner details: {str(e)}"

# Add logger import
import logging
logger = logging.getLogger(__name__) 