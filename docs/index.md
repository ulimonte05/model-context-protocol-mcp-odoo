# MCP-Odoo Documentation

Welcome to the MCP-Odoo documentation. This guide will help you understand, implement, and extend the MCP-Odoo connector, which provides a bridge between Odoo ERP systems and AI agents using the Model Context Protocol.

## Overview

MCP-Odoo enables AI agents to access and manipulate Odoo data through a standardized interface. It exposes accounting data, partner information, and other Odoo resources to AI agents via the Model Context Protocol, allowing conversational and automated interaction with ERP data.

## Documentation Index

### Core Concepts

- [Implementation Guide](implementation_guide.md) - Comprehensive guide to the MCP-Odoo architecture and implementation
- [Accounting Functionality](accounting_guide.md) - Detailed explanation of accounting features and reconciliation
- [Troubleshooting Guide](troubleshooting.md) - Solutions for common issues and advanced debugging

### Examples and Tutorials

- [Basic Usage](examples/basic_usage.md) - Getting started with the MCP-Odoo connector

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourtechtribe/mcp-odoo.git
cd mcp-odoo

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the project root with your Odoo credentials:

```
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=your_username
ODOO_PASSWORD=your_password
HOST=0.0.0.0
PORT=8080
```

### Running the Server

```bash
# Using the SSE transport (default)
python -m mcp_odoo_public

# Using stdio for local agent integration
python -m mcp_odoo_public --transport stdio
```

## Project Structure

- `mcp_odoo_public/`: Main package
  - `odoo/`: Odoo client implementation
  - `resources/`: MCP tools and resources
  - `server.py`: MCP server implementation
  - `config.py`: Configuration management
  - `mcp_instance.py`: FastMCP instance definition
  - `context_handler.py`: Context handling utilities

## Core Features

- 🔌 Seamless connection to Odoo instances
- 🤖 Standardized MCP interface for AI agent compatibility
- 📊 Rich accounting data access and analysis
- 🔄 Reconciliation of invoices and payments
- 🔍 Partner information management

## Contributing

Contributions to MCP-Odoo are welcome! Please see our [Contributing Guide](../CONTRIBUTING.md) for details on how to submit pull requests, report issues, and suggest improvements.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details. 