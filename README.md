# FinPilot AI Multi-Agent Financial Assistant

FinPilot AI is an intelligent multi-agent financial assistant designed to streamline personal budget management, expense tracking, statement analysis, and Indian income tax planning. The system combines dedicated domain agents under a central supervisor orchestrator to provide unified financial intelligence.

## System Architecture

The project consists of three core components:

1. Supervisor Agent: Acts as the central intelligence router for the platform. It inspects incoming queries, classifies intent using a Meta Llama 3.3 70B model, and dynamically routes the request to the appropriate specialized agent or orchestrates multi-step execution.

2. Budget Analysis Agent: Built using the Model Context Protocol (MCP). It connects to two dedicated MCP servers (Filesystem MCP Server and SQLite MCP Server) to read bank and credit card statements in PDF, CSV, or XLSX formats, automatically categorize transaction descriptions, and answer historical spending queries.

3. Tax Planning Agent: Built using LangGraph ReAct agent architecture combined with FAISS vector retrieval-augmented generation (RAG). It provides expert guidance on Indian tax planning, compares the Old Tax Regime versus the New Tax Regime, and calculates eligible tax deductions under Section 80C, Section 80D, and House Rent Allowance (HRA) regulations.

## Intelligent Routing Workflow

When a user enters a query, the system receives and processes it through an automated three-stage routing mechanism:

First, Query Reception and Intent Classification are performed. The user's query is received by the Supervisor Agent, which forwards the message to the Llama 3.3 70B language model. The model analyzes the intent and categorizes the query into BUDGET_AGENT for expenses, TAX_AGENT for tax calculations, HYBRID for queries spanning both domains, or GENERAL for standard conversation.

Second, Routing and Agent Execution take place. Based on the classification, the Supervisor Agent forwards the query to the correct target agent. BUDGET_AGENT queries are sent to the Budget Analysis Agent to execute MCP tools on statement files and SQLite databases. TAX_AGENT queries are sent to the Tax Planning Agent to run LangGraph workflows and FAISS vector RAG retrieval.

Third, Hybrid Processing is executed when a query requires data from both specialized agents. In this case, the Supervisor Agent first calls the Budget Analysis Agent to gather spending figures, then passes those financial details into the Tax Planning Agent to generate customized tax planning recommendations.

## Installation and Configuration

### Prerequisites
Python version 3.10 or higher is required along with an active NVIDIA API key for model inference endpoints.

### Step 1: Environment Setup
Clone the repository and set up your Python environment:

```bash
git clone https://github.com/K-Sricharan/FinPilot_AI_Agent_Project.git
cd FinPilot_AI_Agent_Project
```

### Step 2: Environment Variables
Create a `.env` file in the root directory containing your NVIDIA API key:

```env
NVIDIA_API_KEY=your_nvidia_api_key_here
```

### Step 3: Dependencies Installation
Install the required Python packages for the supervisor and sub-agents:

```bash
pip install -r "Supervisor Agent/requirements.txt"
```

## How to Run

### Interactive CLI Mode
You can start the command-line interface by running the supervisor script:

```bash
python "Supervisor Agent/supervisor.py"
```

You can also pass a query directly as a command argument:

```bash
python "Supervisor Agent/supervisor.py" "Which tax regime is better for 12 LPA income?"
```

### Streamlit Web Application
To launch the interactive web application, run:

```bash
streamlit run "Supervisor Agent/app.py"
```

The Streamlit interface provides a clean chat layout, visual routing information for each response, a statement file uploader, and quick-prompt selection options.

## Directory Layout

The project repository is structured as follows:

`Supervisor Agent/`: Contains `supervisor.py` for routing logic, `app.py` for the Streamlit web application, and `requirements.txt`.

`Budget analysis agent - final/`: Contains `agent.py` for the MCP client orchestrator, `mcp_servers/` for filesystem and database servers, `documents/` for input statements, and SQLite database utilities.

`Tax Agent/`: Contains `Rag/` for LangGraph agent definitions and FAISS vector retrieval, `Tools/` for tax calculation utilities, and `Data/` containing official Indian tax documentation PDFs.

`Preparation/`: Contains project planning documents and reference guides.
