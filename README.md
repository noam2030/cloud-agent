# Cloud Agent

A "Hello World" page with an AI chat box.

- **Frontend:** React + TypeScript (Vite), deployed to **Vercel**
- **Backend:** FastAPI + LangChain + OpenAI, deployed to **Google Cloud Run**
- **CI/CD:** merging to `main` deploys both

See [docs/architecture.md](docs/architecture.md) for how it fits together and [docs/decisions/](docs/decisions/) for why.

## Run locally

Firestore emulator (needs Java), so local runs never touch the real database:

```bash
gcloud components install cloud-firestore-emulator
gcloud emulators firestore start --host-port=localhost:8089
```

Backend (needs [uv](https://docs.astral.sh/uv/)), in another terminal:

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

Three service accounts, each with only what it needs:

| Account | Used by | Can do |
|---|---|---|
| `cloud-agent-deployer` | GitHub Actions (via WIF) | start source deploys, act as the two below |
| `cloud-agent-builder` | Cloud Build | build the image (`run.builder`) |
| `cloud-agent-runtime` | the running container | read the OpenAI key secret, read/write Firestore |

```bash
P=your-project-id
N=$(gcloud projects describe $P --format='value(projectNumber)')
REPO=noam2030/cloud-agent
DEPLOY_SA=cloud-agent-deployer@$P.iam.gserviceaccount.com
BUILD_SA=cloud-agent-builder@$P.iam.gserviceaccount.com
RUN_SA=cloud-agent-runtime@$P.iam.gserviceaccount.com

# 1. APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com \
  artifactregistry.googleapis.com secretmanager.googleapis.com iamcredentials.googleapis.com

# 2. Service accounts and roles
for a in cloud-agent-deployer cloud-agent-builder cloud-agent-runtime; do gcloud iam service-accounts create $a; done
for r in run.sourceDeveloper serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding $P --member=serviceAccount:$DEPLOY_SA --role=roles/$r
done
gcloud projects add-iam-policy-binding $P --member=serviceAccount:$BUILD_SA --role=roles/run.builder
for sa in $BUILD_SA $RUN_SA; do
  gcloud iam service-accounts add-iam-policy-binding $sa \
    --member=serviceAccount:$DEPLOY_SA --role=roles/iam.serviceAccountUser
done

# 3. OpenAI key in Secret Manager, readable only by the runtime account
gcloud secrets create cloud-agent-openai-key
printf %s "sk-..." | gcloud secrets versions add cloud-agent-openai-key --data-file=-
gcloud secrets add-iam-policy-binding cloud-agent-openai-key \
  --member=serviceAccount:$RUN_SA --role=roles/secretmanager.secretAccessor
# Conversations live in the project's (default) Firestore database
gcloud projects add-iam-policy-binding $P --member=serviceAccount:$RUN_SA --role=roles/datastore.user

# 4. Workload Identity Federation: trust GitHub tokens from this repo only
gcloud iam workload-identity-pools create github --location=global   # skip if it exists
gcloud iam workload-identity-pools providers create-oidc cloud-agent \
  --location=global --workload-identity-pool=github \
  --issuer-uri=https://token.actions.githubusercontent.com \
  --attribute-mapping=google.subject=assertion.sub,attribute.repository=assertion.repository \
  --attribute-condition="assertion.repository=='$REPO'"
gcloud iam service-accounts add-iam-policy-binding $DEPLOY_SA --role=roles/iam.workloadIdentityUser \
  --member=principalSet://iam.googleapis.com/projects/$N/locations/global/workloadIdentityPools/github/attribute.repository/$REPO

# 5. GitHub repo variables the workflow reads (none are secret)
gh variable set GCP_PROJECT_ID --body $P
gh variable set GCP_REGION --body us-central1
gh variable set DEPLOY_SA --body $DEPLOY_SA
gh variable set BUILD_SA --body $BUILD_SA
gh variable set RUNTIME_SA --body $RUN_SA
gh variable set WIF_PROVIDER --body projects/$N/locations/global/workloadIdentityPools/github/providers/cloud-agent
gh variable set ALLOWED_ORIGINS --body https://your-app.vercel.app   # one origin, no commas
```

```bash
# 6. After the first deploy creates the service, make it public (once).
#    Kept out of the pipeline so the deployer never needs setIamPolicy.
gcloud run services update cloud-agent-backend --region us-central1 --no-invoker-iam-check
```

After that, every push to `main` that touches `backend/` runs [.github/workflows/deploy-backend.yml](.github/workflows/deploy-backend.yml). You can also start it by hand from the Actions tab.
