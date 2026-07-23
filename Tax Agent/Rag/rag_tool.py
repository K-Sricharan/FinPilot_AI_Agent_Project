"""
rag_tool.py

RAG Tool for the Tax Planning AI Agent.

This tool searches the vector database for relevant
tax information and returns the retrieved context.
"""

from langchain_core.tools import tool

from Rag.retriever import get_retriever


# Create retriever once
retriever = get_retriever()


@tool
def search_tax_documents(question: str) -> str:
    """
    Search the Income Tax knowledge base for relevant
    information.

    Use this tool whenever the user asks about:

    - Income Tax Act
    - Tax Sections
    - 80C
    - 80D
    - HRA Rules
    - New Tax Regime
    - Old Tax Regime
    - Deductions
    - Exemptions
    - Budget Changes
    - Income Tax Rules

    Args:
        question: User question.

    Returns:
        Relevant tax document context.
    """

    documents = retriever.invoke(question)

    if not documents:
        return "No relevant tax information found."

    context = []

    for index, document in enumerate(documents, start=1):

        source = document.metadata.get(
            "source",
            "Unknown Source"
        )

        page = document.metadata.get(
            "page",
            "Unknown"
        )

        context.append(
            f"""
Document {index}

Source : {source}

Page : {page}

Content:
{document.page_content}
"""
        )

    return "\n\n".join(context)