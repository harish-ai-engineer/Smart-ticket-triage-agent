"""Environment loading, LLM construction, and Langfuse callback handler setup."""

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langfuse.callback import CallbackHandler

from tools import TOOLS

load_dotenv()

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
LANGFUSE_PUBLIC_KEY: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY: str | None = os.getenv("LANGFUSE_SECRET_KEY")
LANGFUSE_HOST: str = os.getenv("LANGFUSE_HOST", "http://localhost:3000")


def get_llm() -> ChatOpenAI:
    """Build the shared gpt-4o chat model used by both LLM call sites."""
    return ChatOpenAI(model="gpt-4o", temperature=0, api_key=OPENAI_API_KEY)


def get_classifier_llm() -> ChatOpenAI:
    """Build the classifier LLM with tools bound, in case future intents require lookups."""
    return get_llm().bind_tools(TOOLS)


def get_langfuse_handler() -> CallbackHandler:
    """Build the Langfuse/AgentGuard callback handler used to trace every LLM call."""
    return CallbackHandler(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST,
    )
