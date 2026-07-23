# CI/CD Setup

## What is already configured

This repository has GitHub Actions CI in `.github/workflows/ci.yml`.

On every pull request and every push to `main`, it will:

1. Install Python dependencies.
2. Run Ruff lint checks.
3. Run the automated test suite.
4. Build the Docker image to confirm the app can be packaged.

On every push to `main`, after all checks pass, GitHub Actions triggers a Render deploy.

## Required GitHub secrets

Add these in GitHub under:

`Settings -> Secrets and variables -> Actions -> New repository secret`

- `MONGODB_URI`
- `DB_NAME`
- `OPENROUTER_API_KEY`
- `RENDER_DEPLOY_HOOK_URL`

The CI workflow uses safe dummy values because the current health test does not call MongoDB or OpenRouter.
Production deployment must use the real values.

`RENDER_DEPLOY_HOOK_URL` comes from the Render service's Settings page.

## Docker

Build locally:

```bash
docker build -t chatbot-api .
```

Run locally:

```bash
docker run --env-file .env -p 8000:8000 chatbot-api
```

The backend starts with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Render setup

1. Create a new Web Service on Render.
2. Connect the GitHub repository.
3. Choose Docker as the runtime.
4. Use the `main` branch.
5. Set Auto-Deploy to off, because GitHub Actions triggers deploys only after CI passes.
6. If Render shows a Docker Command field, set it to:
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
7. Add the production environment variables:
   - `MONGODB_URI`
   - `DB_NAME`
   - `OPENROUTER_API_KEY`
8. Copy the service's Deploy Hook URL from Render Settings.
9. Add it to GitHub Actions secrets as `RENDER_DEPLOY_HOOK_URL`.

The included `render.yaml` can also be used as a Render Blueprint. It defines a Docker web service and marks production secrets with `sync: false`, which means values must be entered in the Render dashboard.

## Deployment flow

1. Push to `main`.
2. GitHub Actions runs tests and linting.
3. GitHub Actions builds the Docker image.
4. If everything passes, GitHub Actions calls Render's deploy hook.
5. Render builds the Docker image from this repo and deploys the backend.

## Frontend

The current frontend is a static `frontend/index.html`. It is not deployed by this setup yet.
If the frontend is deployed later, it will need to call the public backend URL instead of localhost.
