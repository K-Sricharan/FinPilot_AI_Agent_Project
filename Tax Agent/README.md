# 🤖 FinPilot AI – Tax Planning AI Agent

> An end-to-end AI-powered Tax Planning Assistant built using **LangGraph**, **LangChain**, **RAG**, **FAISS**, **NVIDIA AI Endpoints**, and **Streamlit**.

FinPilot AI is a production-style AI Agent that helps users understand Indian Income Tax regulations, compare tax regimes, calculate taxes accurately, and explain tax concepts in simple language.

Unlike a traditional chatbot, this project combines **Large Language Models (LLMs)**, **Retrieval-Augmented Generation (RAG)**, and **deterministic Python tools** to provide accurate, explainable, and reliable tax assistance.

The purpose of this project is to understand and implement every core component involved in building modern AI Agents from scratch.

---

# 🚀 Features

FinPilot AI can:

- 🤖 Answer Indian Income Tax related questions
- 📚 Retrieve tax information using RAG
- 🔍 Search tax documents using semantic search
- 🧮 Calculate income tax accurately
- 💰 Compare Old vs New Tax Regime
- 🏠 Calculate HRA Exemption
- 📄 Explain Sections 80C and 80D
- 📊 Apply tax deductions
- 💬 Generate human-friendly responses
- 🧠 Automatically decide which tool to use
- 💻 Interactive Streamlit Chat Interface

---

# 🏗️ High-Level Architecture

```
                    User
                      │
                      ▼
             Streamlit Frontend
                      │
                      ▼
             LangGraph ReAct Agent
                      │
          ┌───────────┴───────────┐
          │                       │
          ▼                       ▼
    RAG Search Tool        Tax Calculator Tool
          │                       │
          ▼                       ▼
   FAISS Vector Store      Python Business Logic
          │                       │
          └───────────┬───────────┘
                      ▼
             NVIDIA Hosted LLM
                      │
                      ▼
              Natural Language Answer
```

---

# 📚 What is an AI Agent?

An **AI Agent** is an intelligent software system that can:

- Understand user requests
- Make decisions
- Use external tools
- Retrieve information
- Perform calculations
- Generate accurate responses

Unlike a normal chatbot that only relies on an LLM, an AI Agent can interact with external systems to produce more reliable answers.

Traditional Chatbot

```
User
 │
 ▼
LLM
 │
 ▼
Answer
```

AI Agent

```
User
 │
 ▼
LLM
 │
 ▼
Decides which tool to use
 │
 ▼
Tool Execution
 │
 ▼
LLM
 │
 ▼
Final Response
```

---

# 🧠 What is LangGraph?

LangGraph is an orchestration framework used for building AI Agents.

Think of LangGraph as the **brain** of the application.

It is responsible for:

- Managing conversation flow
- Deciding whether tools are needed
- Executing tools
- Passing tool outputs back to the LLM
- Returning the final answer

Without LangGraph:

```
User
 │
 ▼
LLM
 │
 ▼
Answer
```

With LangGraph:

```
User
 │
 ▼
LLM
 │
 ▼
Needs Tool?
 │
 ├───────────┐
 │           │
 ▼           ▼
Yes          No
 │
 ▼
Execute Tool
 │
 ▼
LLM
 │
 ▼
Final Answer
```

---

# 🧠 What is an LLM?

A **Large Language Model (LLM)** is a deep learning model trained on massive amounts of text.

Its responsibilities include:

- Understanding language
- Reasoning
- Following instructions
- Generating natural responses

In this project, the LLM **does not calculate taxes**.

Instead, it decides:

- Should I retrieve documents?
- Should I execute the tax calculator?
- How should I explain the result?

---

# 🔧 What are Tools?

A Tool is simply a Python function that an AI Agent can execute.

Example:

```python
@tool
def compare_tax_regimes(...):
```

Instead of calculating taxes itself, the LLM instructs LangGraph to execute the tool.

```
User Question
      │
      ▼
LLM decides
      │
      ▼
Tax Tool
      │
      ▼
Python Calculation
      │
      ▼
LLM explains result
```

This prevents hallucinations and guarantees accurate calculations.

---

# 📚 What is Retrieval-Augmented Generation (RAG)?

RAG stands for **Retrieval-Augmented Generation**.

Instead of relying only on the LLM's memory, the AI first retrieves relevant documents and then generates an answer based on those documents.

Without RAG

```
Question
 │
 ▼
LLM Memory
 │
 ▼
Answer
```

With RAG

```
Question
 │
 ▼
Retriever
 │
 ▼
Relevant Documents
 │
 ▼
LLM
 │
 ▼
Grounded Answer
```

This significantly improves factual accuracy.

---

# 🔎 What is Semantic Search?

Traditional search matches keywords.

Semantic Search matches **meaning**.

Example:

```
Question:
Explain HRA

Document:
House Rent Allowance Rules

Result:
Matched successfully
```

Even though the exact words differ, semantic search retrieves the correct document.

---

# 🧠 What are Embeddings?

Embeddings convert text into vectors (lists of numbers).

Example

```
"What is HRA?"

↓

[0.42, -0.91, 1.08, ...]
```

Similar meanings produce similar vectors.

Example:

```
Explain HRA

What is HRA

House Rent Allowance

↓

Very close vectors
```

Embeddings enable semantic search.

---

# 🗂️ What is FAISS?

FAISS is a Vector Database.

Instead of storing plain text, it stores vector embeddings.

Workflow:

```
PDF Documents

↓

Text Chunks

↓

Embeddings

↓

FAISS Vector Store
```

When a question arrives:

```
Question

↓

Embedding

↓

Similarity Search

↓

Top Relevant Chunks
```

---

# 📄 Document Processing Pipeline

The knowledge base consists of official tax documents.

```
PDF Documents

↓

PyPDFLoader

↓

Raw Documents

↓

RecursiveCharacterTextSplitter

↓

Text Chunks

↓

NVIDIA Embeddings

↓

FAISS Vector Store
```

---

# 🧮 Tax Calculator

The Tax Calculator is implemented entirely in Python.

It performs deterministic calculations for:

- Old Tax Regime
- New Tax Regime
- HRA Exemption
- Section 80C
- Section 80D
- Standard Deduction
- Home Loan Interest
- Health & Education Cess
- Tax Comparison

Unlike an LLM, Python always returns the same result for the same inputs.

---

# 🔄 End-to-End Workflow

## Example 1 — Tax Rule Question

User asks:

```
What is Section 80C?
```

Workflow

```
User

↓

Streamlit

↓

LangGraph Agent

↓

LLM decides RAG is required

↓

RAG Tool

↓

Retriever

↓

FAISS Search

↓

Relevant Tax Documents

↓

LLM

↓

Final Answer
```

---

## Example 2 — Tax Calculation

User asks:

```
Salary = ₹18,00,000

80C = ₹1,50,000

Which regime is better?
```

Workflow

```
User

↓

Streamlit

↓

LangGraph Agent

↓

LLM decides Tax Tool is required

↓

Tax Calculator

↓

Python Calculation

↓

LLM

↓

Final Response
```

---

# ⚙️ Tech Stack

## AI Frameworks

- LangGraph
- LangChain

## Large Language Model

- NVIDIA AI Endpoints
- Google DiffusionGemma *(Current Model)*

## Retrieval-Augmented Generation

- NVIDIA Embeddings
- FAISS
- PyPDFLoader
- RecursiveCharacterTextSplitter

## Backend

- Python

## Frontend

- Streamlit

## Utilities

- python-dotenv
- Dataclasses

---

# 📂 Project Structure

```
Tax Agent
│
├── app.py
├── streamlit_app.py
├── requirements.txt
│
├── Data/
│
├── Models/
│      nvidia_llm.py
│
├── Prompts/
│      system_prompt.py
│
├── Rag/
│      retriever.py
│      rag_tool.py
│      LangGraph_agent.py
│
├── Tools/
│      tax_tools.py
│
└── vectorstore/
```

---

# 📌 Current Capabilities

### AI Agent

- LangGraph ReAct Agent
- Tool Calling
- Multi-turn Conversation
- Conversation Memory

### Retrieval-Augmented Generation

- Semantic Search
- FAISS Vector Database
- NVIDIA Embeddings
- PDF Knowledge Base

### Tax Calculations

- Old Regime
- New Regime
- HRA
- 80C
- 80D
- Home Loan Interest
- Standard Deduction
- Cess
- Tax Comparison

---

# 🎯 Learning Outcomes

This project demonstrates practical implementation of:

- AI Agents
- LangGraph
- LangChain
- Tool Calling
- Retrieval-Augmented Generation (RAG)
- Semantic Search
- Embeddings
- FAISS
- Prompt Engineering
- Streamlit
- Python Tool Development
- Production-style AI Application Architecture

# Project Vision

The objective of FinPilot AI is not just to build another chatbot, but to understand how modern AI Agents are designed for production environments.

By combining **Large Language Models**, **Retrieval-Augmented Generation**, and **deterministic Python tools**, the system produces responses that are more accurate, explainable, and reliable than using an LLM alone.

This project serves as a hands-on implementation of the core concepts behind real-world AI Agent systems used in enterprise applications.
