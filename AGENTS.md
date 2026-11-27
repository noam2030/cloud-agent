# Agent instructions

## Layout
- `frontend/`: React + TypeScript (Vite). Chat UI is in `src/Chat.tsx`.
- `backend/`: FastAPI. Everything is in `app/main.py`.
- `docs/`: architecture and decision records (ADRs).

## Commands
- Backend: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`, `npm run build`, `npm run lint`
- Backend image: `docker build -t cloud-agent-backend backend`

## Rules
- Keep it simple. This is a learning project; every part should be easy to explain.
- Never commit `.env`, `.env.local`, or API keys. The OpenAI key lives in Secret Manager as `cloud-agent-openai-key`.
- The backend is stateless: the frontend sends the full chat history on every request.
- A new architectural choice gets an ADR in `docs/decisions/`.
- Run `npm run build` and `npm run lint` before finishing frontend changes.
