# Testing Guide

## ✅ Quick Test Results

The application is now working! Here's what was verified:

1. **Backend Server**: Running on `http://localhost:8080` ✅
2. **Ollama Integration**: Connected to `http://localhost:11434` ✅
3. **Model Available**: `llama3.2:3b` is installed and working ✅
4. **Website Ingestion**: Successfully scraped and added 303 chunks ✅
5. **Chat with LLM**: Successfully generating answers from context ✅

## 🚀 How to Test the Full Application

### Backend (Already Running)

The backend is running in the background. To verify:
```bash
curl http://localhost:8080/health
```

To restart manually:
```bash
cd backend
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

### Frontend Setup and Start

1. **Install frontend dependencies** (if not already done):
```bash
cd frontend
npm install
```

2. **Start the frontend**:
```bash
npm start
```

The frontend will open at `http://localhost:3000`

### Testing via Frontend UI

1. **Open** `http://localhost:3000` in your browser
2. **Add a website source** in the sidebar:
   - Enter a URL (e.g., `https://en.wikipedia.org/wiki/Machine_learning`)
   - Click "Ingest Websites"
   - Wait for ingestion to complete
3. **Ask questions** in the chat:
   - Type questions about the ingested content
   - The AI will retrieve relevant context and generate answers

### Testing via API (Terminal)

#### 1. Check document stats:
```bash
curl http://localhost:8080/v1/chat/documents/stats
```

#### 2. Ingest a website:
```bash
curl -X POST http://localhost:8080/v1/websites/ingest-multiple \
  -H "Content-Type: application/json" \
  -d '{
    "urls": ["https://en.wikipedia.org/wiki/Machine_learning"],
    "max_pages_per_site": 5
  }'
```

#### 3. Send a chat message:
```bash
curl -X POST http://localhost:8080/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "context_limit": 5,
    "temperature": 0.1
  }'
```

#### 4. View API documentation:
Open `http://localhost:8080/docs` in your browser for interactive API testing

## 📊 Expected Behavior

- **Website Ingestion**: Should scrape content and add chunks to vector database
- **Chat Messages**: Should retrieve relevant context and generate coherent answers
- **Document Stats**: Should show total documents and chunks
- **Source Attribution**: Each answer should include source references

## 🔧 Troubleshooting

### Backend not starting:
- Check if port 8080 is already in use: `lsof -i :8080`
- Verify `.env` file exists in `backend/` directory
- Check Ollama is running: `curl http://localhost:11434/api/tags`

### LLM not generating answers:
- Verify Ollama is running: `ollama list`
- Check model is installed: `ollama list | grep llama3.2`
- Check backend logs for errors

### Frontend not connecting:
- Verify backend is running on port 8080
- Check browser console for errors
- Verify `REACT_APP_API_URL` is set correctly (defaults to `http://localhost:8080`)

## 🎯 Test Checklist

- [x] Backend health check
- [x] Ollama connection
- [x] Model availability
- [x] Website ingestion
- [x] Document storage in vector DB
- [x] LLM answer generation
- [ ] Frontend UI (manual test)
- [ ] Multiple website sources
- [ ] Complex questions
- [ ] Error handling

## 📝 Notes

- The model is currently configured to use `llama3.2:3b` via Ollama
- Vector database is stored at `/tmp/chroma_db`
- Documents are stored at `/tmp/rag-documents`
- All configuration is in `backend/.env`

