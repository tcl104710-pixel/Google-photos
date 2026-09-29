# Deployment Plan: Vercel (Frontend & Backend)

This guide outlines the steps to deploy both the **React (Vite) Frontend** and the **FastAPI Backend** for the Google Photos Retrieval MVP on **Vercel**. 

Vercel natively supports React frontends and can host FastAPI backends using Python Serverless Functions.

---

## 1. Project Restructuring for Vercel

Vercel requires a specific configuration (`vercel.json`) at the root of the repository to properly route traffic between the frontend and the backend.

### A. Create `vercel.json` at the root
Create a file named `vercel.json` in the root of your repository (where `.gitignore` is):

```json
{
  "version": 2,
  "builds": [
    {
      "src": "photo-retrieval-mvp/frontend/package.json",
      "use": "@vercel/vite"
    },
    {
      "src": "photo-retrieval-mvp/api/main.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "photo-retrieval-mvp/api/main.py"
    },
    {
      "src": "/docs",
      "dest": "photo-retrieval-mvp/api/main.py"
    },
    {
      "src": "/openapi.json",
      "dest": "photo-retrieval-mvp/api/main.py"
    },
    {
      "src": "/(.*)",
      "dest": "photo-retrieval-mvp/frontend/$1"
    }
  ]
}
```

### B. Update the FastAPI `requirements.txt`
Vercel's Python runtime requires a `requirements.txt` file in the same directory as your main API file. Ensure `photo-retrieval-mvp/api/requirements.txt` exists and contains your production dependencies:

```text
fastapi==0.115.0
pydantic==2.9.2
groq==0.11.0
# Add your other dependencies here
```

> **⚠️ CRITICAL WARNING:** Vercel serverless functions have a **250MB size limit**. If your project uses local AI models (like downloading `BAAI/bge-m3` via `FlagEmbedding`) or massive libraries (like heavy PyTorch installations for FAISS), the deployment **will fail**. For a production Vercel deployment, you must:
> 1. Use an external Embedding API (like OpenAI or Cohere) instead of local models.
> 2. Use a managed Vector Database (like Pinecone or Supabase pgvector) instead of local FAISS files.

---

## 2. Preparing the Frontend

### A. Environment Variables
Update the Vite configuration to ensure API calls are routed correctly. By default, Vite expects the backend to be on a separate port locally, but on Vercel, it will share the same domain under the `/api` route.

In `photo-retrieval-mvp/frontend/src/api/client.js`, update the base URL dynamically:
```javascript
const BASE_URL = import.meta.env.PROD ? '/api' : 'http://127.0.0.1:8000';
```

---

## 3. Deployment Steps via Vercel Dashboard

1. **Push to GitHub:** Ensure all your code, including `vercel.json` and `requirements.txt`, is pushed to your `main` branch.
2. **Import Project:** Go to [vercel.com/new](https://vercel.com/new) and import your `Google-photos` GitHub repository.
3. **Configure Project:**
   * **Framework Preset:** Leave as `Other` (the `vercel.json` will override this).
   * **Root Directory:** Leave as the root `./` (do NOT select `frontend`).
4. **Environment Variables:** Open the **Environment Variables** tab and paste all the keys from your local `.env` file. *Do not forget:*
   * `GROQ_API_KEY`
   * `GOOGLE_CLIENT_ID`
   * `GOOGLE_CLIENT_SECRET`
5. **Deploy:** Click the **Deploy** button.

---

## 4. Post-Deployment: Google OAuth Setup

Once Vercel gives you a production URL (e.g., `https://google-photos-mvp.vercel.app`), you must update your Google Cloud Console:
1. Go to **APIs & Services > Credentials**.
2. Edit your OAuth 2.0 Client ID.
3. Add your new Vercel URL to **Authorized JavaScript origins** (e.g., `https://google-photos-mvp.vercel.app`).
4. Add the callback URL to **Authorized redirect URIs** (e.g., `https://google-photos-mvp.vercel.app/auth/callback`).

---

## 5. Potential Limitations & Fixes

* **Serverless Cold Starts:** FastAPI running on Vercel is serverless. The first API request after a period of inactivity may take a few seconds to load.
* **10-Second Timeout:** Free-tier Vercel functions timeout after 10 seconds (Pro tier is 60s). If your Groq LLM queries take longer than 10 seconds to generate a query or rank photos, the request will fail. *Fix: Use Groq's streaming API or upgrade to Vercel Pro.*
* **Local Storage:** Serverless functions cannot write to the local file system. If your backend attempts to save local JSON files or FAISS indices, it will throw an error. *Fix: Use a cloud database (PostgreSQL, Redis).*
