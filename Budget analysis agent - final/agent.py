"""
Budget Analysis Agent
----------------------
The orchestrator. Connects to the Filesystem MCP server and the SQLite MCP
server as an MCP client, exposes their tools to Claude, and runs the
tool-use loop until Claude has a final natural-language answer.

Claude never touches files or SQL directly, it only ever calls MCP tools.

Usage:
    python agent.py "Analyze my June expenses"
    python agent.py   # drops into an interactive chat loop
"""

import asyncio
import os
import sys
from contextlib import AsyncExitStack

from openai import OpenAI
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

load_dotenv()

MODEL = "meta/llama-3.3-70b-instruct"

SYSTEM_PROMPT = """You are a Budget Analysis Agent, an AI financial assistant.

You have no direct access to the filesystem or any database. Everything
you know about the user's finances comes from calling tools on two MCP
servers:

- Filesystem MCP: list_documents, read_statement — for reading bank
  statements, credit card statements, and expense sheets (PDF/CSV/XLSX).
- SQLite MCP: insert_transactions, query_summary, monthly_comparison,
  list_recurring_merchants, run_query — for storing and querying
  categorized transaction data.

Your job end-to-end:
1. When asked to analyze a statement, call list_documents (if the filename
   isn't given) then read_statement to get raw transactions.
2. Categorize every transaction yourself using your judgment of the
   merchant/description (e.g. Amazon -> Shopping, Swiggy/Zomato -> Food,
   Uber/Ola -> Transport, rent/landlord -> Housing, Netflix/Spotify ->
   Subscriptions, grocery chains -> Grocery, electricity/water/gas ->
   Utilities, gym/fitness -> Health, salary/credit -> Income, etc).
   Extract a clean `merchant` name from the description. Normalize every
   date to YYYY-MM-DD before storing.
3. Store the categorized transactions with insert_transactions.
4. Use query_summary / monthly_comparison / list_recurring_merchants /
   run_query to answer the user's actual question.
5. Always finish with a direct, numbers-first natural-language answer —
   total spend, top categories, notable changes, and any budget or
   subscription callouts relevant to the question. Use ₹ for currency
   unless the data suggests otherwise.

Be concise. Don't narrate which tools you're calling — just do the work
and report the findings.
"""


class BudgetAgent:
    def __init__(self):
        api_key = os.environ.get("NVIDIA_API_KEY")
        if not api_key:
            raise RuntimeError(
                "NVIDIA_API_KEY"
            )
        self.client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        )
        self.sessions: dict[str, ClientSession] = {}
        self.tool_to_session: dict[str, ClientSession] = {}
        self.tools: list[dict] = []
        self._stack = AsyncExitStack()

    async def connect(self):
        base = os.path.dirname(os.path.abspath(__file__))
        servers = {
            "filesystem": [sys.executable, os.path.join(base, "mcp_servers", "filesystem_server.py")],
            "sqlite": [sys.executable, os.path.join(base, "mcp_servers", "sqlite_server.py")],
        }
        for name, cmd in servers.items():
            params = StdioServerParameters(command=cmd[0], args=cmd[1:])
            read, write = await self._stack.enter_async_context(stdio_client(params))
            session = await self._stack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            self.sessions[name] = session

            resp = await session.list_tools()
            for t in resp.tools:
                self.tool_to_session[t.name] = session
                self.tools.append(
                    {
                        "name": t.name,
                        "description": t.description or "",
                        "input_schema": t.inputSchema,
                    }
                )

    async def close(self):
        await self._stack.aclose()

    async def _call_tool(self, name: str, args: dict):
        session = self.tool_to_session[name]
        result = await session.call_tool(name, args)
        parts = []
        for block in result.content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else "null"

    async def ask(self, user_message: str, history: list[dict] | None = None) -> tuple[str, list[dict]]:
        import json
        messages = (history or []) + [{"role": "user", "content": user_message}]

        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in self.tools
        ]

        while True:
            kwargs = {
                "model": MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT,
                    },
                    *messages,
                ],
                "max_tokens": 2048,
            }
            if openai_tools:
                kwargs["tools"] = openai_tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            response_message = response.choices[0].message
            tool_calls = getattr(response_message, "tool_calls", None)

            if tool_calls:
                messages.append(response_message)
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments else {}
                    tool_result = await self._call_tool(tool_name, tool_args)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": str(tool_result),
                        }
                    )
            else:
                final_text = response_message.content or ""
                messages.append({"role": "assistant", "content": final_text})
                return final_text, messages


async def main():
    agent = BudgetAgent()
    await agent.connect()
    try:
        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
            answer, _ = await agent.ask(question)
            print(answer)
        else:
            print("Budget Analysis Agent — type a question (or 'exit').")
            history: list[dict] = []
            while True:
                q = input("\nyou> ").strip()
                if q.lower() in ("exit", "quit"):
                    break
                answer, history = await agent.ask(q, history)
                print(f"\nagent> {answer}")
    finally:
        await agent.close()


if __name__ == "__main__":
    asyncio.run(main())
