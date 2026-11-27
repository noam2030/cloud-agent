# 1. Cloud Run for the backend

**Context:** The FastAPI app needs to run in Google Cloud, cheaply, with little ops work.

**Decision:** Package it as a Docker container and run it on Cloud Run.

**Why:** Cloud Run runs any container, scales to zero when idle (near-zero cost for a demo), and handles HTTPS. It also supports deploys from source, so Cloud Build builds the image and there's no registry to manage by hand.

**Alternatives:** App Engine (older, less flexible), GKE/Kubernetes (too much ops for one service), a VM (you manage the OS and scaling).

**Tradeoff:** Cold starts. After idle time, the first request waits a few seconds.
