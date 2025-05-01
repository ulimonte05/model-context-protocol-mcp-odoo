# MCP-Odoo Implementation Guide

This guide provides comprehensive information about implementing and extending the MCP-Odoo connector, which bridges Odoo ERP systems with AI agents using the Model Context Protocol (MCP).

## Introduction

MCP-Odoo enables AI agents to access and manipulate Odoo data through a standardized interface. It exposes accounting data, partner information, and other Odoo resources to AI agents via the Model Context Protocol, allowing conversational and automated interaction with ERP data.

The connector serves as a bridge between:
- **Odoo ERP systems** - Where business data resides
- **AI agents** - That need to query and analyze this data
- **Model Context Protocol** - The standard that enables this communication

## Technical Foundation

### The Model Context Protocol (MCP)

MCP standardizes how to expose data and functionality to Large Language Model (LLM) agents. An MCP server behaves like a specialized web API with:

- **Resources**: For delivering data (similar to GET endpoints)
- **Tools**: For executing actions with effects (similar to POST endpoints)

The Python SDK, particularly in version 1.6.0+, provides a simple way to create MCP servers with:
- Multiple transport methods (stdio, SSE)
- Structured tools and resources
- Application lifecycle management

### FastMCP Architecture

At its core, the MCP-Odoo server is built on the FastMCP implementation which provides:

1. **Server Definition**: Creating a named MCP server instance
```python
mcp = FastMCP(
    name="mcp-odoo",
    version="1.0.0",
    instructions="MCP server for Odoo accounting integration..."
)
```

2. **Tool/Resource Registration**: Exposing functionality to agents
```python
@mcp.tool()
async def odoo_version(ctx: Context) -> str:
    """Get the Odoo server version."""
    # Implementation...
```

3. **Application Lifecycle**: Managing connections and resources
```python
@asynccontextmanager
async def app_lifespan() -> AsyncGenerator[AppContext, None]:
    # Initialize resources
    client = OdooClient(...)
    await client.connect()
    
    try:
        yield AppContext(odoo_client=client, ...)
    finally:
        # Clean up resources
        await client.disconnect()
```

4. **Transport Support**: Allowing both local (stdio) and remote (SSE) access
```python
# Run with appropriate transport
mcp.run(transport="sse")  # or "stdio"
```

## Odoo Integration Architecture

### Connection Management

MCP-Odoo connects to Odoo instances using the XML-RPC protocol. The connection is managed in several layers:

1. **Configuration Layer**: Environment variables or `.env` files specify connection parameters
```
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
```

2. **Client Layer**: The `OdooClient` class manages the XML-RPC connection
```python
class OdooClient:
    """Client for connecting to Odoo via XML-RPC with accounting support."""
    
    def __init__(self, url, database, username, password):
        # Initialize connection parameters
        
    async def connect(self) -> int:
        """Connect to Odoo and authenticate user."""
        
    async def execute_kw(self, model, method, args, kwargs=None) -> Any:
        """Execute method on model with arguments."""
```

3. **Context Layer**: Resources are initialized once and shared throughout the application lifecycle
```python
@dataclass
class AppContext:
    """Application context for MCP-Odoo"""
    odoo_client: OdooClient
    config: Dict[str, Any]
```

### Resource Organization

MCP-Odoo organizes Odoo resources into logical modules:

1. **Partners**: Contact and company information
2. **Accounting**: Financial data including invoices, payments, and reconciliation
3. **(Extensible)**: Additional modules can be added for other Odoo functionality

Each resource module defines tools that agents can use to interact with that part of the Odoo system.

## Key Accounting Functionality

The MCP-Odoo connector particularly focuses on accounting functionality, allowing AI agents to:

### 1. Query Accounting Documents

- **List vendor bills** - View incoming invoices from suppliers
- **List customer invoices** - View outgoing invoices to customers
- **View payment records** - See payments made or received
- **Get detailed invoice information** - Access line items, tax details, etc.

### 2. Perform Reconciliation Analysis

Reconciliation is the process of matching payments with invoices, confirming that:
- Each payment corresponds to an invoice
- Each invoice is eventually paid (fully or partially)

The system uses Odoo's accounting principles, where:
- A vendor bill creates an entry with:
  - DEBIT: Expense account (e.g., 6000 Purchases)
  - CREDIT: Vendor liability account (e.g., 4000 Accounts Payable)

- A payment creates an entry with:
  - DEBIT: Vendor liability account (e.g., 4000 Accounts Payable)
  - CREDIT: Bank/cash account (e.g., 5720 Bank)

- When reconciled, the vendor liability account nets to zero

The MCP-Odoo connector exposes this logic through tools that can:
- Match payments to corresponding invoices
- Determine payment status of invoices
- Analyze partial payments and multiple invoices

## Implementation Details

### Server Initialization

The server is initialized in `mcp_instance.py` with:

```python
mcp = FastMCP(
    name="mcp-odoo",
    version="1.0.0",
    instructions="MCP server for Odoo accounting integration...",
    dependencies=["xmlrpc", "pydantic"]
)

# Set lifespan for resource management
mcp.lifespan = app_lifespan
```

### Transport Handling

The server supports both stdio (for local agents) and SSE (for remote HTTP clients) transport methods. This is configured in `__main__.py`:

```python
def main():
    parser = argparse.ArgumentParser(description="MCP Odoo Integration Server")
    parser.add_argument(
        "--transport",
        type=str,
        choices=["stdio", "sse"],
        default="sse",
        help="Transport to use: stdio (local agents) or sse (remote HTTP clients)"
    )
    # ...parse other arguments...
    
    run_server(
        transport=args.transport,
        host=args.host,
        port=args.port
    )
```

### Tool Implementation

Tools are implemented using the `@mcp.tool()` decorator, typically with:
1. Access to the context (which contains the Odoo client)
2. Specific parameters for the tool
3. Error handling and logging
4. Type annotations for better agent understanding

Example:
```python
@mcp.tool()
async def list_vendor_bills(ctx: Context, limit: int = 20) -> List[Dict[str, Any]]:
    """List vendor bills (supplier invoices)."""
    try:
        # Get client from context
        client = get_odoo_client_from_context(ctx)
        
        # Query Odoo
        domain = [('move_type', '=', 'in_invoice')]
        result = await client.search_read(
            model="account.move",
            domain=domain,
            fields=["name", "partner_id", "amount_total", "invoice_date", "payment_state"],
            limit=limit
        )
        
        return result
    except Exception as e:
        logger.error(f"Error listing vendor bills: {str(e)}")
        raise
```

## Context Handling and Troubleshooting

A crucial aspect of MCP-Odoo is proper context handling - ensuring that the Odoo client is properly extracted from the context or recreated if needed. Common issues include:

- Context serialization issues: Sometimes the context is serialized to a dictionary instead of passed as an object
- Connection management: Ensuring connections are reused or reconnected as needed
- Type consistency: Ensuring all tools use the same parameter types and patterns

The connector includes a helper function to handle these issues:

```python
def get_odoo_client_from_context(ctx: Context) -> OdooClient:
    """
    Safely extract Odoo client from context or recreate it if needed.
    
    This function handles common issues where AppContext
    might be passed as a dictionary instead of a proper object.
    """
    # Implementation that checks types and recovers as needed
```

## Adding New Functionality

To extend the MCP-Odoo connector with new Odoo functionality:

1. **Create a new resource file**: Add a Python module in the `resources/` directory
   ```
   mcp_odoo_public/resources/my_new_module.py
   ```

2. **Define tools using decorators**:
   ```python
   @mcp.tool()
   async def my_new_function(ctx: Context, param1: str) -> Dict[str, Any]:
       """Documentation for the new tool."""
       client = get_odoo_client_from_context(ctx)
       # Implementation...
       return result
   ```

3. **Register in the __init__.py file**:
   ```python
   # In resources/__init__.py
   from .my_new_module import my_new_function
   
   __all__ = [
       # ... existing tools ...
       "my_new_function",
   ]
   ```

4. **Import in server.py** to ensure the tool is registered:
   ```python
   # In server.py
   from .resources import my_new_module
   ```

## Best Practices

### Odoo Query Performance

- Use specific fields in `search_read` calls to limit data transfer
- Add appropriate domain filters to reduce result sets
- Consider pagination for large datasets (offset/limit)
- Use indexes when available in Odoo models

### Error Handling

Implement comprehensive error handling:
- Catch and log specific exceptions
- Provide meaningful error messages for agents
- Handle reconnection scenarios

### Security Considerations

- Never hardcode credentials
- Use `.env` files or environment variables
- Consider using API keys instead of passwords when possible
- Limit exposed functionality to what agents actually need

## Conclusion

The MCP-Odoo connector provides a powerful bridge between Odoo ERP systems and AI agents. By leveraging the Model Context Protocol, it allows agents to query and analyze accounting data, perform reconciliation, and access Odoo functionality in a standardized way.

The modular architecture makes it easy to extend with additional Odoo functionality while maintaining proper connection management and context handling.

## References

- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [Odoo External API Documentation](https://www.odoo.com/documentation/16.0/developer/api/external_api.html)
- [Odoo Accounting Principles](https://www.odoo.com/documentation/16.0/applications/finance/accounting.html) 