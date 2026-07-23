# Agent_Documentation

## 1. Definitions and Glossary

This section establishes formal definitions for technical acronyms, architectural terms, and core domain concepts referenced throughout this documentation.

### Model Context Protocol (MCP)
An open specification and architectural standard designed to establish secure, standardized inter-process communication between artificial intelligence models and localized execution environments. MCP abstracts external data sources, database drivers, and filesystem routines into exposed server tools invoked by client orchestrators via JSON-RPC payloads over standard input/output streams.

### FastMCP
An implementation framework in Python that streamlines the creation of Model Context Protocol compliant servers. It automates API route generation, tool definition metadata serialization, input schema validation, and transport stream binding.

### Large Language Model (LLM)
A high-parameter neural network trained on vast text corpora to perform zero-shot and few-shot reasoning, semantic categorization, unstructured text parsing, and natural language synthesis. Within this system, the LLM functions as an autonomous reasoning engine that orchestrates tool calls without maintaining direct database connection pools or file handles.

### Inter-Process Communication (IPC) via Standard I/O (stdio)
A lightweight networking channel wherein a parent process initializes subprocesses and communicates through redirected standard input (`stdin`) and standard output (`stdout`) pipes. This ensures strict OS-level boundary isolation between client orchestrators and server subprocesses.

### Data Normalization
The systematic transformation of heterogeneous raw fields—such as bank-specific column naming conventions, disparate date string formats, and localized currency indicators—into a uniform internal data schema standardized around canonical properties.

### Parameterized SQL Query
A database query execution practice wherein input parameters are passed separately from the SQL statement template to the relational database driver. This technique prevents SQL injection vulnerabilities by ensuring user input cannot alter execution logic.

### Path Traversal Defense
A file access validation methodology that computes canonical target file paths and asserts that target locations remain strictly nested within designated directory boundaries.

---

## 2. System Architecture and Design Overview

The Budget Analysis Agent system is constructed using a decoupled, micro-server architecture designed around the Model Context Protocol (MCP). The core design principle establishes an explicit boundary between artificial intelligence reasoning engines and physical data persistence mechanisms. The primary Large Language Model never directly accesses the local storage drive, executes raw file stream operations, or opens relational database connections. Instead, every interaction with user financial data is mediated through explicit RPC tool calls directed to specialized, isolated MCP server runtimes.

```
+-----------------------------------------------------------------------+
|                           User Interface                              |
|           (Streamlit Web Application / Interactive CLI)               |
+-----------------------------------+-----------------------------------+
                                    |
                                    v
+-----------------------------------------------------------------------+
|                      BudgetAgent Orchestrator                         |
|                    (agent.py / OpenAI API Client)                     |
+-----------------+-----------------------------------+-----------------+
                  |                                   |
                  | stdio IPC                         | stdio IPC
                  v                                   v
+-----------------------------------+   +-------------------------------+
|       Filesystem MCP Server       |   |       SQLite MCP Server       |
|    (mcp_servers/filesystem_...)   |   |   (mcp_servers/sqlite_server)  |
+-----------------+-----------------+   +---------------+---------------+
                  |                                     |
                  v                                     v
+-----------------------------------+   +-------------------------------+
|         documents/ Folder         |   |     data/transactions.db      |
|    (PDF, CSV, XLSX Financials)    |   |       (SQLite Database)       |
+-----------------------------------+   +-------------------------------+
```

The system topology separates responsibilities into three distinct operational tiers:

1. **User Interface Tier**: Represented by either a Streamlit web application (`app.py`) or a Command Line Interface interactive loop (`agent.py`). This layer manages non-blocking user input collection, session state maintenance, document upload streams, and natural language response rendering.
2. **Orchestration Tier**: Encapsulated within the `BudgetAgent` class in `agent.py`. This component initializes sub-process bindings to the tool servers, exposes server capabilities to the LLM runtime, maintains context thread state, and coordinates multi-turn reasoning loops.
3. **Data Access Tier**: Composed of two standalone FastMCP server processes:
   - The Filesystem Server (`filesystem_server.py`), which owns document identification and format parsing across Portable Document Format (`.pdf`), Comma-Separated Values (`.csv`), and Microsoft Excel (`.xlsx`, `.xls`) structures.
   - The SQLite Server (`sqlite_server.py`), which manages transactional storage schema initialization, structural data insertion, comparative metrics generation, recurring subscription heuristic calculation, and safe query execution.

This decoupled layout guarantees system reliability and security. If a file format parser encounters a malformed document stream, the exception is trapped at the MCP server layer and returned to the agent as a clean JSON error response, keeping the main web server process stable.

---

## 3. Filesystem Model Context Protocol Server (`filesystem_server.py`)

### 3.1 Overview and Security Parameters
The Filesystem MCP server (`filesystem_server.py`) is responsible for discovering, reading, and parsing local financial files located within the project's documents repository. It operates under a strict principle of least privilege: file reads are hard-restricted to a single, designated directory root, defaulting to the `documents/` folder relative to the project root. This target directory path can be modified dynamically at runtime by defining the `BUDGET_AGENT_DOCUMENTS_DIR` environment variable.

Directory restriction is strictly enforced by the internal helper function `_safe_path(filename)`. When a tool call requests access to a specific filename, `_safe_path` resolves the absolute canonical path of the request using `os.path.abspath` and compares it against the resolved canonical path of the configured documents root. If the target path does not share the parent directory prefix or attempts relative directory traversal using `..` sequences, `_safe_path` raises a `ValueError` with an explicit security violation message. Additionally, if the target file does not exist, a `FileNotFoundError` is thrown before any read operations are initiated.

### 3.2 Multi-Format Document Parsing Engine
The server converts raw financial files into a normalized array of dictionary records containing three core keys: `date`, `description`, and `amount`.

#### CSV and Excel Parsing Mechanics
Delimited text files (`.csv`) and tabular spreadsheet workbooks (`.xlsx`, `.xls`) are ingested via `pandas.read_csv` and `pandas.read_excel` respectively. Because different banking institutions use varying column names, the internal function `_normalize_dataframe` applies an automated column resolution heuristic:
1. Column headers are stripped of whitespace and converted to lower case.
2. The engine scans for target column header substrings matching candidates:
   - Date column matching terms: `date`
   - Description column matching terms: `description`, `merchant`, `narration`, `particulars`, `details`
   - Amount column matching terms: `amount`, `debit`, `value`, `withdrawal`
3. For each row in the DataFrame, values extracted from candidate columns are passed through `_to_float()`. This utility strips localized currency symbols (such as Indian Rupee symbols), removes comma thousands separators, and converts string numbers to 64-bit floating point representations.

#### PDF Statement Extraction Mechanics
Portable Document Format files (`.pdf`) are processed using the `pdfplumber` engine inside `_parse_pdf()`. The extraction sequence operates as follows:
1. The PDF is opened and iterated page by page.
2. `pdfplumber` extracts raw tabular bounding boxes using `extract_tables()`.
3. The first row of each identified table is evaluated as a header array.
4. Subsequent table rows are mapped to dictionary objects by matching header strings against keyword patterns (`date`, `desc`/`particular`/`narration`/`merchant`, `amount`/`debit`/`withdraw`).
5. Extracted strings are sanitized, normalized, and converted into floating point amounts before being returned to the caller.

### 3.3 Server Tool Definitions

#### `list_documents()`
- **Purpose**: Discovers and returns metadata for all supported statement files available within the configured documents directory.
- **Arguments**: None.
- **Return Value**: An array of dictionary structures containing:
  - `filename` (string): The standard file name on disk.
  - `size_bytes` (integer): Total file size in bytes.
  - `type` (string): Lowercase extension name representing the format (e.g., `csv`, `pdf`, `xlsx`).

#### `read_statement(filename)`
- **Purpose**: Reads a targeted document file from storage, detects its format, executes format-specific parsing routines, and returns normalized transaction rows.
- **Arguments**: `filename` (string, required): Name of the file within the documents directory.
- **Return Value**: A structured dictionary containing:
  - `filename` (string): Echoes the requested target name.
  - `transaction_count` (integer): Total number of valid transaction rows extracted.
  - `transactions` (array of objects): Sequence of extracted normalized transaction records containing `date`, `description`, and `amount`.

---

## 4. SQLite Model Context Protocol Server (`sqlite_server.py`)

### 4.1 Overview and Relational Database Schema
The SQLite MCP Server (`sqlite_server.py`) acts as the exclusive database interface for the system. The underlying storage runtime relies on SQLite 3, reading its path configuration from the `BUDGET_AGENT_DB_PATH` environment variable, or defaulting to `data/transactions.db`.

Upon server initialization, connection request, or tool invocation, `_conn()` ensures that the destination directory exists and executes an idempotent DDL statement creating the primary data table:

```sql
CREATE TABLE IF NOT EXISTS transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT,
    month TEXT,
    merchant TEXT,
    description TEXT,
    category TEXT,
    amount REAL,
    source_file TEXT
)
```

The database schema properties serve targeted structural purposes:
- `id`: Unique surrogate integer primary key with auto-increment behavior.
- `date`: Raw or normalized transaction date string (ideally `YYYY-MM-DD`).
- `month`: Derived year-month string formatted strictly as `YYYY-MM`, indexed implicitly by analytical SQL queries to enable rapid monthly aggregation and comparison.
- `merchant`: Extracted vendor or payee entity name determined during LLM categorization.
- `description`: Full raw line-item narration from the original statement.
- `category`: Financial category classification (e.g., `Housing`, `Food & Dining`, `Subscriptions`, `Utilities`).
- `amount`: Signed numerical value representing transaction monetary impact.
- `source_file`: Optional audit string recording the original document filename.

### 4.2 Server Tool Definitions

#### `insert_transactions(transactions, source_file=None)`
- **Purpose**: Receives bulk arrays of categorized transaction records, derives month keys, and persists them into the SQLite repository using parameterized SQL statements.
- **Arguments**:
  - `transactions` (array of objects, required): Array of transaction dictionaries containing `date`, `merchant`, `description`, `category`, and `amount`.
  - `source_file` (string, optional): Originating file identifier.
- **Internal Logic**: Runs regex extraction (`_extract_month`) on the `date` parameter using pattern `(\d{4})-(\d{2})` to ensure standard `YYYY-MM` month field populations.
- **Return Value**: Dictionary containing `inserted` (integer count of added rows).

#### `query_summary(category=None, month=None)`
- **Purpose**: Computes aggregate expenditure metrics filtered by specific categories, target months, or broad global scopes.
- **Arguments**:
  - `category` (string, optional): Target category filter.
  - `month` (string, optional): Target month filter in `YYYY-MM` format.
- **Return Value**: Dictionary containing:
  - `total` (float): Aggregate sum of matching transaction amounts.
  - `breakdown` (array of objects): Per-category summary list showing `category` name, `total` expenditure sum, and row `count`.

#### `monthly_comparison(month_a, month_b)`
- **Purpose**: Generates side-by-side comparative analysis between two distinct temporal billing periods.
- **Arguments**:
  - `month_a` (string, required): Baseline comparison month (`YYYY-MM`).
  - `month_b` (string, required): Target comparison month (`YYYY-MM`).
- **Mathematical Formula**: For each identified category present across either month, the percentage change metric `pct_change` is computed using standard delta ratio math:
  
  $$\text{pct\_change} = \frac{V_b - V_a}{V_a} \times 100$$
  
  If $V_a = 0$ and $V_b > 0$, the change defaults to $100.0\%$; if both equal zero, it yields $0.0\%$.
- **Return Value**: Dictionary containing `month_a`, `month_b`, and an array of `comparison` objects with category baseline totals, comparison totals, and computed percentage deltas.

#### `list_recurring_merchants(min_months=2)`
- **Purpose**: Performs statistical detection of recurring fixed-cost or subscription spending patterns across multiple statement cycles.
- **Arguments**: `min_months` (integer, default=2): Minimum distinct month occurrence threshold.
- **Underlying SQL Logic**: Executes standard group aggregation queries:

```sql
SELECT merchant, COUNT(DISTINCT month) as months, AVG(amount) as avg_amount,
       MIN(amount) as min_amount, MAX(amount) as max_amount
FROM transactions
WHERE merchant IS NOT NULL
GROUP BY merchant
HAVING months >= ?
ORDER BY months DESC
```

- **Return Value**: Array of merchant objects containing `merchant` name, `months_seen`, `avg_amount`, and `amount_range` tuple `[min_amount, max_amount]`.

#### `run_query(sql)`
- **Purpose**: Provides a read-only query execution endpoint for custom analytical questions that fall outside standard predefined tool APIs.
- **Arguments**: `sql` (string, required): The SQL statement to evaluate.
- **Security Constraints**: Strict validation is applied before query submission. The query string is trimmed, converted to lowercase, and verified via regex `^select\b`. Additional regex checks block dangerous keywords: `insert`, `update`, `delete`, `drop`, `alter`, `attach`, and `pragma`. Queries breaking these constraints trigger immediate `ValueError` exceptions.
- **Return Value**: Array of dictionaries mapping column headers to row values.

---

## 5. Agent Orchestrator Engine (`agent.py`)

### 5.1 System Architecture and Subprocess Lifecycle
The `BudgetAgent` class in `agent.py` functions as the client runtime. It handles inter-process execution, tools registration, prompt engineering, and LLM communication.

When `BudgetAgent.connect()` is called, it initializes an `AsyncExitStack` context. It launches `filesystem_server.py` and `sqlite_server.py` as Python child processes bound to stdio pipes (`stdio_client`). The client initializes an asynchronous `ClientSession` over each pipe, issues `session.initialize()`, and executes `list_tools()`. The returned MCP tool definitions are aggregated into `self.tools`, mapping each tool name to its respective session instance in `self.tool_to_session`.

```
                  +--------------------------------+
                  |  BudgetAgent.connect() Initiated|
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  | Launch Stdio Server Parameters  |
                  |  - filesystem_server.py        |
                  |  - sqlite_server.py            |
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |  Establish ClientSession Pipes |
                  |  Issue RPC session.initialize()|
                  +---------------+----------------+
                                  |
                                  v
                  +--------------------------------+
                  |   Execute session.list_tools() |
                  | Register Tool Schema Handlers  |
                  +--------------------------------+
```

### 5.2 System Prompt Directive Configuration
The agent's behavior is driven by a system prompt (`SYSTEM_PROMPT`) configured to enforce strict tool usage patterns and operational rules:
1. Explains that the agent lacks direct disk or SQL permissions and must operate entirely through MCP tool RPC requests.
2. Mandates an end-to-end execution workflow: document discovery via `list_documents`, document reading via `read_statement`, vendor categorization, record storage via `insert_transactions`, and query verification.
3. Defines vendor categorization guidelines (e.g., mapping Amazon to `Shopping`, Swiggy/Zomato to `Food & Dining`, Uber/Ola to `Transport`, utility bills to `Utilities`).
4. Mandates ISO date normalization (`YYYY-MM-DD`) and clean merchant name extraction prior to database insertion.
5. Directs responses to prioritize clear, numerical answers using proper currency symbols (e.g., ₹).

### 5.3 OpenAI SDK and Model Endpoint Integration
LLM inference requests are dispatched via the `openai.OpenAI` client initialized within `BudgetAgent.__init__()`. The runtime targets the NVIDIA API Catalog integration endpoint:
- `base_url`: `https://integrate.api.nvidia.com/v1`
- `model`: `meta/llama-3.3-70b-instruct`
- Required API Key Variable: `NVIDIA_API_KEY`

---

## 6. Graphical User Interface Integration (`app.py`)

### 6.1 Streamlit Page Architecture and Session Management
`app.py` delivers a browser-based user web application built on Streamlit. To allow asynchronous MCP I/O tasks to run smoothly within Streamlit's synchronous execution model, `app.py` applies `nest_asyncio.apply()` on startup.

State persistence across page re-renders is managed using Streamlit's `st.session_state` storage context:
- `st.session_state.agent`: Holds the singleton connected instance of `BudgetAgent`.
- `st.session_state.messages`: Stores the conversational display structure (role and text content) for UI chat components.
- `st.session_state.history`: Maintains the raw message exchange context passed into `agent.ask()`.

### 6.2 Application Execution Workflow

```
User Action: Upload File / Send Prompt
   |
   +---> File Upload Stream:
   |        1. Receive File Buffer via st.file_uploader.
   |        2. Write Buffer Bytes to documents/ Directory.
   |        3. Trigger UI Rerun via st.rerun().
   |
   +---> Chat Prompt Entry:
            1. Append User Message to st.session_state.messages.
            2. Retrieve Singleton Agent via get_agent().
            3. Run Async Loop: loop.run_until_complete(agent.ask(prompt)).
            4. Append Assistant Response to Session Messages.
            5. Render Response to Streamlit Chat Viewport.
```

---

## 7. Deployment, Configuration, and Environment Setup

### 7.1 Dependencies and Technical Prerequisites
The application requires Python 3.10+ and the core dependencies declared in `requirements.txt`:

```
mcp
anthropic
pandas
openpyxl
pdfplumber
streamlit
python-dotenv
openai
```

### 7.2 Environment Variable Specifications
System behavior is governed by three primary environment variables defined within a `.env` configuration file:

```ini
# NVIDIA API Authorization Key for Llama 3.3 70B Model Access (Required)
NVIDIA_API_KEY=nvapi-your-key-here

# Optional Override Paths
BUDGET_AGENT_DOCUMENTS_DIR=c:\Users\Admin\Downloads\budget-analysis-agent (1)\budget-analysis-agent\documents
BUDGET_AGENT_DB_PATH=c:\Users\Admin\Downloads\budget-analysis-agent (1)\budget-analysis-agent\data\transactions.db
```

### 7.3 Operational Launch Procedures

#### Command-Line Execution
Single Query Direct Mode:
```bash
python agent.py "Analyze my June expenses"
```

Interactive Terminal Loop:
```bash
python agent.py
```

#### Streamlit Web Interface Launch
```bash
streamlit run app.py
```

Upon launch, open the displayed local HTTP URL (typically `http://localhost:8501`) to access statement management and financial analysis tools.
