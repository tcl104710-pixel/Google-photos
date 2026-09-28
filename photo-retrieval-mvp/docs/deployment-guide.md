# Deployment Guide (Google Cloud Run)

This document explains how to deploy the Antigravity Photos MVP backend and frontend to Google Cloud Platform using Cloud Run.

## Prerequisites
- Google Cloud Project with billing enabled.
- Docker & `gcloud` CLI installed locally.
- A managed PostgreSQL instance (e.g. Cloud SQL for PostgreSQL) with `pgvector` enabled.
- A managed Redis instance (e.g. Memorystore for Redis).
- Google OAuth 2.0 Client credentials authorized for your Cloud Run URL.

## 1. Backend Deployment (FastAPI)

1. **Build the Docker Image**:
   ```bash
   cd photo-retrieval-mvp
   gcloud builds submit --tag gcr.io/YOUR_PROJECT_ID/antigravity-backend
   ```

2. **Deploy to Cloud Run**:
   ```bash
   gcloud run deploy antigravity-backend \
     --image gcr.io/YOUR_PROJECT_ID/antigravity-backend \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars="POSTGRES_DSN=...,REDIS_URL=...,GOOGLE_CLIENT_ID=...,GOOGLE_CLIENT_SECRET=...,GROQ_API_KEY=..."
   ```

3. Update the Google OAuth Authorized redirect URIs in the GCP Console to match the deployed Cloud Run URL (e.g., `https://antigravity-backend-xxxxx.run.app/auth/callback`).

## 2. Frontend Deployment (Vite React)

1. **Configure Environment Variables**:
   Update `frontend/.env.production` to point to the backend Cloud Run URL:
   ```env
   VITE_API_URL=https://antigravity-backend-xxxxx.run.app
   ```

2. **Build for Production**:
   ```bash
   cd frontend
   npm run build
   ```

3. **Deploy via Firebase Hosting (Recommended for SPAs)**:
   ```bash
   npm install -g firebase-tools
   firebase init hosting # Select the 'dist' directory as public
   firebase deploy
   ```
   *Alternatively, you can containerize the frontend using Nginx and deploy it to Cloud Run.*

## 3. Post-Deployment Checks
- Verify database migrations ran successfully.
- Verify OAuth login correctly routes to the Google Consent screen and redirects back.
- Ensure CORS in `api/main.py` allows the frontend URL.
