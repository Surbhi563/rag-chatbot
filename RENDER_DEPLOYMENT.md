# Render Deployment Guide

Complete guide to deploy the RAG Chatbot to Render.

## Overview

You'll deploy 3 services on Render:
1. **Backend** - FastAPI application (Python)
2. **Frontend** - React application (Node.js)
3. **Ollama** (Optional) - LLM service for running models

## Prerequisites

- GitHub repository with your code
- Render account (sign up at [render.com](https://render.com))
- Ollama account (or use OpenAI API as alternative)

---

## Step 1: Deploy Backend

### 1.1 Create New Web Service

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository
4. Select the repository containing your code

### 1.2 Configure Backend Service

**Basic Settings:**
- **Name:** `rag-chatbot-backend` (or your preferred name)
- **Environment:** `Python 3`
- **Region:** Choose closest to you
- **Branch:** `main` (or your main branch)
- **Root Directory:** `backend`

**Build & Start:**
- **Build Command:** 
  ```bash
  pip install -r requirements.txt
  ```
  Or if using `uv`:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync --no-dev
  ```
- **Start Command:**
  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```
  Or if using `uv`:
  ```bash
  uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

### 1.3 Set Environment Variables

In Render dashboard, go to **Environment** tab and add:

```
# Core Configuration
ENV=prod
PORT=10000
LOG_LEVEL=INFO
LOG_FORMAT=json

# Storage (using Render's filesystem - data persists during service uptime)
VECTOR_DB_PATH=/opt/render/project/src/chroma_db
LOCAL_BUCKET_DIR=/opt/render/project/src/rag-documents

# LLM Configuration - Option A: Using Ollama (requires separate Ollama service)
LLM_BASE_URL=https://your-ollama-service.onrender.com
LLM_DEFAULT_MODEL=llama3.2:3b
LLM_DEFAULT_TEMPERATURE=0.1
LLM_DEFAULT_MAX_TOKENS=2000

# LLM Configuration - Option B: Using OpenAI (alternative)
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_API_KEY=sk-your-openai-api-key
# LLM_DEFAULT_MODEL=gpt-3.5-turbo
# LLM_DEFAULT_TEMPERATURE=0.1
# LLM_DEFAULT_MAX_TOKENS=2000

# App Metadata
APP_NAME=rag-chatbot
APP_VERSION=1.0.0

# Python Settings
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

**Important Notes:**
- Replace `your-ollama-service.onrender.com` with your actual Ollama service URL after deploying it
- For OpenAI, uncomment those lines and add your API key
- `PORT` is automatically set by Render, but we include it for clarity

### 1.4 Deploy

Click **"Create Web Service"** and wait for deployment to complete. Note down your backend URL (e.g., `https://rag-chatbot-backend-xyz.onrender.com`).

---

## Step 2: Deploy Ollama (Optional - Only if using Ollama)

If you want to use Ollama instead of OpenAI:

### 2.1 Create New Web Service

1. Click **"New +"** → **"Web Service"**
2. Select same repository

### 2.2 Configure Ollama Service

**Basic Settings:**
- **Name:** `rag-chatbot-ollama`
- **Environment:** `Docker`
- **Root Directory:** `ollama`

**Docker Settings:**
- **Dockerfile Path:** `Dockerfile.render` (or `Dockerfile` if that doesn't exist)

**Environment Variables:**
```
OLLAMA_HOST=0.0.0.0:$PORT
PORT=11434
```

### 2.3 Deploy and Setup Model

1. Deploy the service
2. Once deployed, go to **Shell** tab in Render dashboard
3. Run:
   ```bash
   ollama pull llama3.2:3b
   ```
   This downloads the model (may take several minutes)

4. Note your Ollama service URL (e.g., `https://rag-chatbot-ollama-abc.onrender.com`)

5. Update backend environment variable:
   - Go to backend service → Environment
   - Update `LLM_BASE_URL` to your Ollama service URL

**Note:** Free tier on Render will spin down after inactivity. For production, consider using OpenAI API or upgrade to a paid plan.

---

## Step 3: Deploy Frontend

### Option A: Deploy on Render

### 3.1 Create New Static Site

1. Click **"New +"** → **"Static Site"**
2. Connect your GitHub repository

### 3.2 Configure Frontend

**Basic Settings:**
- **Name:** `rag-chatbot-frontend`
- **Root Directory:** `frontend`
- **Build Command:**
  ```bash
  npm install && REACT_APP_API_URL=https://your-backend-url.onrender.com npm run build
  ```
  Replace `your-backend-url.onrender.com` with your actual backend URL from Step 1

- **Publish Directory:** `build`

**Environment Variables:**
```
REACT_APP_API_URL=https://your-backend-url.onrender.com
```
Replace with your actual backend URL.

### 3.3 Deploy

Click **"Create Static Site"** and wait for deployment.

---

### Option B: Deploy on Vercel (Recommended for Frontend)

Vercel is free and faster for React apps:

1. Go to [vercel.com](https://vercel.com)
2. Sign up with GitHub
3. Click **"New Project"**
4. Import your repository
5. Configure:
   - **Framework Preset:** React
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `build`
   - **Environment Variable:**
     ```
     REACT_APP_API_URL=https://your-backend-url.onrender.com
     ```
6. Click **"Deploy"**

Your frontend will be live at `https://rag-chatbot-frontend.vercel.app`

---

## Step 4: Update CORS Settings

After all services are deployed:

1. Go to backend service on Render
2. Add to Environment Variables:
   ```
   CORS_ORIGINS=["https://your-frontend-url.vercel.app","https://your-frontend-url.onrender.com"]
   ```
   Replace with your actual frontend URL(s)

---

## Step 5: Testing

1. **Test Backend:**
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Should return: `{"ok":true}`

2. **Test API:**
   ```bash
   curl https://your-backend-url.onrender.com/v1/chat/documents/stats
   ```

3. **Test Frontend:**
   - Open your frontend URL
   - Try ingesting a website
   - Ask a question

---

## Configuration Summary

### Backend Environment Variables (Final)
```
ENV=prod
VECTOR_DB_PATH=/opt/render/project/src/chroma_db
LOCAL_BUCKET_DIR=/opt/render/project/src/rag-documents
LLM_BASE_URL=https://your-ollama-service.onrender.com
# OR use OpenAI:
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_API_KEY=sk-...
LLM_DEFAULT_MODEL=llama3.2:3b
LLM_DEFAULT_TEMPERATURE=0.1
LLM_DEFAULT_MAX_TOKENS=2000
CORS_ORIGINS=["https://your-frontend-url.vercel.app"]
```

### Frontend Environment Variables
```
REACT_APP_API_URL=https://your-backend-url.onrender.com
```

---

## Important Notes

### Free Tier Limitations

1. **Render Free Tier:**
   - Services spin down after 15 minutes of inactivity
   - First request after spin-down takes longer (~30-60 seconds)
   - 750 hours/month free (enough for 24/7 on one service)

2. **Storage:**
   - Vector database persists only while service is running
   - Data may be lost on service restart or spin-down
   - For production, consider persistent storage solutions

3. **Ollama on Render:**
   - Models are downloaded each time service restarts
   - Consider using OpenAI API for production
   - Or upgrade to paid plan for persistent storage

### Cost Optimization

- Use **Vercel** for frontend (free, faster)
- Use **Render** for backend
- Consider **OpenAI API** instead of Ollama for more reliability
- Upgrade to paid plan if you need 24/7 uptime

### Troubleshooting

1. **Backend won't start:**
   - Check environment variables
   - Check logs in Render dashboard
   - Ensure `requirements.txt` includes all dependencies

2. **Frontend can't connect:**
   - Verify `REACT_APP_API_URL` matches backend URL
   - Check CORS settings in backend
   - Check backend logs for errors

3. **Ollama errors:**
   - Ensure model is pulled: `ollama pull llama3.2:3b`
   - Check Ollama service is running
   - Verify `LLM_BASE_URL` includes protocol (https://)

4. **Vector DB issues:**
   - Data persists only during service uptime
   - After spin-down, vector DB is empty again
   - Consider using external vector DB for production

---

## Quick Reference

**Backend Service:**
- Type: Web Service
- Build: `pip install -r requirements.txt`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Frontend Service:**
- Type: Static Site (Render) or Vercel
- Build: `npm run build`
- Publish: `build`

**Ollama Service (Optional):**
- Type: Web Service (Docker)
- Dockerfile: `ollama/Dockerfile.render`
- Environment: `OLLAMA_HOST=0.0.0.0:$PORT`

---

## Next Steps After Deployment

1. **Add Website Sources:**
   - Use the deployed frontend to add URLs
   - Content will be scraped and indexed

2. **Test the System:**
   - Ingest some websites
   - Ask questions
   - Verify everything works

3. **Monitor:**
   - Check Render dashboard for logs
   - Monitor API response times
   - Check service uptime

4. **Optimize:**
   - Adjust `context_limit` if responses are too long
   - Tune `temperature` for better answers
   - Consider caching for better performance

---

**🎉 Congratulations! Your RAG Chatbot is now deployed!**

