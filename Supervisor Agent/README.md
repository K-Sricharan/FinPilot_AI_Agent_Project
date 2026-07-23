# FinPilot AI — Multi-Agent Supervisor

The **FinPilot AI Supervisor Agent** is an intelligent orchestrator that connects the two specialized domain agents in this system:

1. **📊 Budget Analysis Agent** (`Budget analysis agent - final`):
   - FastMCP client agent with Filesystem and SQLite tools.
   - Categorizes, tracks, and analyzes expenses from bank/credit card statements (PDF/CSV/XLSX).
2. **🧾 Tax Planning Agent** (`Tax Agent`):
   - LangGraph ReAct agent with FAISS RAG retriever and tax comparison tools.
   - Compares Old vs New Tax Regimes and provides advice on deductions (Section 80C, 80D, HRA).

> [!NOTE]
> The `Preparation` folder is intentionally excluded and preserved untouched.

---

## 🏗️ Architecture & Routing

```
                        ┌────────────────────────┐
                        │      User Prompt       │
                        └───────────┬────────────┘
                                    │
                                    ▼
                        ┌────────────────────────┐
                        │   Supervisor Router    │
                        │  (Llama-3.3-70B LLM)   │
                        └─────┬────────────┬─────┘
                              │            │
               ┌──────────────┘            └──────────────┐
               ▼                                          ▼
 ┌──────────────────────────┐               ┌──────────────────────────┐
 │  Budget Analysis Agent   │               │    Tax Planning Agent    │
 │  (MCP Client + SQLite)   │               │   (LangGraph + RAG/Tools)│
 └──────────────────────────┘               └──────────────────────────┘
```

### Intent Categories:
- **`BUDGET_AGENT`**: Spending, bank statements, Swiggy/Uber expenses, monthly summaries, SQLite transaction queries.
- **`TAX_AGENT`**: Income tax calculation, Old vs New regime comparisons, 80C/80D/HRA rules, tax savings tips.
- **`HYBRID`**: Combined questions requiring personal expense context + tax planning calculation (runs Budget Agent first, then passes findings to Tax Agent).
- **`GENERAL`**: General greetings or system capability questions.

---

## 🚀 Getting Started

### 1. Environment Setup
Ensure `NVIDIA_API_KEY` is present in `.env` (or inherited from parent/subfolder `.env`).

```bash
NVIDIA_API_KEY=your_nvidia_api_key
```

### 2. Run Interactive CLI Mode
```bash
python supervisor.py
```

Or pass a single question directly:
```bash
python supervisor.py "Which tax regime is better for 15 LPA income?"
```

### 3. Run Streamlit Web Application
```bash
streamlit run app.py
```

---

## 📁 File Structure

```
Supervisor Agent/
├── app.py           # Streamlit multi-agent UI with routing badges & statement uploader
├── supervisor.py    # Core FinPilotSupervisor class & routing logic
├── requirements.txt # Combined python package dependencies
└── README.md        # Architecture & documentation
```
