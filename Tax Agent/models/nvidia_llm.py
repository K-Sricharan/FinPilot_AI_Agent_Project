from dotenv import load_dotenv
import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv()

api_key = os.getenv("NVIDIA_API_KEY")

llm = ChatNVIDIA(
    model="meta/llama-3.3-70b-instruct",
    api_key=api_key,
    temperature=0.1,
    max_tokens=1024
)
