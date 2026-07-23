"""
streamlit_app.py

FinPilot AI
Tax Planning Assistant

"""

import streamlit as st

from langchain_core.messages import HumanMessage

from Rag.LangGraph_agent import get_agent


# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------

st.set_page_config(
    page_title="FinPilot AI",
    page_icon="💰",
    layout="wide",
)

# ---------------------------------------------------------
# Title
# ---------------------------------------------------------

st.title("💰 FinPilot AI")
st.caption("AI Powered Indian Tax Planning Assistant")

# ---------------------------------------------------------
# Sidebar
# ---------------------------------------------------------

with st.sidebar:

    st.header("FinPilot AI")

    st.write(
        """
        Ask questions like:

        • Which tax regime is better?

        • Calculate my income tax

        • Explain Section 80C

        • Explain HRA

        • Explain Section 80D
        """
    )

    if st.button("🗑 Clear Chat"):

        st.session_state.messages = []

        st.rerun()

# ---------------------------------------------------------
# Initialize Agent
# ---------------------------------------------------------

agent = get_agent()

# ---------------------------------------------------------
# Session State
# ---------------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []

# ---------------------------------------------------------
# Display Previous Messages
# ---------------------------------------------------------

for message in st.session_state.messages:

    if message.type == "human":

        with st.chat_message("user"):

            st.markdown(message.content)

    else:

        with st.chat_message("assistant"):

            st.markdown(message.content)

# ---------------------------------------------------------
# Chat Input
# ---------------------------------------------------------

question = st.chat_input("Ask your tax question...")

# ---------------------------------------------------------
# User Message
# ---------------------------------------------------------

if question:

    human_message = HumanMessage(content=question)

    st.session_state.messages.append(human_message)

    with st.chat_message("user"):

        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Thinking..."):

            response = agent.invoke(

                {

                    "messages": st.session_state.messages

                }

            )

            st.session_state.messages = response["messages"]

            answer = st.session_state.messages[-1].content

            st.markdown(answer)