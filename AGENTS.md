# Agent instructions

## Layout
- `frontend/`: React + TypeScript (Vite). Page in `src/App.tsx`, chat window in `src/Chat.tsx`, backend calls in `src/api.ts`.
- `backend/app/`: FastAPI, in layers. Dependencies point one way: `main` -> `api` -> `db`, `agent` -> `models`.
  - `main.py`: builds the app (CORS, routes). Entry point for uvicorn.
  - `api.py`: HTTP endpoints (controller). Validation, status codes, current user.
  - `db.py`: Firestore reads and writes. No HTTP or AI code.
  - `agent.py`: LangChain + OpenAI. No HTTP or database code.
  - `models.py`: shared Pydantic shapes (User, Message, Conversation).
- `docs/`: architecture and decision records (ADRs).

## Commands
- Firestore emulator: `gcloud emulators firestore start --host-port=localhost:8089`
- Backend: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`, `npm run build`, `npm run lint`
- Backend image: `docker build -t cloud-agent-backend backend`

## Rules
- Keep it simple. This is a learning project; every part should be easy to explain.
- Never commit `.env`, `.env.local`, or API keys. The OpenAI key lives in Secret Manager as `cloud-agent-openai-key`.
- Conversations live in Firestore, owned by the backend. The browser sends only the new message. Never store them in the browser.
- The user comes from `current_user()` in the backend, never from the client.
- A new architectural choice gets an ADR in `docs/decisions/`.
- Run `npm run build` and `npm run lint` before finishing frontend changes.
