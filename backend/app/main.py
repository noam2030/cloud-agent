import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Literal

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import firestore
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

# Locally, settings come from backend/.env. On Cloud Run they are real env vars.
load_dotenv()

logger = logging.getLogger(__name__)

# Created once at startup. Raises right away if OPENAI_API_KEY is missing.
llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-5-nano"))

# On Cloud Run this uses the service's own account. Locally it uses the
# emulator when FIRESTORE_EMULATOR_HOST is set.
db = firestore.AsyncClient()

app = FastAPI()

# The frontend (Vercel) and backend (Cloud Run) are on different domains,
# so the browser needs CORS permission to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

SYSTEM_PROMPT = SystemMessage("You are a helpful assistant. Keep answers short.")
MAX_HISTORY = 50  # messages sent to the model, to stay within its context window


class User(BaseModel):
    id: str
    name: str


def current_user() -> User:
    # Everyone is the guest for now. Google login will replace only this
    # function: verify the token, return the real user.
    return User(id="guest", name="Guest")


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime


class Conversation(ConversationSummary):
    messages: list[Message]


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, max_length=64)  # None = new chat
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


def conversations(user: User):
    # Each user has their own subcollection: cloud_agent_users/{user}/conversations
    return db.collection("cloud_agent_users").document(user.id).collection("conversations")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/me")
def me(user: User = Depends(current_user)) -> User:
    return user


@app.get("/api/conversations")
async def list_conversations(user: User = Depends(current_user)) -> list[ConversationSummary]:
    query = conversations(user).order_by("updated_at", direction=firestore.Query.DESCENDING)
    return [ConversationSummary(id=doc.id, **doc.to_dict()) async for doc in query.stream()]


@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: User = Depends(current_user)) -> Conversation:
    doc = await conversations(user).document(conversation_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return Conversation(id=doc.id, **doc.to_dict())


@app.post("/api/chat")
async def chat(req: ChatRequest, user: User = Depends(current_user)) -> ChatResponse:
    # Load the history from the database. The client sends only the new message.
    if req.conversation_id:
        ref = conversations(user).document(req.conversation_id)
        doc = await ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Conversation not found")
        data = doc.to_dict()
        history = [Message(**m) for m in data["messages"]]
        title = data["title"]
    else:
        ref = conversations(user).document(uuid.uuid4().hex)
        history = []
        title = req.message[:80]  # the first question becomes the title

    history.append(Message(role="user", content=req.message))

    # Turn the messages into LangChain message objects.
    lc_messages = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content)
        for m in history[-MAX_HISTORY:]
    ]
    try:
        result = await llm.ainvoke([SYSTEM_PROMPT, *lc_messages])
    except Exception:
        logger.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail="The AI service failed. Try again.")

    history.append(Message(role="assistant", content=result.text))
    # Save only after a successful answer, so a failed call leaves no half-saved turn.
    await ref.set(
        {
            "title": title,
            "messages": [m.model_dump() for m in history],
            "updated_at": datetime.now(timezone.utc),
        }
    )
    return ChatResponse(conversation_id=ref.id, reply=result.text)
