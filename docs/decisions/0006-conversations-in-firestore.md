# 6. Conversations stored in Firestore

**Context:** The page lists the user's past conversations, so they must survive a refresh and later follow the user across devices once Google login exists.

**Decision:** The backend stores conversations in Firestore at `cloud_agent_users/{user}/conversations/{id}`. The browser sends only `{conversation_id, message}`. The server loads the history, calls the model, and saves the question and answer together. The servers stay stateless; the state lives in the database.

**Why:**
- The server controls what reaches the model, so a client can't fake earlier messages.
- The server decides who the user is (`current_user()`), not the browser. Google login will replace only that function.
- Per-user subcollections sort by `updated_at` without a custom index.
- A failed model call saves nothing, so there are no half-saved turns.

**Alternatives:**
- Browser localStorage: no backend work, but tied to one browser and lost when it's cleared.
- A named Firestore database just for this app: isolated, but outside the free tier.
- Postgres (Cloud SQL): the usual choice for relational data, but an always-on instance costs money.

**Tradeoffs:**
- It shares the project's `(default)` database (free tier), so the runtime account has `datastore.user` on all of it, including other apps' data.
- Until login exists, every visitor is "guest" and sees the same list.
- Each conversation is one document (1 MB limit). The model gets the last 50 messages.
