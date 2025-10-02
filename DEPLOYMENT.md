# Deployment Guide

## Free Hosting Options

### 1. Railway (Recommended)

**Backend + Frontend on Railway:**

1. **Create Railway Account:**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend:**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Deploy backend
   cd backend
   railway init
   railway up
   ```

3. **Set Environment Variables:**
   - In Railway dashboard, add these variables:
   ```
   LLM_API_KEY=your-openai-key (optional, uses local Ollama)
   VECTOR_DB_PATH=/tmp/chroma_db
   LOCAL_BUCKET_DIR=/tmp/rag-documents
   ```

4. **Deploy Frontend:**
   - Create new Railway project for frontend
   - Set build command: `npm run build`
   - Set start command: `npx serve -s build -l 3000`

### 2. Render (Alternative)

**Backend on Render:**
1. Go to [render.com](https://render.com)
2. Connect GitHub repository
3. Create new Web Service
4. Set build command: `cd backend && pip install -r requirements.txt`
5. Set start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

**Frontend on Vercel:**
1. Go to [vercel.com](https://vercel.com)
2. Import GitHub repository
3. Set root directory to `frontend`
4. Deploy automatically

### 3. Fly.io (Alternative)

```bash
# Install flyctl
curl -L https://fly.io/install.sh | sh

# Deploy backend
cd backend
fly launch
fly deploy

# Deploy frontend
cd frontend
fly launch
fly deploy
```

## Environment Variables

### Backend (.env)
```env
# LLM Configuration (optional - uses local Ollama by default)
LLM_API_KEY=your-openai-key
LLM_BASE_URL=https://api.openai.com/v1
LLM_DEFAULT_MODEL=gpt-3.5-turbo

# Vector Database
VECTOR_DB_PATH=/tmp/chroma_db

# Storage
LOCAL_BUCKET_DIR=/tmp/rag-documents

# App Configuration
APP_NAME=rag-chatbot
APP_VERSION=1.0.0
ENVIRONMENT=production
```

### Frontend (.env)
```env
REACT_APP_API_URL=https://your-backend-url.railway.app
```

## Post-Deployment Setup

1. **Add Website Sources:**
   - Use the deployed frontend to add website URLs
   - The system will scrape and ingest content

2. **Test the System:**
   - Try asking questions about the ingested content
   - Verify the local LLM is working

## Cost Considerations

- **Railway:** $5/month credit (usually enough for small projects)
- **Render:** 750 hours/month free
- **Vercel:** Free for frontend
- **Fly.io:** 3 small VMs free

## Troubleshooting

1. **Backend not starting:** Check environment variables
2. **Frontend can't connect:** Verify API_BASE_URL
3. **LLM errors:** Ensure Ollama is running or API key is set
4. **Vector DB issues:** Check VECTOR_DB_PATH permissions

## Local Development

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8082

# Frontend
cd frontend
npm start
```
