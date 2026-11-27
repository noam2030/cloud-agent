# Cloud Agent

A "Hello World" page with an AI chat box.

- **Frontend:** React + TypeScript (Vite), deployed to **Vercel**
- **Backend:** FastAPI + LangChain + OpenAI, deployed to **Google Cloud Run**
- **CI/CD:** merging to `main` deploys both

See [docs/architecture.md](docs/architecture.md) for how it fits together and [docs/decisions/](docs/decisions/) for why.

## Run locally

Backend (needs [uv](https://docs.astral.sh/uv/)):

```bash
cd backend
cp .env.example .env          # put your OpenAI key in .env
uv run uvicorn app.main:app --reload --port 8000
```

Frontend (needs Node 20+):

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev                   # http://localhost:5173
```

## Deploy

### Frontend: Vercel (one time)

1. Vercel > Add New Project > import `noam2030/cloud-agent`.
2. Root Directory: `frontend`. Vercel detects Vite.
3. Environment variable: `VITE_API_URL` = the Cloud Run URL (no trailing slash).

After that, every push to `main` deploys, and every PR gets a preview URL.

### Backend: Google Cloud Run (one time)

```bash
PROJECT_ID=your-project-id
REGION=us-central1
REPO=noam2030/cloud-agent
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')
SA=github-deployer@$PROJECT_ID.iam.gserviceaccount.com
RUNTIME_SA=$PROJECT_NUMBER-compute@developer.gserviceaccount.com
gcloud config set project $PROJECT_ID

# 1. APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com

# 2. OpenAI key in Secret Manager, readable by the Cloud Run runtime account
printf %s "sk-..." | gcloud secrets create openai-api-key --data-file=-
gcloud secrets add-iam-policy-binding openai-api-key \
  --member=serviceAccount:$RUNTIME_SA --role=roles/secretmanager.secretAccessor

# 3. Service account that GitHub Actions acts as
gcloud iam service-accounts create github-deployer
for role in run.sourceDeveloper iam.serviceAccountUser serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member=serviceAccount:$SA --role=roles/$role
done
# Source deploys build with the default compute account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member=serviceAccount:$RUNTIME_SA --role=roles/run.builder

# 4. Workload Identity Federation: trust GitHub tokens from this repo only
gcloud iam workload-identity-pools create github --location=global
gcloud iam workload-identity-pools providers create-oidc cloud-agent \
  --location=global --workload-identity-pool=github \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository \
  --attribute-condition="assertion.repository=='$REPO'"
gcloud iam service-accounts add-iam-policy-binding $SA \
  --role=roles/iam.workloadIdentityUser \
  --member=principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/attribute.repository/$REPO

# 5. GitHub repo variables the workflow reads (not secrets; none of these are sensitive)
gh variable set GCP_REGION --body $REGION
gh variable set DEPLOY_SA --body $SA
gh variable set WIF_PROVIDER --body projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github/providers/cloud-agent
gh variable set ALLOWED_ORIGINS --body https://your-app.vercel.app
```

After that, every push to `main` that touches `backend/` runs [.github/workflows/deploy-backend.yml](.github/workflows/deploy-backend.yml). You can also start it by hand from the Actions tab.
