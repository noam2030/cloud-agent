"""Data shapes shared by the API, the database, and the agent."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class User(BaseModel):
    id: str
    name: str


class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationSummary(BaseModel):
    id: str
    title: str
    updated_at: datetime


class Conversation(ConversationSummary):
    messages: list[Message]
