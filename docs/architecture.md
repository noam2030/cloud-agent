# Architecture

```
Browser ──> Vercel: static React app (HTML/JS/CSS)
   │
   └──> Cloud Run: FastAPI container ──> OpenAI API
            ▲                    ▲
     Secret Manager         GitHub Actions
     (OPENAI_API_KEY)       (deploys on merge to main)
```

## A chat request, step by step

1. The user types a question. `Chat.tsx` adds it to the message list.
2. The browser sends `POST {VITE_API_URL}/api/chat` with the **whole** conversation.
3. The page comes from Vercel and the API from Cloud Run, which are different origins, so the browser first sends a CORS preflight (`OPTIONS`). FastAPI's `CORSMiddleware` answers it if the origin is in `ALLOWED_ORIGINS`.
4. Pydantic validates the body (role is `user` or `assistant`, length limits) and rejects bad input with 422.
5. The messages become LangChain `HumanMessage`/`AIMessage` objects, a `SystemMessage` goes first, and `ChatOpenAI.ainvoke` calls OpenAI.
6. The reply goes back as `{reply}`. If OpenAI fails, the API returns 502 with a generic message.

## Deploy flow

- **Frontend:** merging to `main` triggers Vercel's GitHub integration, which runs `npm run build` and serves `dist/` from its CDN.
- **Backend:** merging to `main` with changes in `backend/` triggers a GitHub Actions run. It gets a GitHub OIDC token, exchanges it for a Google token (Workload Identity Federation), runs Cloud Build on the Dockerfile, deploys a new Cloud Run revision, and checks `/api/health`.
