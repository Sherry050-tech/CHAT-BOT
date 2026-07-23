# CI/CD Setup

## What is already configured

This repository has GitHub Actions CI in `.github/workflows/ci.yml`.

On every pull request and every push to `main`, it will:

1. Install Python dependencies.
2. Run Ruff lint checks.
3. Run the automated test suite.
4. Build the Docker image to confirm the app can be packaged.

## Required GitHub secrets

Add these in GitHub under:

`Settings -> Secrets and variables -> Actions -> New repository secret`

- `MONGODB_URI`
- `DB_NAME`
- `OPENROUTER_API_KEY`

The CI workflow uses safe dummy values because the current health test does not call MongoDB or OpenRouter.
Production deployment must use the real values.

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

## CD provider still needed

Actual deployment needs the hosting provider your teammate chooses, such as Render, Railway, Fly.io, Azure, AWS, or a VPS.

Once the provider is known, add one provider-specific workflow or connect the provider directly to GitHub. The deployment should run automatically after CI passes on `main`.

Recommended simple options:

- Render or Railway for the fastest setup.
- AWS/Azure if the project needs a more production-style cloud setup.

## Frontend

The current frontend is a static `frontend/index.html`. It is not deployed by this setup yet.
If the frontend is deployed later, it will need to call the public backend URL instead of localhost.
