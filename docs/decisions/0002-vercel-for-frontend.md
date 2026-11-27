# 2. Vercel for the frontend

**Context:** The React app builds to static files (HTML/JS/CSS).

**Decision:** Host it on Vercel through its GitHub integration.

**Why:** Push-to-deploy with no workflow file, preview URLs for every PR, a global CDN, and a free tier.

**Alternatives:** Firebase Hosting or Cloud Storage + CDN (keeps everything in Google but needs more setup), Netlify (similar to Vercel).

**Tradeoff:** Two providers. The frontend and backend live on different domains, which means CORS (see ADR 4).
