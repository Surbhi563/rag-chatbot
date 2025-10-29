# Railway Multi-Service Configuration

Railway doesn't support multiple services in a single `railway.json` file. Here's how to deploy both backend and Ollama.

## Current Setup

✅ **Root `railway.json`** → Backend service (auto-detected)
✅ **Root `ollama.railway.json`** → Ollama service (reference this when adding service)

---

## Deploying Both Services

### Step 1: Backend Service (Automatic)

Railway automatically detects the root `railway.json` and deploys your backend.

### Step 2: Ollama Service (Manual)

1. In Railway project dashboard
2. Click **"+ New"** → **"Empty Service"** (or **"GitHub Repo"**)
3. Select same repository
4. In service **Settings**:
   - **Root Directory:** `ollama` (optional, Railway will use Dockerfile path)
   - **Build Command:** Leave empty (Dockerfile handles it)
   - **Configuration File:** `ollama.railway.json` (if Railway supports specifying it)
   
   OR
   
   Railway should auto-detect `ollama/railway.json` if you set Root Directory to `ollama`

### Alternative: Use Service Settings

If Railway doesn't auto-detect, configure manually in service Settings:

1. **Build:** Docker
2. **Dockerfile Path:** `ollama/Dockerfile.render`
3. **Docker Context:** `ollama`
4. **Start Command:** `/bin/bash /start.sh`
5. **Health Check Path:** `/api/tags`

---

## Configuration Files

### `railway.json` (Backend)
- Located: Root directory
- Service: Backend (Python/FastAPI)
- Builder: NIXPACKS
- Auto-detected by Railway ✅

### `ollama.railway.json` (Ollama)
- Located: Root directory  
- Service: Ollama (Docker)
- Builder: DOCKERFILE
- Reference when adding Ollama service

### `ollama/railway.json` (Alternative)
- Located: `ollama/` directory
- Same config as `ollama.railway.json`
- Used when Root Directory = `ollama`

---

## Quick Deploy Steps

1. **Push code to GitHub** (both config files included)
2. **Railway auto-deploys backend** (uses root `railway.json`)
3. **Add Ollama service manually:**
   - New Service → Same Repo
   - Root Directory: `ollama`
   - Railway uses `ollama/railway.json` automatically

---

## Service URLs

After deployment:
- **Backend:** `rag-chatbot-backend.railway.app`
- **Ollama:** `ollama-service.railway.app` (or your service name)

Connect them using Railway's environment variable references:
```
LLM_BASE_URL=https://${{ollama-service.RAILWAY_PUBLIC_DOMAIN}}
```

---

## Troubleshooting

**Railway not detecting Ollama config?**
- Make sure you added a **new service** (not modifying backend)
- Set **Root Directory** to `ollama` in service settings
- Or manually configure Dockerfile path: `ollama/Dockerfile.render`

**Want to use root `ollama.railway.json` instead?**
- Railway doesn't directly support named config files
- Better to use `ollama/railway.json` or configure manually in dashboard

Both services are ready to deploy! 🚀

