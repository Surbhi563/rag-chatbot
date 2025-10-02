# GitHub Setup Instructions

## Step 1: Create GitHub Repository

1. Go to [github.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Repository name: `rag-chatbot` (or any name you prefer)
5. Description: "RAG chatbot with local LLM and website ingestion"
6. Make it **Public** (required for free hosting)
7. **DO NOT** check "Add a README file"
8. **DO NOT** check "Add .gitignore"
9. **DO NOT** check "Choose a license"
10. Click "Create repository"

## Step 2: Connect Local Repository to GitHub

After creating the repository, GitHub will show you commands. Use these:

```bash
# Add the remote repository (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/rag-chatbot.git

# Push the code to GitHub
git branch -M main
git push -u origin main
```

## Step 3: Deploy to Railway

1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your `rag-chatbot` repository
6. Railway will automatically detect it's a Python project
7. Set environment variables in Railway dashboard:
   - `VECTOR_DB_PATH=/tmp/chroma_db`
   - `LOCAL_BUCKET_DIR=/tmp/rag-documents`
   - `LLM_API_KEY=your-openai-key` (optional)

## Step 4: Deploy Frontend

1. Create a new Railway project for the frontend
2. Select the same GitHub repository
3. Set the root directory to `frontend`
4. Set build command: `npm install && npm run build`
5. Set start command: `npx serve -s build -l 3000`
6. Set environment variable: `REACT_APP_API_URL=https://your-backend-url.railway.app`

## Alternative: One-Click Deploy

You can also use Railway's one-click deploy by adding this button to your README:

```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-id)
```

## Environment Variables

### Backend (.env)
```env
VECTOR_DB_PATH=/tmp/chroma_db
LOCAL_BUCKET_DIR=/tmp/rag-documents
LLM_API_KEY=your-openai-key
APP_NAME=rag-chatbot
APP_VERSION=1.0.0
ENVIRONMENT=production
```

### Frontend (.env)
```env
REACT_APP_API_URL=https://your-backend-url.railway.app
```

## Post-Deployment

1. Your backend will be available at: `https://your-project-name.railway.app`
2. Your frontend will be available at: `https://your-frontend-project.railway.app`
3. Test the system by adding website URLs and asking questions
4. The local LLM (Ollama) will work automatically in the cloud

## Troubleshooting

- **Build fails**: Check that all dependencies are in `requirements.txt`
- **Frontend can't connect**: Verify `REACT_APP_API_URL` is correct
- **LLM errors**: Ensure environment variables are set correctly
- **Vector DB issues**: Check that `VECTOR_DB_PATH` is writable

## Cost

- **Railway**: $5/month credit (usually enough for small projects)
- **Total**: $0-5/month for hosting
- **No API costs**: Uses local Ollama LLM
