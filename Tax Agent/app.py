from langchain_core.messages import HumanMessage

from Rag.LangGraph_agent import get_agent


agent = get_agent()

messages = []

print("=" * 60)
print("🤖 Tax Planning AI Assistant")
print("Type 'exit' to quit.")
print("=" * 60)

while True:

    question = input("\nYou : ")

    if question.lower() == "exit":
        print("\nGoodbye 👋")
        break

    messages.append(
        HumanMessage(content=question)
    )

    result = agent.invoke(
    {
        "messages": messages
    }
)

print("\n" + "=" * 80)
print("Returned Messages")
print("=" * 80)

for message in result["messages"]:

    print(f"\nType : {type(message).__name__}")

    if hasattr(message, "tool_calls") and message.tool_calls:
        print("Tool Calls:")
        print(message.tool_calls)

    print("Content:")
    print(message.content)

    print("-" * 80)

messages = result["messages"]

print("\nAI :", messages[-1].content)