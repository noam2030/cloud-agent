# 4. CORS instead of a proxy

**Context:** The browser blocks calls from one origin (Vercel) to another (Cloud Run) unless the server allows them.

**Decision:** FastAPI's `CORSMiddleware` allows the origins listed in `ALLOWED_ORIGINS`. Dev uses the same setup (`localhost:5173` -> `localhost:8000`).

**Why:** One mechanism for dev and prod, so local runs behave like the deployed app.

**Alternatives:** A Vite dev proxy (dev only), or Vercel rewrites so the browser only sees one domain (no CORS needed, but it hides the backend URL behind another layer).

**Tradeoff:** The origin list must be kept in sync with the Vercel URL.
