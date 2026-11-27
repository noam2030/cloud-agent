"""HTTP endpoints (the controller). Validates input, calls db and agent, shapes responses."""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from . import agent, db
from .models import Conversation, ConversationSummary, Message, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


def current_user() -> User:
    # Everyone is the guest for now. Google login will replace only this
    # function: verify the token, return the real user.
    return User(id="guest", name="Guest")


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, max_length=64)  # None = new chat
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    conversation_id: str
    reply: str


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/me")
def me(user: User = Depends(current_user)) -> User:
    return user


@router.get("/conversations")
async def list_conversations(user: User = Depends(current_user)) -> list[ConversationSummary]:
    return await db.list_conversations(user.id)


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, user: User = Depends(current_user)) -> Conversation:
    conversation = await db.get_conversation(user.id, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.post("/chat")
async def chat(req: ChatRequest, user: User = Depends(current_user)) -> ChatResponse:
    # Load the history from the database. The client sends only the new message.
    if req.conversation_id:
        conversation = await db.get_conversation(user.id, req.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        conversation_id, title, history = conversation.id, conversation.title, conversation.messages
    else:
        conversation_id = db.new_conversation_id()
        title = req.message[:80]  # the first question becomes the title
        history = []

    history.append(Message(role="user", content=req.message))
    try:
        answer = await agent.reply(history)
    except Exception:
        logger.exception("OpenAI call failed")
        raise HTTPException(status_code=502, detail="The AI service failed. Try again.")

    history.append(Message(role="assistant", content=answer))
    # Save only after a successful answer, so a failed call leaves no half-saved turn.
    await db.save_conversation(user.id, conversation_id, title, history)
    return ChatResponse(conversation_id=conversation_id, reply=answer)
