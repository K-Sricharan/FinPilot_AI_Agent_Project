# Budget Analysis Agent

AI-powered financial assistant that reads bank statements, credit card statements, invoices, and expense reports, categorizes transactions using an LLM, stores them in SQLite, and answers financial questions through natural language. The project uses the Model Context Protocol (MCP) to separate AI reasoning from file and database operations.

## Architecture

```
User
   │
   ▼
Budget Analysis Agent (agent.py)
   ├── Filesystem MCP (mcp_servers/filesystem_server.py)
   │      Reads PDF, CSV, XLSX, XLS financial documents
   └── SQLite MCP (mcp_servers/sqlite_server.py)
          Stores transactions and performs financial analysis
```

The language model never accesses files or executes SQL directly. All external operations are handled securely through MCP servers, while the model focuses on categorization, trend analysis, reasoning, and financial recommendations.

---

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file and add your NVIDIA API key:

```env
NVIDIA_API_KEY=YOUR_API_KEY
```

---

## Sample Dataset

The `documents/` directory contains sample financial data for testing.

| File | Format | Description |
|------|--------|-------------|
| HDFC_April.csv | CSV | April bank transactions |
| HDFC_May.csv | CSV | May bank transactions |
| ICICI_June.csv | CSV | June transactions from another bank |
| Expenses_June.xlsx | Excel | Additional monthly expenses |
| HDFC_July_Statement.pdf | PDF | Sample bank statement |

The sample data includes recurring merchants such as Netflix, Spotify, Airtel Broadband, rent, and salary credits, making it suitable for testing recurring expense detection, spending analysis, and month-over-month comparisons.

---

## Run

Start the Streamlit application:

```bash
streamlit run app.py
```

---

## Example Queries

- Analyze my June expenses
- Compare June spending with May
- How much did I spend on groceries?
- Which subscriptions are recurring?
- Read my July bank statement
- Show my monthly spending trend
- What is my largest expense category?
- Where can I reduce my expenses?

---

## Technology Stack

- Python
- Streamlit
- NVIDIA NIM / OpenAI Compatible API
- Model Context Protocol (MCP)
- SQLite
- Pandas
- pdfplumber
- OpenPyXL

---

## Notes

- Transaction categorization is performed entirely by the language model without hardcoded merchant mappings.
- Filesystem MCP handles document parsing, while SQLite MCP manages all database operations.
- Supports PDF, CSV, XLSX, and XLS financial documents.
- The SQLite database is automatically created on first use.
- The MCP servers are independent and can be integrated with other MCP-compatible clients.

---


