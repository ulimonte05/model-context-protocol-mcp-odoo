# Basic Usage Example

This guide demonstrates how to use the MCP-Odoo connector with an AI agent to perform accounting data analysis.

## Setting Up

First, ensure you have configured the MCP-Odoo connector with your Odoo credentials:

```
# .env file
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
HOST=0.0.0.0
PORT=8080
```

## Starting the Server

Run the MCP-Odoo server using:

```bash
# Using the SSE transport (for remote HTTP clients)
python -m mcp_odoo_public

# Or using stdio for local agents
python -m mcp_odoo_public --transport stdio
```

## Connecting an Agent

### Using Python MCP Client

This example shows how to use the Python MCP client to connect to the server and execute tools:

```python
import asyncio
from mcp.client.fastmcp import Client, stdio_streams

async def main():
    # Connect to the MCP-Odoo server (assuming stdio transport)
    read_stream, write_stream = stdio_streams()
    async with Client(read_stream, write_stream) as client:
        # Initialize the client
        await client.initialize()
        
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")
        
        # Check Odoo connection
        odoo_version = await client.call_tool("odoo_version", {})
        print(f"Odoo version: {odoo_version}")
        
        # List some vendor bills
        bills = await client.call_tool("list_vendor_bills", {"limit": 5})
        print(f"Found {len(bills)} vendor bills")
        
        # Show details of the first bill
        if bills:
            bill_id = bills[0]["id"]
            bill_details = await client.call_tool("get_invoice_details", {"invoice_id": bill_id})
            print(f"Bill details: {bill_details['name']} - {bill_details['amount_total']}")
            
            # Get payments for this bill
            payments = await client.call_tool("list_payments", {"limit": 10})
            
            # Analyze reconciliation
            reconciliation = await client.call_tool(
                "reconcile_invoices_and_payments", 
                {"partner_id": bills[0]["partner_id"][0]}
            )
            
            print(f"Reconciliation summary: {reconciliation['summary']}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Using SSE for Web Integration

For web applications, you can use the SSE transport:

```javascript
// Example JavaScript code to connect to MCP-Odoo via SSE
const serverUrl = 'http://localhost:8080';

// Connect to the SSE stream
const eventSource = new EventSource(`${serverUrl}/sse`);

// Handle incoming messages
eventSource.onmessage = function(event) {
    const message = JSON.parse(event.data);
    console.log('Received message:', message);
    
    // Handle different message types
    if (message.type === 'tool_result') {
        processToolResult(message.tool_name, message.result);
    }
};

// Function to call MCP tools
async function callTool(toolName, params = {}) {
    const response = await fetch(`${serverUrl}/messages`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'call_tool',
            tool_name: toolName,
            params: params
        }),
    });
    
    return response.json();
}

// Example: List vendor bills
async function listVendorBills() {
    const result = await callTool('list_vendor_bills', { limit: 10 });
    console.log('Vendor bills:', result);
    return result;
}

// Process tool results
function processToolResult(toolName, result) {
    console.log(`Result from ${toolName}:`, result);
    // Process and display the result in the UI
}
```

## Using with Claude or GPT Agents

When using with Claude or GPT agents, you need to:

1. Start the MCP-Odoo server with the SSE transport
2. Create a proxy that forwards agent requests to MCP
3. Structure your agent prompts to use the available tools

Example agent prompt:

```
You are an accounting assistant with access to Odoo data through the MCP-Odoo connector.

Available tools include:
- odoo_version: Get Odoo server version
- list_vendor_bills: List vendor bills
- list_customer_invoices: List customer invoices 
- list_payments: List payment records
- get_invoice_details: Get detailed invoice information
- reconcile_invoices_and_payments: Match invoices with payments

Please analyze the vendor bills and their payment status.
```

## Example Scenarios

### 1. Analyzing Unpaid Invoices

```python
# Get unpaid vendor bills
unpaid_bills = await client.call_tool("list_vendor_bills", {"paid": False, "limit": 100})

# Group by vendor
vendor_totals = {}
for bill in unpaid_bills:
    vendor_id = bill['partner_id'][0]
    vendor_name = bill['partner_id'][1]
    if vendor_id not in vendor_totals:
        vendor_totals[vendor_id] = {
            'name': vendor_name,
            'total': 0,
            'bills': []
        }
    vendor_totals[vendor_id]['total'] += bill['amount_total']
    vendor_totals[vendor_id]['bills'].append(bill)

# Print vendors sorted by amount
for vendor_id, data in sorted(vendor_totals.items(), key=lambda x: x[1]['total'], reverse=True):
    print(f"{data['name']}: {data['total']:.2f} ({len(data['bills'])} bills)")
```

### 2. Performing Reconciliation Analysis

```python
# Define time period
from datetime import datetime, timedelta
end_date = datetime.now().strftime('%Y-%m-%d')
start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')

# Perform reconciliation analysis
reconciliation = await client.call_tool(
    "reconcile_invoices_and_payments",
    {
        "date_from": start_date,
        "date_to": end_date
    }
)

# Analyze results
print(f"Summary: {reconciliation['summary']}")
print(f"Fully reconciled: {len(reconciliation['reconciled_items'])}")
print(f"Partially reconciled: {len(reconciliation['partially_reconciled_items'])}")
print(f"Unreconciled invoices: {len(reconciliation['unreconciled_invoices'])}")

# Check for old unreconciled invoices (more than 60 days)
old_threshold = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
old_unpaid = [
    inv for inv in reconciliation['unreconciled_invoices']
    if inv['date'] < old_threshold
]

print(f"Old unpaid invoices (>60 days): {len(old_unpaid)}")
for inv in old_unpaid:
    print(f"  {inv['number']} - {inv['partner_id'][1]} - {inv['amount_total']:.2f}")
```

### 3. Analyzing Payment Efficiency

```python
# Get all vendors
vendors = await client.call_tool("list_suppliers", {"limit": 100})

# Analyze payment efficiency for each vendor
results = []
for vendor in vendors:
    # Get reconciliation data for this vendor
    reconciliation = await client.call_tool(
        "reconcile_invoices_and_payments",
        {"partner_id": vendor['id']}
    )
    
    # Calculate metrics
    total_invoices = (
        len(reconciliation['reconciled_items']) + 
        len(reconciliation['partially_reconciled_items']) +
        len(reconciliation['unreconciled_invoices'])
    )
    
    if total_invoices > 0:
        full_payment_rate = len(reconciliation['reconciled_items']) / total_invoices
        has_partial = len(reconciliation['partially_reconciled_items']) > 0
        
        # Collect results
        results.append({
            'vendor_name': vendor['name'],
            'total_invoices': total_invoices,
            'fully_paid': len(reconciliation['reconciled_items']),
            'partially_paid': len(reconciliation['partially_reconciled_items']),
            'unpaid': len(reconciliation['unreconciled_invoices']),
            'payment_rate': full_payment_rate
        })

# Sort by payment rate
results.sort(key=lambda x: x['payment_rate'])

# Print results
print("Vendor Payment Efficiency (worst to best):")
for r in results:
    print(f"{r['vendor_name']}: {r['payment_rate']*100:.1f}% fully paid " +
          f"({r['fully_paid']}/{r['total_invoices']} invoices)")
```

## Next Steps: AI Agent Integration

For integrating MCP-Odoo with AI agents (LLMs) using frameworks like LangGraph, see our dedicated guides:

- [AI Agent Integration](ai_agent_integration.md) - Comprehensive guide to connecting MCP-Odoo with LLMs
- [Simple Odoo Agent](simple_odoo_agent.py) - Interactive Python script for testing MCP-Odoo with AI agents

These examples demonstrate how to combine the power of Odoo's data with modern AI capabilities for enhanced financial analysis and reporting. 