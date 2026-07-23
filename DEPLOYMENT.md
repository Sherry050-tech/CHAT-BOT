# CI/CD Setup

## What is already configured

This repository has GitHub Actions CI in `.github/workflows/ci.yml`.

On every pull request and every push to `main`, it will:

1. Install Python dependencies.
2. Run Ruff lint checks.
3. Run the automated test suite.
4. Build the Docker image to confirm the app can be packaged.

On every push to `main`, after all checks pass, GitHub Actions deploys to Railway.

## Required GitHub secrets

Add these in GitHub under:

`Settings -> Secrets and variables -> Actions -> New repository secret`

- `MONGODB_URI`
- `DB_NAME`
- `OPENROUTER_API_KEY`
- `GROQ_API_KEY`
- `RAILWAY_TOKEN`
- `RAILWAY_SERVICE_ID`

The CI workflow uses safe dummy values because the current health test does not call MongoDB or OpenRouter.
Production deployment must use the real values.

`RAILWAY_TOKEN` comes from the Railway project settings.
`RAILWAY_SERVICE_ID` is the target Railway service ID.

## Docker

Build locally:

```bash
docker build -t chatbot-api .
```

Run locally:

```bash
docker run --env-file .env -p 8000:8000 chatbot-api
```

The Docker image uses `requirements-render.txt`, which excludes `sentence-transformers`
so the API can run on Render's free 512 MiB instance. The full local development
dependencies remain in `requirements.txt`.

Because of that memory limit, document upload/RAG embeddings need either:

- a larger Render instance, or
- a different hosted embedding provider.

The backend starts with:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Railway setup

1. Create a new Railway project.
2. Create a new service from this GitHub repository.
3. Railway will use the `Dockerfile` in the repository.
4. Set the start command if Railway asks for one:
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the production environment variables:
   - `MONGODB_URI`
   - `DB_NAME`
   - `OPENROUTER_API_KEY`
   - `GROQ_API_KEY`
6. Create a Railway project token.
7. Add the project token to GitHub Actions secrets as `RAILWAY_TOKEN`.
8. Copy the Railway service ID.
9. Add the service ID to GitHub Actions secrets as `RAILWAY_SERVICE_ID`.

## Deployment flow

1. Push to `main`.
2. GitHub Actions runs tests and linting.
3. GitHub Actions builds the Docker image.
4. If everything passes, GitHub Actions runs `railway up --ci`.
5. Railway builds the Docker image from this repo and deploys the backend.

## Frontend

The current frontend is a static `frontend/index.html`. It is not deployed by this setup yet.
If the frontend is deployed later, it will need to call the public backend URL instead of localhost.
