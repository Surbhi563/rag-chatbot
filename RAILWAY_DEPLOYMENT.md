# Railway Deployment Guide - Multiple Services

Railway picks up the root `railway.json` for your **backend service**. To deploy Ollama as well, you need to add it as a **separate service** in the same project.

## How Railway Works

- **Root `railway.json`** = Backend service config ✅ (already set up)
- **`ollama/railway.json`** = Ollama service config ✅ (already set up)
- Both services deploy in the **same Railway project**

---

## Step-by-Step Deployment

### Step 1: Deploy Backend (Auto-detected)

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your `rag-chatbot` repository
5. Railway will automatically:
   - Detect `railway.json` at root
   - Deploy your backend service
   - Use the config: `cd backend && uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Step 2: Add Ollama Service

After backend is deployed:

1. In your Railway project dashboard
2. Click **"+ New"** → **"Empty Service"**
3. Select **"GitHub Repo"** → Choose same repository
4. Click the service → Go to **"Settings"** tab
5. Configure:
   - **Root Directory:** `ollama`
   - **Dockerfile Path:** `Dockerfile.render`
   - Railway will auto-detect `ollama/railway.json`
6. **Save**

**Or via Railway CLI:**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to your project (if not already)
railway link

# Deploy Ollama service
cd ollama
railway service create ollama-service
railway up
```

### Step 3: Set Environment Variables

#### Backend Service Variables:
```
ENV=prod
LOG_LEVEL=INFO
LOG_FORMAT=json
VECTOR_DB_PATH=/tmp/chroma_db
LOCAL_BUCKET_DIR=/tmp/rag-documents

# Option A: Use Ollama (set after Ollama service is deployed)
LLM_BASE_URL=${{OLLAMA_SERVICE_URL}}  # Railway service URL variable
LLM_DEFAULT_MODEL=llama3.2:3b
LLM_DEFAULT_TEMPERATURE=0.1
LLM_DEFAULT_MAX_TOKENS=2000

# Option B: Use OpenAI (recommended - no memory issues)
# LLM_BASE_URL=https://api.openai.com/v1
# LLM_API_KEY=sk-your-openai-key
# LLM_DEFAULT_MODEL=gpt-3.5-turbo
# LLM_DEFAULT_PROVIDER=openai
```

#### Ollama Service Variables:
```
PORT=11434  # Railway will auto-set this, but good to have default
OLLAMA_HOST=0.0.0.0:$PORT
```

### Step 4: Connect Services

In Railway dashboard:

1. Go to **Backend Service** → **"Variables"** tab
2. Click **"New Variable"**
3. Name: `LLM_BASE_URL`
4. Value: Click **"Add Reference"** → Select **Ollama Service** → **`RAILWAY_PUBLIC_DOMAIN`**
   - This creates: `${{ollama-service.RAILWAY_PUBLIC_DOMAIN}}`
5. Format it: `https://${{ollama-service.RAILWAY_PUBLIC_DOMAIN}}`
6. **Save**

---

## Railway Service URLs

Railway gives each service a unique URL:
- **Backend:** `rag-chatbot-backend.railway.app`
- **Ollama:** `ollama-service.railway.app` (or whatever you named it)

You can reference these between services using Railway's variable syntax.

---

## Quick Start (Recommended)

**For fastest deployment, use OpenAI API instead:**

1. Deploy backend only (Railway auto-detects `railway.json`)
2. Set environment variables:
   ```
   LLM_BASE_URL=https://api.openai.com/v1
   LLM_API_KEY=sk-your-openai-key
   LLM_DEFAULT_MODEL=gpt-3.5-turbo
   LLM_DEFAULT_PROVIDER=openai
   ```
3. **Done!** No Ollama service needed ✅

---

## Current Config Files

✅ **Root `railway.json`** - Backend service (active)
✅ **`ollama/railway.json`** - Ollama service (ready to use)

Both are properly configured and ready to deploy!

---

## Troubleshooting

**Railway not detecting Ollama service?**
- Make sure you created a **new service** (not just adding to backend)
- Set **Root Directory** to `ollama` in service settings
- Check that `ollama/railway.json` exists

**Service URLs not connecting?**
- Wait 2-3 minutes for both services to fully deploy
- Check Railway service logs
- Verify environment variables are set correctly

**Memory issues with Ollama?**
- Railway free tier: 512MB RAM (same as Render)
- Consider using OpenAI API instead
- Or upgrade Railway plan for more memory

---

## Next Steps

1. Deploy backend (Railway auto-detects `railway.json` at root)
2. Add Ollama as second service (point to `ollama/` directory)
3. OR just use OpenAI API (simpler, no memory issues)

Need help with a specific step? Let me know!

