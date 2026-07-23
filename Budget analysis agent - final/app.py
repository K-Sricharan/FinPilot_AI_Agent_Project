"""
Streamlit UI for the Budget Analysis Agent.

Run with:
    streamlit run app.py

Drop your statements into documents/ first (or upload via the sidebar),
then just chat:
    "Analyze my June expenses"
    "How much did I spend on food this month?"
    "Compare June with May"
"""

import asyncio
import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

import nest_asyncio
nest_asyncio.apply()

from agent import BudgetAgent  # noqa: E402

st.set_page_config(page_title="Budget Analysis Agent", layout="centered")
st.title("Budget Analysis Agent")
st.caption("Reads your statements, categorizes spending, stores it, and answers questions about it.")

if not os.environ.get("NVIDIA_API_KEY"):
    st.error("NVIDIA_API_KEY")
    st.stop()


def get_event_loop():
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


def get_agent():
    if "agent" not in st.session_state:
        loop = get_event_loop()
        agent = BudgetAgent()
        loop.run_until_complete(agent.connect())
        st.session_state.agent = agent
    return st.session_state.agent


with st.sidebar:
    st.subheader("Documents")
    docs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "documents")
    os.makedirs(docs_dir, exist_ok=True)
    existing = sorted(os.listdir(docs_dir))
    if existing:
        for f in existing:
            st.write(f"📄 {f}")
    else:
        st.write("No files yet.")

    uploaded = st.file_uploader("Add a statement", type=["pdf", "csv", "xlsx", "xls"])
    if uploaded is not None:
        dest = os.path.join(docs_dir, uploaded.name)
        with open(dest, "wb") as f:
            f.write(uploaded.getbuffer())
        st.success(f"Saved {uploaded.name}")
        st.rerun()

    st.divider()
    st.subheader("Try asking")
    for q in [
        "Analyze my June expenses",
        "How much did I spend on food this month?",
        "Compare June with May",
        "Which subscriptions are recurring?",
    ]:
        st.code(q, language=None)

    if st.button("Reset chat"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt = st.chat_input("Ask about your spending...")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Working..."):
            agent = get_agent()
            loop = get_event_loop()
            answer, history = loop.run_until_complete(agent.ask(prompt, st.session_state.history))
            st.session_state.history = history
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
