# Architecture

```
Browser ──> Vercel: static React app (HTML/JS/CSS)
   │
   └──> Cloud Run: FastAPI container ──> OpenAI API
            ▲         │          ▲
     Secret Manager   │     GitHub Actions
     (OPENAI_API_KEY) │     (deploys on merge to main)
                      └──> Firestore (conversations)
```

## Page load

1. The browser gets the static app from Vercel.
2. It calls `GET /api/me` (shows "Hello Guest") and `GET /api/conversations` (the list). The backend decides who the user is in `current_user()`; for now everyone is the guest.

## A chat request, step by step

1. The user types a question. `Chat.tsx` shows it right away.
2. The browser sends `POST {VITE_API_URL}/api/chat` with only `{conversation_id, message}`. `conversation_id` is empty for a new chat.
3. The page comes from Vercel and the API from Cloud Run, which are different origins, so the browser first sends a CORS preflight (`OPTIONS`). FastAPI's `CORSMiddleware` answers it if the origin is in `ALLOWED_ORIGINS`.
4. Pydantic validates the body (length limits) and rejects bad input with 422.
5. The backend loads the conversation from Firestore (404 if it isn't this user's) and appends the new question.
6. The last 50 messages become LangChain `HumanMessage`/`AIMessage` objects, a `SystemMessage` goes first, and `ChatOpenAI.ainvoke` calls OpenAI.
7. The backend saves the whole conversation back to Firestore, with the first question as its title, and returns `{conversation_id, reply}`. If OpenAI fails, it saves nothing and returns 502.
8. The browser shows the reply and refreshes the list.

Clicking a conversation in the list calls `GET /api/conversations/{id}` and opens it in the chat window.

## Deploy flow

- **Frontend:** merging to `main` triggers Vercel's GitHub integration, which runs `npm run build` and serves `dist/` from its CDN.
- **Backend:** merging to `main` with changes in `backend/` triggers a GitHub Actions run. It gets a GitHub OIDC token, exchanges it for a Google token (Workload Identity Federation), runs Cloud Build on the Dockerfile, deploys a new Cloud Run revision, and checks `/api/health`.
