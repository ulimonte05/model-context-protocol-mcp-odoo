# Troubleshooting Guide

This guide addresses common issues that may arise when using the MCP-Odoo connector, with a special focus on context handling and error resolution.

## Context Handling Issues

One of the most common issues with MCP-Odoo and MCP 1.6.0 in general is related to context handling. The specific problem usually manifests as errors like:

```
Error: 'dict' object has no attribute 'odoo_client'
```

Or in some cases:

```
Error: 'str' object has no attribute 'request_context'
```

### Understanding the Problem

The root cause is that, in certain scenarios of MCP 1.6.0, the `AppContext` instance defined in the lifespan is not properly passed to the tool handlers. Instead:

1. Sometimes it's serialized to an empty or incomplete dictionary
2. In other cases, when finding parameters like `ctx` in the function signature, the system tries to inject an incorrect value (like a string)

### How MCP-Odoo Resolves This

MCP-Odoo implements a robust approach to handle these context issues:

1. **Context Handler Module**: The `context_handler.py` module contains specialized functions to safely extract the Odoo client from the context or recreate it if needed:

```python
def get_odoo_client_from_context(ctx: Context) -> OdooClient:
    """
    Safely extract Odoo client from context or recreate it if needed.
    
    This handles the common issue in MCP 1.6.0 where AppContext
    might be passed as a dictionary instead of a proper object.
    """
    try:
        # Get lifespan context from request context
        app_context = ctx.request_context.lifespan_context
        
        # Handle case when app_context is a dictionary
        if isinstance(app_context, dict):
            # Recreate OdooClient from dictionary data
            from .odoo.client import OdooClient
            from .config import config
            
            logger.info("Context is a dictionary, attempting to extract Odoo client...")
            
            # If dictionary has odoo_client as another dictionary, try to recreate it
            if "odoo_client" in app_context and isinstance(app_context["odoo_client"], dict):
                odoo_data = app_context["odoo_client"]
                client = OdooClient(
                    url=odoo_data.get("url"),
                    database=odoo_data.get("database"),
                    username=odoo_data.get("username"),
                    password=odoo_data.get("password")
                )
                if not client.is_connected:
                    await client.connect()
            else:
                # Create new client using configuration
                config_data = config.as_dict()
                odoo_config = config_data.get("odoo", {})
                client = OdooClient(
                    url=odoo_config.get("host") or odoo_config.get("url"),
                    database=odoo_config.get("database"),
                    username=odoo_config.get("username"),
                    password=odoo_config.get("password")
                )
                await client.connect()
        else:
            # Use client directly from AppContext
            client = app_context.odoo_client
            
        # Check connection status and reconnect if needed
        if not client.is_connected:
            await client.connect()
            
        return client
    except Exception as e:
        logger.error(f"Error getting Odoo client from context: {str(e)}", exc_info=True)
        
        # Fall back to creating a new client from config
        from .config import config
        from .odoo.client import OdooClient
        
        config_data = config.as_dict()
        odoo_config = config_data.get("odoo", {})
        client = OdooClient(
            url=odoo_config.get("host") or odoo_config.get("url"),
            database=odoo_config.get("database"),
            username=odoo_config.get("username"),
            password=odoo_config.get("password")
        )
        await client.connect()
        return client
```

2. **Consistent Tool Definitions**: All tools use consistent type annotations and context handling:

```python
@mcp.tool()
async def list_vendor_bills(ctx: Context, limit: int = 20) -> List[Dict[str, Any]]:
    """List vendor bills (supplier invoices)."""
    try:
        # Get client using the helper function instead of direct access
        client = get_odoo_client_from_context(ctx)
        
        # Rest of implementation...
    except Exception as e:
        logger.error(f"Error listing vendor bills: {str(e)}")
        raise
```

## Common Errors and Solutions

### 1. Connection Issues

**Symptom**: Operations fail with connection errors:
```
Error connecting to Odoo: Connection refused
```

**Possible Causes**:
- Incorrect Odoo URL
- Odoo server is down
- Network connectivity issues
- Firewall blocking connections

**Solutions**:
- Verify the Odoo URL in your `.env` file
- Check if the Odoo server is running
- Test basic connectivity with a simple tool like `curl` or `ping`
- Verify firewall rules

### 2. Authentication Failures

**Symptom**: Operations fail with authentication errors:
```
Authentication failed with the provided credentials
```

**Possible Causes**:
- Incorrect username or password
- Database name is incorrect
- User lacks necessary permissions in Odoo

**Solutions**:
- Double-check credentials in your `.env` file
- Verify the database name
- Ensure the user has appropriate access rights in Odoo
- If using Odoo SaaS, make sure API access is enabled

### 3. Missing Tools in MCP

**Symptom**: Expected tools do not appear when an agent tries to list available tools

**Possible Causes**:
- Tools not properly registered with the MCP instance
- Tools file not imported in server initialization
- Syntax errors in tool definitions

**Solutions**:
- Ensure all tool modules are properly imported in `server.py`
- Check that tools are properly registered in `__init__.py`
- Verify tool definitions have the correct `@mcp.tool()` decorator
- Check logs for any syntax errors or import failures

### 4. Timeout Errors

**Symptom**: Operations fail with timeout errors:
```
Error: Operation timed out
```

**Possible Causes**:
- Odoo server is overloaded
- Query is too complex or returning too much data
- Network latency issues

**Solutions**:
- Increase timeout settings in the configuration
- Optimize queries by reducing fields or adding limits
- Add pagination for large data sets
- Consider indexing frequently queried fields in Odoo

### 5. Data Format Issues

**Symptom**: Operations fail with data format errors or unexpected results:
```
KeyError: 'partner_id'
```

**Possible Causes**:
- Mismatch between expected and actual data format
- Field not requested in the query
- Field does not exist in the Odoo model

**Solutions**:
- Ensure all required fields are included in the `fields` parameter of `search_read` calls
- Check field names against the Odoo model structure
- Use the `get_fields` method to verify field availability
- Add field existence checks in your code

## Diagnosing MCP Context Issues

If you suspect context handling issues, you can add diagnostic logging:

```python
@mcp.tool()
async def diagnostic_tool(ctx: Context) -> Dict[str, Any]:
    """Tool for diagnosing context issues."""
    result = {
        "ctx_type": str(type(ctx)),
        "has_request_context": hasattr(ctx, "request_context"),
    }
    
    if hasattr(ctx, "request_context"):
        result["request_context_type"] = str(type(ctx.request_context))
        result["has_lifespan_context"] = hasattr(ctx.request_context, "lifespan_context")
        
        if hasattr(ctx.request_context, "lifespan_context"):
            lifespan = ctx.request_context.lifespan_context
            result["lifespan_context_type"] = str(type(lifespan))
            
            if isinstance(lifespan, dict):
                result["lifespan_keys"] = list(lifespan.keys())
                if "odoo_client" in lifespan:
                    result["odoo_client_type"] = str(type(lifespan["odoo_client"]))
            else:
                result["has_odoo_client"] = hasattr(lifespan, "odoo_client")
                if hasattr(lifespan, "odoo_client"):
                    result["odoo_client_exists"] = lifespan.odoo_client is not None
    
    return result
```

## Testing Tools Independently

To help identify which tools are working correctly and which have issues, you can create a simple test script:

```python
import asyncio
from mcp.client.fastmcp import Client, stdio_streams

async def test_tools():
    # Connect to MCP-Odoo server
    read_stream, write_stream = stdio_streams()
    async with Client(read_stream, write_stream) as client:
        await client.initialize()
        
        # Get list of available tools
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools")
        
        # Test each tool with basic parameters
        for tool in tools:
            try:
                print(f"\nTesting tool: {tool.name}")
                # Call with minimal parameters
                params = {}
                # Add required parameters if any
                for param in tool.parameters:
                    if param.required:
                        # Add a default value based on type
                        if param.type == "integer":
                            params[param.name] = 10
                        elif param.type == "string":
                            params[param.name] = "test"
                        # Add other types as needed
                
                result = await client.call_tool(tool.name, params)
                print(f"Success! Result type: {type(result)}")
            except Exception as e:
                print(f"Failed: {str(e)}")
        
        print("\nTest completed")

if __name__ == "__main__":
    asyncio.run(test_tools())
```

## Advanced Troubleshooting

### Analyzing MCP Communication

For deeper issues, you can enable debug logging to see the actual MCP messages being exchanged:

```bash
python -m mcp_odoo_public --transport stdio --log-level DEBUG
```

This will show the JSON-RPC messages being sent and received, which can help identify where communication is breaking down.

### Debugging Lifespan Issues

If you suspect the lifespan context isn't being properly initialized or passed, you can modify the `app_lifespan` function to include more detailed logging:

```python
@asynccontextmanager
async def app_lifespan() -> AsyncGenerator[AppContext, None]:
    """Lifespan context manager for MCP-Odoo"""
    logger.info("Initializing MCP-Odoo lifespan...")
    
    # Get configuration
    config_data = config.as_dict()
    logger.debug(f"Configuration loaded: {list(config_data.keys())}")
    
    odoo_config = config_data.get("odoo", {})
    logger.debug(f"Odoo config keys: {list(odoo_config.keys())}")
    
    # Create Odoo client
    client = OdooClient(
        url=odoo_config.get("host"),
        database=odoo_config.get("database"),
        username=odoo_config.get("username"),
        password="[REDACTED]"  # Don't log passwords
    )
    logger.debug(f"OdooClient created: {client}")

    # Connect to Odoo
    try:
        await client.connect()
        logger.info(f"Connected to Odoo as {client.username} (uid: {client.uid})")
        
        # Create app context
        app_ctx = AppContext(
            odoo_client=client,
            config=config_data
        )
        
        # Log details about what we're returning
        logger.debug(f"AppContext created: {id(app_ctx)}")
        logger.debug(f"AppContext has odoo_client: {hasattr(app_ctx, 'odoo_client')}")
        
        # Yield context to FastMCP
        yield app_ctx
    except Exception as e:
        logger.error(f"Error in lifespan: {str(e)}", exc_info=True)
        # Re-raise to ensure FastMCP knows there was a problem
        raise
    finally:
        # Disconnect from Odoo
        if client.is_connected:
            await client.disconnect()
            logger.info("Disconnected from Odoo")
```

## Performance Optimization

If your MCP-Odoo connector is working but running slowly, consider these optimizations:

1. **Query Optimization**:
   - Request only needed fields: `fields=['id', 'name']` instead of all fields
   - Use appropriate limits: `limit=100` instead of fetching all records
   - Add specific domain filters to reduce result sets

2. **Connection Pooling**:
   - The connector reuses the same Odoo client for multiple operations
   - Ensure your `OdooClient` implementation properly manages connection state

3. **Caching**:
   - Consider adding a caching layer for frequently accessed, rarely changing data
   - Simple implementation can use an in-memory dictionary with TTL

4. **Parallel Processing**:
   - For complex operations, consider using `asyncio.gather()` to run multiple Odoo queries in parallel

## Conclusion

The context handling issues in MCP 1.6.0 can be challenging, but the MCP-Odoo connector implements a robust solution through:

1. Type checking and recovery logic
2. Consistent tool implementations
3. Centralized context handling
4. Fallback mechanisms for reconnection

By following the guidelines in this troubleshooting guide, you should be able to diagnose and resolve most common issues with the MCP-Odoo connector. 