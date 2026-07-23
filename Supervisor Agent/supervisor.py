"""
Supervisor Agent - FinPilot AI
-------------------------------
Connects the Budget Analysis Agent and Tax Planning Agent.
Determines user intent dynamically and routes queries to the appropriate specialized agent.
Does not modify any preparation folders.

Usage:
    python supervisor.py "How much did I spend on food in June?"
    python supervisor.py "Which tax regime is better for 12 LPA income?"
    python supervisor.py  # Interactive CLI mode
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure root directory .env or sub-folder .env files are loaded
BASE_DIR = Path(__file__).resolve().parent
WORKSPACE_DIR = BASE_DIR.parent

# Load environment variables
load_dotenv(BASE_DIR / ".env")
load_dotenv(WORKSPACE_DIR / "Budget analysis agent - final" / ".env")
load_dotenv(WORKSPACE_DIR / "Tax Agent" / ".env")

# Register paths for sub-agents
BUDGET_AGENT_DIR = WORKSPACE_DIR / "Budget analysis agent - final"
TAX_AGENT_DIR = WORKSPACE_DIR / "Tax Agent"

if str(BUDGET_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(BUDGET_AGENT_DIR))

if str(TAX_AGENT_DIR) not in sys.path:
    sys.path.insert(0, str(TAX_AGENT_DIR))

from openai import OpenAI
from langchain_core.messages import HumanMessage, AIMessage

# Import specialized agents
from agent import BudgetAgent

# Tax Agent setup (imported with cwd context handling)
def load_tax_agent():
    curr_dir = os.getcwd()
    try:
        os.chdir(TAX_AGENT_DIR)
        from Rag.LangGraph_agent import get_agent
        agent = get_agent()
        return agent
    finally:
        os.chdir(curr_dir)


MODEL_NAME = "meta/llama-3.3-70b-instruct"

CLASSIFICATION_PROMPT = """You are the Supervisor Router for FinPilot AI.
Your job is to analyze the user's query and route it to the correct specialized financial agent.

Specialized Agents:
1. BUDGET_AGENT:
   - Handles personal expense tracking, statement analysis (PDF/CSV/XLSX), monthly spending summaries, Swiggy/Uber/Zomato/Amazon categories, recurring merchants, database queries about past transactions.
2. TAX_AGENT:
   - Handles Indian tax planning, Old vs New Tax Regime comparisons, Section 80C, 80D, HRA deductions, tax exemptions, tax savings advice, tax rules and regulations.
3. HYBRID:
   - Required when a query asks for tax calculations based on personal spending/expense data or requires both budget analysis and tax optimization.
4. GENERAL:
   - Greetings, general questions about the system, or out-of-scope non-financial prompts.

Output MUST be valid JSON with exact keys:
{
  "intent": "BUDGET_AGENT" | "TAX_AGENT" | "HYBRID" | "GENERAL",
  "reasoning": "Short 1-sentence explanation of why this route was selected."
}
"""


class FinPilotSupervisor:
    def __init__(self):
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError("NVIDIA_API_KEY environment variable is required.")
        
        self.client = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=api_key
        )
        self.budget_agent = BudgetAgent()
        self.tax_agent = load_tax_agent()
        self.is_connected = False

    async def connect(self):
        """Initialize connections to underlying agents (e.g. MCP servers for Budget Agent)."""
        if not self.is_connected:
            await self.budget_agent.connect()
            self.is_connected = True

    async def close(self):
        """Close agent connections cleanly."""
        if self.is_connected:
            await self.budget_agent.close()
            self.is_connected = False

    def classify_intent(self, query: str) -> dict:
        """Classify user query using LLM router."""
        try:
            response = self.client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": CLASSIFICATION_PROMPT},
                    {"role": "user", "content": query}
                ],
                temperature=0.0,
                max_tokens=256
            )
            raw_content = response.choices[0].message.content.strip()
            
            # Clean JSON markdown fences if present
            if raw_content.startswith("```"):
                lines = raw_content.splitlines()
                raw_content = "\n".join([line for line in lines if not line.startswith("```")])
            
            data = json.loads(raw_content)
            intent = data.get("intent", "GENERAL").upper()
            reasoning = data.get("reasoning", "Routed based on query analysis.")
            return {"intent": intent, "reasoning": reasoning}
        except Exception as e:
            # Fallback classification if parsing fails
            query_lower = query.lower()
            if any(k in query_lower for k in ["tax", "80c", "80d", "hra", "regime", "deduction", "income tax"]):
                return {"intent": "TAX_AGENT", "reasoning": "Keyword match: Tax planning query."}
            elif any(k in query_lower for k in ["spend", "expense", "june", "may", "swiggy", "statement", "budget", "category"]):
                return {"intent": "BUDGET_AGENT", "reasoning": "Keyword match: Budget expense query."}
            else:
                return {"intent": "GENERAL", "reasoning": "General query fallback."}

    async def route_and_execute(
        self, 
        query: str, 
        budget_history: list[dict] = None, 
        tax_messages: list = None
    ) -> dict:
        """Process user query through supervisor routing."""
        if not self.is_connected:
            await self.connect()

        budget_history = budget_history or []
        tax_messages = tax_messages or []

        classification = self.classify_intent(query)
        intent = classification["intent"]
        reasoning = classification["reasoning"]

        if intent == "BUDGET_AGENT":
            answer, updated_budget_history = await self.budget_agent.ask(query, budget_history)
            return {
                "intent": "BUDGET_AGENT",
                "agent_name": "Budget Analysis Agent",
                "reasoning": reasoning,
                "response": answer,
                "budget_history": updated_budget_history,
                "tax_messages": tax_messages
            }

        elif intent == "TAX_AGENT":
            curr_dir = os.getcwd()
            try:
                os.chdir(TAX_AGENT_DIR)
                human_msg = HumanMessage(content=query)
                messages_input = tax_messages + [human_msg]
                res = self.tax_agent.invoke({"messages": messages_input})
                updated_tax_messages = res["messages"]
                answer = updated_tax_messages[-1].content
            finally:
                os.chdir(curr_dir)

            return {
                "intent": "TAX_AGENT",
                "agent_name": "Tax Planning Agent",
                "reasoning": reasoning,
                "response": answer,
                "budget_history": budget_history,
                "tax_messages": updated_tax_messages
            }

        elif intent == "HYBRID":
            # 1. Ask Budget Agent for spend details
            budget_query = f"Provide a detailed summary of my spending and investments relevant to this question: {query}"
            budget_ans, updated_budget_history = await self.budget_agent.ask(budget_query, budget_history)

            # 2. Feed spend summary + question to Tax Agent
            curr_dir = os.getcwd()
            try:
                os.chdir(TAX_AGENT_DIR)
                combined_prompt = (
                    f"User Query: {query}\n\n"
                    f"Budget Analysis Agent Data Summary:\n{budget_ans}\n\n"
                    f"Based on the above financial data and tax rules, answer the user's query comprehensively."
                )
                human_msg = HumanMessage(content=combined_prompt)
                messages_input = tax_messages + [human_msg]
                res = self.tax_agent.invoke({"messages": messages_input})
                updated_tax_messages = res["messages"]
                tax_ans = updated_tax_messages[-1].content
            finally:
                os.chdir(curr_dir)

            combined_response = (
                f"### 📊 Budget Data Summary\n{budget_ans}\n\n"
                f"### 🧾 Tax Planning Recommendation\n{tax_ans}"
            )

            return {
                "intent": "HYBRID",
                "agent_name": "Budget Analysis Agent + Tax Planning Agent",
                "reasoning": reasoning,
                "response": combined_response,
                "budget_history": updated_budget_history,
                "tax_messages": updated_tax_messages
            }

        else:  # GENERAL
            general_response = (
                "Hello! I am **FinPilot Supervisor Agent** ✈️\n\n"
                "I connect your **Budget Analysis Agent** and **Tax Planning Agent**.\n\n"
                "Here is what you can ask me:\n"
                "- **Budget Queries**: *'Analyze my June expenses'*, *'How much did I spend on food?'*, *'List recurring merchants'*\n"
                "- **Tax Queries**: *'Which tax regime is better for 15 LPA?'*, *'Explain Section 80C and HRA'*\n"
                "- **Combined Queries**: *'Calculate my tax savings based on my June rent and expenses'*."
            )
            return {
                "intent": "GENERAL",
                "agent_name": "Supervisor Agent",
                "reasoning": reasoning,
                "response": general_response,
                "budget_history": budget_history,
                "tax_messages": tax_messages
            }


async def main():
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    supervisor = FinPilotSupervisor()
    await supervisor.connect()
    try:
        if len(sys.argv) > 1:
            query = " ".join(sys.argv[1:])
            print(f"\n[Query]: {query}")
            result = await supervisor.route_and_execute(query)
            print(f"\n[Routed to: {result['agent_name']}]")
            print(f"[Reason]: {result['reasoning']}")
            print(f"\n[Answer]:\n{result['response']}\n")
        else:
            print("=" * 60)
            print("FinPilot AI - Supervisor Agent CLI")
            print("Connecting Budget Analysis Agent & Tax Planning Agent...")
            print("Type 'exit' or 'quit' to stop.")
            print("=" * 60)

            budget_history = []
            tax_messages = []

            while True:
                q = input("\nYou > ").strip()
                if not q:
                    continue
                if q.lower() in ("exit", "quit"):
                    print("Goodbye 👋")
                    break

                result = await supervisor.route_and_execute(
                    q, 
                    budget_history=budget_history, 
                    tax_messages=tax_messages
                )

                budget_history = result["budget_history"]
                tax_messages = result["tax_messages"]

                print(f"\n🎯 Routed to : {result['agent_name']}")
                print(f"💡 Reason    : {result['reasoning']}")
                print(f"\n🤖 Response  :\n{result['response']}")
                print("-" * 60)
    finally:
        await supervisor.close()


if __name__ == "__main__":
    asyncio.run(main())
