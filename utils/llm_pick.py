from langchain_groq import ChatGroq
import os
from dotenv import load_dotenv

load_dotenv()


def pick_llm(level: str):

    if level.lower() == "low":
        model = "openai/gpt-oss-20b"

    elif level.lower() == "medium":
        model = "openai/gpt-oss-120b"

    elif level.lower() == "high":
        model = "openai/gpt-oss-120b"

    else:
        raise ValueError(f"Unsupported level: {level}")

    return ChatGroq(
        model=model,
        api_key=os.getenv("GROQ_API_KEY")
    )