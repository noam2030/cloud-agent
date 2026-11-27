"""The AI part: turns a conversation into a reply, using tools from an MCP server."""

import asyncio
import logging
import os

import google.auth.transport.requests
import google.oauth2.id_token
from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI

from .models import Message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a helpful assistant. Keep answers short. Use tools when they help."
MAX_HISTORY = 50  # messages sent to the model, to stay within its context window

# Base URL of the MCP server, e.g. https://cloud-mcp-....run.app. Unset = no tools.
MCP_URL = os.getenv("MCP_URL")

# Created once at startup. Raises right away if OPENAI_API_KEY is missing.
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-nano"))


async def _mcp_headers() -> dict[str, str]:
    # The MCP service on Cloud Run is private. A Google ID token for it proves
    # this backend's identity (cloud-agent-runtime has run.invoker on it).
    # Local http:// servers need no token.
    if not MCP_URL.startswith("https://"):
        return {}
    # fetch_id_token is a blocking HTTP call, so run it off the event loop.
    token = await asyncio.to_thread(
        google.oauth2.id_token.fetch_id_token, google.auth.transport.requests.Request(), MCP_URL
    )
    return {"Authorization": f"Bearer {token}"}


async def _load_tools():
    """Fetch the tool list from the MCP server. If it's down, chat still works without tools."""
    if not MCP_URL:
        return []
    try:
        client = MultiServerMCPClient(
            {"cloud-mcp": {"transport": "streamable_http", "url": f"{MCP_URL}/mcp", "headers": await _mcp_headers()}}
        )
        return await client.get_tools()
    except Exception:
        logger.exception("Could not load MCP tools; answering without them")
        return []


async def reply(history: list[Message]) -> str:
    """Return the model's answer to the last message. Raises if OpenAI fails."""
    # Turn our messages into LangChain message objects.
    lc_messages = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in history[-MAX_HISTORY:]
    ]
    # The agent loops: the model may call tools, read their results, then answer.
    agent = create_agent(llm, await _load_tools(), system_prompt=SYSTEM_PROMPT)
    result = await agent.ainvoke({"messages": lc_messages})
    return result["messages"][-1].text
