"""
langgraph_agent.py

LangGraph Agent for the Tax Planning AI Agent.

The agent automatically:
- Decides whether to call a tool
- Executes the tool
- Feeds the tool result back to the LLM
- Returns the final response
"""

from langgraph.prebuilt import create_react_agent

from models.nvidia_llm import llm
from Prompts.system_prompt import SYSTEM_PROMPT

from Tools.tax_tools import compare_tax_regimes
from Rag.rag_tool import search_tax_documents


# ---------------------------------------------------------
# Register Tools
# ---------------------------------------------------------

TOOLS = [
    compare_tax_regimes,
    search_tax_documents
]


# ---------------------------------------------------------
# Create LangGraph ReAct Agent
# ---------------------------------------------------------

agent = create_react_agent(
    model=llm,
    tools=TOOLS,
    prompt=SYSTEM_PROMPT,
)


def get_agent():
   
    return agent