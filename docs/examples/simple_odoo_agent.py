#!/usr/bin/env python3
"""
Simple MCP-Odoo + LLM Agent Integration Example

This script demonstrates how to create a basic AI agent that connects to 
the MCP-Odoo server and performs accounting queries.

Usage:
  python simple_odoo_agent.py

Required environment variables:
  - OPENAI_API_KEY or ANTHROPIC_API_KEY: Your API key for the LLM provider
  - MCP_SERVER_URL: URL of your MCP-Odoo server (default: http://localhost:8080)
"""
import os
import asyncio
import sys
from datetime import datetime

try:
    from dotenv import load_dotenv
    # Load environment variables from .env file if it exists
    load_dotenv()
except ImportError:
    print("python-dotenv not installed. Continuing with existing environment variables.")

try:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langgraph.prebuilt import create_react_agent
    from langchain_core.messages import HumanMessage
except ImportError:
    print("Required packages not installed. Please install them with:")
    print("pip install langchain-mcp-adapters langgraph")
    sys.exit(1)

async def run_odoo_agent():
    """Run a simple AI agent that connects to MCP-Odoo"""
    # Check for API keys
    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: No API key found for LLM providers.")
        print("Please set either OPENAI_API_KEY or ANTHROPIC_API_KEY in your environment or .env file.")
        return

    # Setup MCP client
    mcp_server_url = os.environ.get("MCP_SERVER_URL", "http://localhost:8080")
    mcp_servers = {
        "odoo": {
            "url": f"{mcp_server_url}/sse",
            "transport": "sse",
        }
    }
    
    print(f"Connecting to MCP-Odoo server at {mcp_server_url}...")
    
    try:
        # Create the MCP client and connect
        async with MultiServerMCPClient(mcp_servers) as client:
            # Get tools from the MCP server
            tools = client.get_tools()
            print(f"Available MCP tools: {[t.name for t in tools]}")
            
            # Select model based on available API keys
            if os.environ.get("ANTHROPIC_API_KEY"):
                model_name = "anthropic:claude-3-sonnet-20240229"
                print(f"Using Anthropic model: {model_name}")
            else:
                model_name = "openai:gpt-4"
                print(f"Using OpenAI model: {model_name}")
            
            # Create the agent
            agent = create_react_agent(
                model_name,
                tools
            )
            
            # Display main menu
            while True:
                print("\n=== MCP-Odoo Agent Demo ===")
                print("1. Get Odoo version")
                print("2. List recent vendor bills")
                print("3. Analyze invoice reconciliation")
                print("4. Custom query")
                print("0. Exit")
                
                choice = input("\nSelect an option (0-4): ")
                
                if choice == "0":
                    print("Exiting...")
                    break
                
                # Process the choice
                query = ""
                if choice == "1":
                    query = "What version of Odoo are we connected to?"
                elif choice == "2":
                    query = "List the 3 most recent vendor bills. Include their payment status."
                elif choice == "3":
                    today = datetime.now()
                    last_month = (today.replace(day=1) - datetime.timedelta(days=1)).replace(day=1)
                    date_from = last_month.strftime("%Y-%m-%d")
                    query = f"Analyze payment reconciliation status from {date_from} to today. What invoices are unpaid?"
                elif choice == "4":
                    query = input("Enter your custom query: ")
                else:
                    print("Invalid choice, please try again.")
                    continue
                
                # Run the query through the agent
                if query:
                    print(f"\nSending query: '{query}'")
                    print("Waiting for response (this may take a moment)...\n")
                    
                    try:
                        # Invoke the agent with the query
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
                    except Exception as e:
                        print(f"Error during agent execution: {str(e)}")
                
                # Wait for user to continue
                input("\nPress Enter to continue...")
    
    except Exception as e:
        print(f"Error connecting to MCP-Odoo server: {str(e)}")

if __name__ == "__main__":
    try:
        asyncio.run(run_odoo_agent())
    except KeyboardInterrupt:
        print("\nProcess interrupted by user. Exiting...")
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}") 