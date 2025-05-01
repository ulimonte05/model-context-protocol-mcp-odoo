# Accounting Functionality Guide

This guide explains in detail how MCP-Odoo handles accounting data from Odoo, particularly focusing on invoices, payments, and reconciliation.

## Accounting Data Models

MCP-Odoo interacts with several key Odoo accounting models:

1. **account.move** - The central model for accounting entries, including:
   - Vendor bills (move_type = 'in_invoice')
   - Customer invoices (move_type = 'out_invoice')
   - Journal entries (move_type = 'entry')
   - Credit notes (move_type = 'in_refund' or 'out_refund')

2. **account.payment** - Represents money transfers:
   - Outbound payments (to vendors)
   - Inbound payments (from customers)

3. **account.move.line** - Individual line items within accounting entries:
   - Debit/credit amounts
   - Account associations
   - Reconciliation status

## Accounting Operations

### Vendor Bills Management

Vendor bills represent invoices received from suppliers. The MCP-Odoo connector allows agents to:

1. **List vendor bills**:
   ```python
   @mcp.tool()
   async def list_vendor_bills(ctx: Context, limit: int = 20, offset: int = 0, 
                               paid: Optional[bool] = None) -> List[Dict[str, Any]]:
       """
       List vendor bills (supplier invoices).
       
       Args:
           limit: Maximum number of records to return
           offset: Number of records to skip (for pagination)
           paid: Filter by payment status (True=paid, False=unpaid, None=all)
       
       Returns:
           List of vendor bills with their details
       """
       # Implementation details...
   ```

2. **Get vendor bill details**:
   ```python
   @mcp.tool()
   async def get_invoice_details(ctx: Context, invoice_id: int) -> Dict[str, Any]:
       """
       Get detailed information about a specific invoice.
       
       Args:
           invoice_id: ID of the invoice to retrieve
           
       Returns:
           Detailed invoice information including lines, taxes, and payment info
       """
       # Implementation details...
   ```

### Customer Invoices Management

Customer invoices represent bills sent to clients. The connector provides similar functionality:

1. **List customer invoices**:
   ```python
   @mcp.tool()
   async def list_customer_invoices(ctx: Context, limit: int = 20, offset: int = 0,
                                    paid: Optional[bool] = None) -> List[Dict[str, Any]]:
       """
       List customer invoices.
       
       Args:
           limit: Maximum number of records to return
           offset: Number of records to skip (for pagination)
           paid: Filter by payment status (True=paid, False=unpaid, None=all)
       
       Returns:
           List of customer invoices with their details
       """
       # Implementation details...
   ```

### Payments Management

The connector provides tools to access payment records:

```python
@mcp.tool()
async def list_payments(ctx: Context, limit: int = 20, payment_type: Optional[str] = None,
                        partner_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    List payment records.
    
    Args:
        limit: Maximum number of records to return
        payment_type: Filter by payment type ('inbound' or 'outbound')
        partner_id: Filter by partner (customer/vendor) ID
    
    Returns:
        List of payment records with their details
    """
    # Implementation details...
```

## Reconciliation Logic

Reconciliation is the process of matching payments with invoices. In accounting terms, it ensures that:

1. Each payment is applied to the correct invoice(s)
2. Each invoice's payment status is accurately tracked
3. The accounts balance properly according to double-entry accounting principles

### Double-Entry Accounting Principles

Odoo follows double-entry accounting, where:

- Every transaction affects at least two accounts
- The sum of debits equals the sum of credits for each transaction
- Account types determine whether debits increase or decrease the account balance

For example, a typical vendor bill creates:
- A debit in an expense account (increasing expenses)
- A credit in accounts payable (increasing liabilities)

When paid, this creates:
- A debit in accounts payable (decreasing liabilities)
- A credit in a bank account (decreasing assets)

### Reconciliation Tool

The connector provides a specialized tool for matching invoices with payments:

```python
@mcp.tool()
async def reconcile_invoices_and_payments(
    ctx: Context, 
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    partner_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Analyze and match invoices with their corresponding payments.
    
    Args:
        date_from: Start date for analysis (YYYY-MM-DD)
        date_to: End date for analysis (YYYY-MM-DD)
        partner_id: Limit analysis to a specific partner
        
    Returns:
        Reconciliation report with matched and unmatched items
    """
    # Implementation accessing Odoo reconciliation data
```

This tool performs several steps:

1. Retrieves all relevant invoices in the date range
2. Retrieves all relevant payments in the date range
3. For each invoice:
   - Checks its payment status directly from Odoo
   - If paid, identifies which payment(s) were applied to it
   - If partially paid, identifies the paid amount and remaining balance
4. Builds a structured report of matches and unmatched items

### Example Reconciliation Result

The reconciliation tool returns structured data that looks like this:

```json
{
  "reconciled_items": [
    {
      "invoice": {
        "id": 123,
        "number": "BILL/2023/001",
        "partner_id": [42, "Vendor Name"],
        "date": "2023-01-15",
        "amount_total": 1000.00,
        "payment_state": "paid"
      },
      "payments": [
        {
          "id": 456,
          "name": "PAYMENT/2023/001",
          "date": "2023-01-30",
          "amount": 1000.00
        }
      ]
    }
  ],
  "partially_reconciled_items": [
    {
      "invoice": {
        "id": 124,
        "number": "BILL/2023/002",
        "partner_id": [42, "Vendor Name"],
        "date": "2023-02-15",
        "amount_total": 1500.00,
        "payment_state": "partial"
      },
      "payments": [
        {
          "id": 457,
          "name": "PAYMENT/2023/002",
          "date": "2023-02-28",
          "amount": 750.00
        }
      ],
      "remaining_amount": 750.00
    }
  ],
  "unreconciled_invoices": [
    {
      "id": 125,
      "number": "BILL/2023/003",
      "partner_id": [43, "Another Vendor"],
      "date": "2023-03-15",
      "amount_total": 800.00,
      "payment_state": "not_paid"
    }
  ],
  "unmatched_payments": [
    {
      "id": 458,
      "name": "PAYMENT/2023/003",
      "partner_id": [44, "Third Vendor"],
      "date": "2023-03-30",
      "amount": 500.00,
      "invoice_ids": []
    }
  ],
  "summary": {
    "total_invoices": 3,
    "total_payments": 3,
    "fully_reconciled": 1,
    "partially_reconciled": 1,
    "unreconciled": 1
  }
}
```

## Accounting Entry Analysis

For deeper analysis, MCP-Odoo provides tools to examine journal entries:

```python
@mcp.tool()
async def list_accounting_entries(
    ctx: Context,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    journal_id: Optional[int] = None,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    List accounting entries (journal entries).
    
    Args:
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        journal_id: Filter by specific journal
        limit: Maximum number of records to return
        
    Returns:
        List of accounting entries
    """
    # Implementation accesses account.move with move_type = 'entry'
```

To get the detailed lines within an entry:

```python
@mcp.tool()
async def get_account_move_lines(ctx: Context, move_id: int) -> List[Dict[str, Any]]:
    """
    Get the detail lines of an accounting entry.
    
    Args:
        move_id: ID of the account move/entry
        
    Returns:
        List of account move lines with debit/credit details
    """
    # Implementation accesses account.move.line
```

## Categorizing Financial Movements

The connector helps categorize financial movements into meaningful groups:

1. **Vendor Payments**: Outflows to suppliers
   - Identified by payment_type = 'outbound' and partner_type = 'supplier'
   - Typically involves accounts payable (e.g., 400x accounts in Spain's PGC)

2. **Customer Receipts**: Inflows from customers
   - Identified by payment_type = 'inbound' and partner_type = 'customer'
   - Typically involves accounts receivable (e.g., 430x accounts in Spain's PGC)

3. **Tax Payments**: Payments to tax authorities
   - Identified by partner being a tax authority
   - Or by involving tax accounts (e.g., 47x accounts in Spain's PGC)

4. **Other Movements**: Miscellaneous accounting entries
   - Internal transfers, provisions, depreciation, etc.
   - Identified by journal type or specific accounts

## Implementation Notes

1. **Payment Status Logic**: The connector relies on Odoo's payment_state field:
   - 'not_paid': Invoice has not been paid
   - 'in_payment': Payment has been registered but not reconciled
   - 'partial': Invoice has been partially paid
   - 'paid': Invoice has been fully paid
   - 'reversed': Invoice has been reversed (e.g., by a credit note)

2. **Reconciliation Detection**: The connector can determine reconciliation status in several ways:
   - Using the invoice's payment_state field
   - Checking the reconciled field on account.move.line
   - Examining partial reconciliations in account.partial.reconcile
   - Looking at payment records linked to invoices

3. **Performance Considerations**:
   - For large datasets, the connector uses pagination (limit/offset)
   - It requests only necessary fields to reduce data transfer
   - Specific date ranges can be used to limit the scope

## Example Accounting Workflows

### Example 1: Analyzing Unpaid Vendor Bills

```python
# Step 1: Get list of unpaid vendor bills
unpaid_bills = await list_vendor_bills(ctx, paid=False, limit=100)

# Step 2: Analyze by vendor
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

# Step 3: Generate report of vendors with highest outstanding amounts
sorted_vendors = sorted(vendor_totals.values(), key=lambda x: x['total'], reverse=True)
```

### Example 2: Reconciliation Analysis for a Specific Vendor

```python
# Step 1: Get vendor ID
vendor_id = 42  # Example vendor ID

# Step 2: Perform reconciliation analysis
reconciliation = await reconcile_invoices_and_payments(ctx, partner_id=vendor_id)

# Step 3: Calculate payment efficiency
if reconciliation['fully_reconciled'] + reconciliation['partially_reconciled'] > 0:
    payment_efficiency = reconciliation['fully_reconciled'] / (
        reconciliation['fully_reconciled'] + reconciliation['partially_reconciled']
    ) * 100
else:
    payment_efficiency = 0

# Step 4: Identify old unpaid invoices
current_date = datetime.now()
old_unpaid = [
    inv for inv in reconciliation['unreconciled_invoices']
    if (current_date - datetime.strptime(inv['date'], '%Y-%m-%d')).days > 60
]
```

## Conclusion

The accounting functionality in MCP-Odoo provides AI agents with powerful tools to analyze financial data from Odoo. By exposing invoices, payments, and reconciliation information through the Model Context Protocol, the connector enables sophisticated financial analysis and reporting in natural language conversations.

This approach respects Odoo's double-entry accounting principles while making the data accessible through a standardized interface that AI agents can easily understand and utilize. 