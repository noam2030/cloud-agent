# 3. GitHub Actions + Workload Identity Federation for backend deploys

**Context:** Merging to `main` should deploy the backend. GitHub needs permission to deploy to Google Cloud.

**Decision:** A GitHub Actions workflow in the repo. It authenticates with Workload Identity Federation (WIF), not a service account JSON key.

**Why:** The pipeline is code in the repo, so it's reviewed and versioned like everything else. With WIF, GitHub issues a short-lived OIDC token, and Google trusts it only for this repo. There's no long-lived key to leak or rotate.

**Alternatives:** A Cloud Build trigger connected to GitHub (fewer parts, but the pipeline is configured in the Google console). A JSON key stored in GitHub Secrets (simple, but a permanent credential).

**Tradeoff:** WIF needs a one-time setup (pool, provider, IAM binding).

**Least privilege:** Three service accounts. The deployer (what GitHub becomes) can only start source deploys. The builder can only build. The runtime account can only read the OpenAI key. The project default compute account has `editor`, so nothing uses it.
