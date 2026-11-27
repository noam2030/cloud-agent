"""Entry point: builds the FastAPI app. Run with `uvicorn app.main:app`."""

import os

from dotenv import load_dotenv

# Load backend/.env before the other modules read env vars at import time.
# On Cloud Run the settings are real env vars and there is no .env file.
load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402

from .api import router  # noqa: E402

app = FastAPI()

# The frontend (Vercel) and backend (Cloud Run) are on different domains,
# so the browser needs CORS permission to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)
