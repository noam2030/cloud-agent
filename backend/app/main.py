import logging
import os
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Locally, settings come from backend/.env. On Cloud Run they are real env vars.
load_dotenv()

logger = logging.getLogger(__name__)

# Created once at startup. Raises right away if OPENAI_API_KEY is missing.
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-nano"))

app = FastAPI()

# The frontend (Vercel) and backend (Cloud Run) are on different domains,
# so the browser needs CORS permission to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    messages: list[Message] = Field(min_length=1, max_length=50)


class ChatResponse(BaseModel):
    reply: str


SYSTEM_PROMPT = SystemMessage("You are a helpful assistant. Keep answers short.")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    # Turn the JSON messages into LangChain message objects.
    history = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in req.messages
    ]
    try:
        result = await llm.ainvoke([SYSTEM_PROMPT, *history])
    except Exception:
        logger.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail="The AI service failed. Try again.")
    return ChatResponse(reply=result.text)
