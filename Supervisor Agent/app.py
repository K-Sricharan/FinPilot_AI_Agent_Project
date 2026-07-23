"""
Streamlit Web UI for FinPilot AI Supervisor Agent.
Routes user prompts to Budget Analysis Agent or Tax Planning Agent dynamically.

Usage:
    streamlit run app.py
"""

import asyncio
import os
import sys
from pathlib import Path

import nest_asyncio
nest_asyncio.apply()

import streamlit as st

# Setup import paths
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from supervisor import FinPilotSupervisor

# Page Config
st.set_page_config(
    page_title="FinPilot AI — Multi-Agent Supervisor",
    page_icon="🤖",
    layout="wide",
)

# Title & Subtitle
st.title("🤖 FinPilot AI — Supervisor Agent")
st.caption("Intelligent Multi-Agent Orchestrator for Budget Analysis & Indian Tax Planning")

if not os.environ.get("NVIDIA_API_KEY"):
    st.error("⚠️ NVIDIA_API_KEY is not set in environment variables. Please check your .env file.")
    st.stop()


def get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


@st.cache_resource
def init_supervisor():
    loop = get_event_loop()
    supervisor = FinPilotSupervisor()
    loop.run_until_complete(supervisor.connect())
    return supervisor


# Initialize supervisor
try:
    supervisor = init_supervisor()
except Exception as e:
    st.error(f"Failed to initialize Supervisor Agent: {e}")
    st.stop()

# Sidebar Setup
with st.sidebar:
    st.header("📄 Upload Financial Statements")
    docs_dir = WORKSPACE_DIR / "Budget analysis agent - final" / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    
    uploaded_file = st.file_uploader("Add bank statement for Budget Agent", type=["pdf", "csv", "xlsx", "xls"])
    if uploaded_file is not None:
        dest_path = docs_dir / uploaded_file.name
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"Saved `{uploaded_file.name}` to documents directory.")

    existing_docs = sorted(os.listdir(docs_dir))
    if existing_docs:
        st.caption("Available Statements:")
        for doc in existing_docs:
            st.markdown(f"- 📄 `{doc}`")

    st.divider()
    st.subheader("💡 Try Quick Prompts")

    sample_prompts = [
        ("📊 Budget Query", "Analyze my June expenses"),
        ("🧾 Tax Query", "Which tax regime is better for 12 LPA income?"),
        ("📚 Tax Law Query", "Explain Section 80C and HRA exemptions"),
        ("🔄 Hybrid Query", "Analyze my expenses and calculate potential tax savings"),
    ]

    for label, sample_q in sample_prompts:
        if st.button(f"{label}: \"{sample_q}\"", key=sample_q):
            st.session_state.prompt_input = sample_q

    st.divider()
    if st.button("🗑️ Clear Chat History", type="secondary"):
        st.session_state.chat_history = []
        st.session_state.budget_history = []
        st.session_state.tax_messages = []
        st.rerun()

# State Management
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "budget_history" not in st.session_state:
    st.session_state.budget_history = []
if "tax_messages" not in st.session_state:
    st.session_state.tax_messages = []

# Display Chat Messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        if msg.role == "assistant" if hasattr(msg, "role") else msg["role"] == "assistant":
            if "agent_name" in msg:
                st.markdown(f"**🎯 Routed to:** `{msg['agent_name']}` *(Reason: {msg['reasoning']})*")
            st.markdown(msg["content"])
        else:
            st.markdown(msg["content"])

# Chat Input
user_input = st.chat_input("Ask a finance or tax question...")

# Handle sidebar button prompt fill
if "prompt_input" in st.session_state and st.session_state.prompt_input:
    user_input = st.session_state.prompt_input
    del st.session_state.prompt_input

if user_input:
    # Render user prompt
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process via Supervisor Agent
    with st.chat_message("assistant"):
        with st.spinner("working..."):
            loop = get_event_loop()
            result = loop.run_until_complete(
                supervisor.route_and_execute(
                    user_input,
                    budget_history=st.session_state.budget_history,
                    tax_messages=st.session_state.tax_messages
                )
            )

            # Update session state histories
            st.session_state.budget_history = result["budget_history"]
            st.session_state.tax_messages = result["tax_messages"]

            # Render routing details badge & answer
            st.markdown(f"**🎯 Routed to:** `{result['agent_name']}` *(Reason: {result['reasoning']})*")
            st.markdown(result["response"])

            st.session_state.chat_history.append({
                "role": "assistant",
                "agent_name": result["agent_name"],
                "reasoning": result["reasoning"],
                "content": result["response"]
            })
