# Integrating MCP-Odoo with AI Agents

This guide demonstrates how to integrate the MCP-Odoo server with AI agents using LangGraph and popular LLM providers like OpenAI and Anthropic.

## Prerequisites

Before starting, make sure you have the following:

1. MCP-Odoo server running (see the [basic usage guide](basic_usage.md))
2. An API key for OpenAI or Anthropic
3. Required Python packages:
   - langchain
   - langchain-mcp-adapters
   - langgraph
   - python-dotenv (optional, for loading environment variables)

```bash
pip install langchain langchain-mcp-adapters langgraph python-dotenv
```

## Setting Up Environment Variables

Create a `.env` file in your project root with your API keys and MCP server URL:

```
# LLM API Keys - You only need one of these
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# MCP Server URL
MCP_SERVER_URL=http://localhost:8080
```

## Basic Integration Example

Here's a simple example showing how to connect to the MCP-Odoo server and create an AI agent that can query Odoo data:

```python
import os
import asyncio
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

async def main():
    # Set up the MCP client with server configuration
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8080")
    mcp_servers = {
        "odoo": {
            "url": f"{mcp_server_url}/sse",
            "transport": "sse",
        }
    }
    
    print(f"Connecting to MCP-Odoo server at {mcp_server_url}...")
    
    # Create the MCP client
    async with MultiServerMCPClient(mcp_servers) as client:
        # Get available tools from the MCP server
        tools = client.get_tools()
        print(f"Available MCP tools: {[t.name for t in tools]}")
        
        # Select the model to use (OpenAI or Anthropic)
        if os.environ.get("ANTHROPIC_API_KEY"):
            model_name = "anthropic:claude-3-sonnet-20240229"
            print(f"Using Anthropic model: {model_name}")
        elif os.environ.get("OPENAI_API_KEY"):
            model_name = "openai:gpt-4"
            print(f"Using OpenAI model: {model_name}")
        else:
            raise ValueError("No API key found for OpenAI or Anthropic")
        
        # Create the LangGraph agent
        agent = create_react_agent(
            model_name,
            tools
        )
        
        # Run a query
        query = "What version of Odoo are we connected to?"
        print(f"Sending query: '{query}'")
        
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]}
        )
        
        # Process and display the response
        if isinstance(response, dict) and "messages" in response:
            for message in response["messages"]:
                if hasattr(message, 'content'):
                    print(f"Response: {message.content}")
                else:
                    print(f"Response: {message}")
        else:
            print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Advanced Example: Multi-Step Financial Analysis

This example shows how to create an agent that performs a multi-step financial analysis using Odoo accounting data:

```python
import os
import asyncio
import datetime
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

async def run_accounting_analysis():
    # Set up MCP client
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8080")
    mcp_servers = {
        "odoo": {
            "url": f"{mcp_server_url}/sse",
            "transport": "sse",
        }
    }
    
    # Create the MCP client
    async with MultiServerMCPClient(mcp_servers) as client:
        # Get available tools
        tools = client.get_tools()
        
        # Select model
        if os.environ.get("OPENAI_API_KEY"):
            model_name = "openai:gpt-4"
        elif os.environ.get("ANTHROPIC_API_KEY"):
            model_name = "anthropic:claude-3-sonnet-20240229"
        else:
            raise ValueError("No API key found for OpenAI or Anthropic")
        
        # Create system prompt for specialized accounting analysis
        today = datetime.datetime.now()
        first_day_last_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
        date_from = first_day_last_month.strftime("%Y-%m-%d")
        
        system_prompt = f"""You are a financial accounting expert specializing in Odoo ERP systems.
Your task is to analyze the accounting data for the period from {date_from} to today.

Follow these steps:
1. First, get the Odoo version to confirm connection
2. Check recent vendor bills (list_vendor_bills)
3. Examine payment reconciliation (reconcile_invoices_and_payments)
4. Analyze account flows between bank accounts (572) and vendor accounts (400)
5. Provide insights and recommendations based on your findings

Focus on identifying:
- Unpaid vendor bills that need attention
- Payment patterns and reconciliation status
- Potential accounting issues or anomalies
"""
        
        # Create the specialized agent
        agent = create_react_agent(
            model_name,
            tools,
            prompt=system_prompt
        )
        
        # Run the analysis query
        query = f"Perform a comprehensive financial analysis of our Odoo data from {date_from} to today. Focus on vendor payments, reconciliation status, and provide actionable recommendations."
        
        print(f"Starting financial analysis from {date_from} to today...")
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]}
        )
        
        # Process and display the response
        if isinstance(response, dict) and "messages" in response:
            for message in response["messages"]:
                if hasattr(message, 'content'):
                    print(f"Analysis: {message.content}")
                else:
                    print(f"Analysis: {message}")
        else:
            print(f"Analysis: {response}")

if __name__ == "__main__":
    asyncio.run(run_accounting_analysis())
```

## Handling Responses

LangGraph agents can return responses in different formats. Here's a utility function to handle various response formats:

```python
def extract_message_content(message):
    """Extracts content from different message formats"""
    if hasattr(message, 'content'):
        return message.content
    elif isinstance(message, dict) and 'content' in message:
        return message['content']
    elif isinstance(message, dict) and 'role' in message and 'content' in message:
        return message['content']
    elif isinstance(message, str):
        return message
    else:
        return str(message)

# Usage example:
response = await agent.ainvoke({"messages": [HumanMessage(content=query)]})
if isinstance(response, dict) and "messages" in response:
    for message in response["messages"]:
        print(extract_message_content(message))
elif isinstance(response, list):
    for message in response:
        print(extract_message_content(message))
else:
    print(extract_message_content(response))
```

## Available MCP-Odoo Tools

The MCP-Odoo server provides several tools that your AI agent can use:

1. `odoo_version` - Get the Odoo server version
2. `list_vendor_bills` - List vendor bills with filtering options
3. `list_customer_invoices` - List customer invoices
4. `list_payments` - List payments
5. `get_invoice_details` - Get detailed information about a specific invoice
6. `reconcile_invoices_and_payments` - Generate a reconciliation report
7. `list_accounting_entries` - Get journal entries for accounting analysis
8. `list_suppliers` - List suppliers with optional filtering
9. `list_customers` - List customers with optional filtering
10. `find_entries_by_account` - Find accounting entries related to a specific account
11. `trace_account_flow` - Trace money flow between different account types

## Tips for Effective Integration

1. **Customize the system prompt** to give the AI agent specific instructions about accounting concepts and Odoo.
2. **Break down complex tasks** into smaller, sequential steps for the agent to follow.
3. **Include error handling** to manage potential issues with Odoo connectivity or data retrieval.
4. **Add date filtering** to limit the scope of accounting queries for better performance.
5. **Use specialized agents** for different accounting tasks (reconciliation, analysis, etc.).

## Further Reading

- [LangGraph Documentation](https://python.langchain.com/docs/expression_language/langgraph)
- [Langchain MCP Adapters](https://github.com/langchain-ai/langchain-mcp-adapters)
- [MCP-Odoo Implementation Guide](../implementation_guide.md)
- [MCP-Odoo Accounting Guide](../accounting_guide.md) 