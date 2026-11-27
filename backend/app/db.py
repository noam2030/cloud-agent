"""Storage: conversations in Firestore at cloud_agent_users/{user}/conversations/{id}."""

import uuid
from datetime import datetime, timezone

from google.cloud import firestore

from .models import Conversation, ConversationSummary, Message

# On Cloud Run this uses the service's own account. Locally it uses the
# emulator when FIRESTORE_EMULATOR_HOST is set.
client = firestore.AsyncClient()


def _conversations(user_id: str):
    # Each user has their own subcollection, so sorting needs no custom index.
    return client.collection("cloud_agent_users").document(user_id).collection("conversations")


def new_conversation_id() -> str:
    return uuid.uuid4().hex


async def list_conversations(user_id: str) -> list[ConversationSummary]:
    query = _conversations(user_id).order_by("updated_at", direction=firestore.Query.DESCENDING)
    return [ConversationSummary(id=doc.id, **doc.to_dict()) async for doc in query.stream()]


async def get_conversation(user_id: str, conversation_id: str) -> Conversation | None:
    """Return the conversation, or None if this user has no conversation with that id."""
    doc = await _conversations(user_id).document(conversation_id).get()
    if not doc.exists:
        return None
    return Conversation(id=doc.id, **doc.to_dict())


async def save_conversation(
    user_id: str, conversation_id: str, title: str, messages: list[Message]
) -> None:
    """Create or overwrite a conversation."""
    await _conversations(user_id).document(conversation_id).set(
        {
            "title": title,
            "messages": [m.model_dump() for m in messages],
            "updated_at": datetime.now(timezone.utc),
        }
    )
