"""The AI part: turns a conversation into a reply using LangChain and OpenAI."""

import os

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from .models import Message

SYSTEM_PROMPT = SystemMessage("You are a helpful assistant. Keep answers short.")
MAX_HISTORY = 50  # messages sent to the model, to stay within its context window

# Created once at startup. Raises right away if OPENAI_API_KEY is missing.
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-nano"))


async def reply(history: list[Message]) -> str:
    """Return the model's answer to the last message. Raises if OpenAI fails."""
    # Turn our messages into LangChain message objects.
    lc_messages = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in history[-MAX_HISTORY:]
    ]
    result = await llm.ainvoke([SYSTEM_PROMPT, *lc_messages])
    return result.text
