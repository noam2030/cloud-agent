# 5. Stateless chat API

**Status:** Superseded by [ADR 6](0006-conversations-in-firestore.md).

**Context:** Follow-up questions need the earlier conversation.

**Decision:** The frontend keeps the history and sends all of it on every request. The backend stores nothing.

**Why:** No database or session store. Any Cloud Run instance can serve any request, so scaling is free.

**Alternatives:** Server-side sessions in Redis/Firestore (needed for history across devices, auth, or long chats).

**Tradeoff:** Requests grow with the conversation, and history is lost on page refresh. The API caps it at 50 messages.
