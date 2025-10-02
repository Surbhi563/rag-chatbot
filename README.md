# RAG Chatbot

A modern Retrieval-Augmented Generation (RAG) chatbot with a separated frontend and backend architecture. Upload documents and ask questions about their content using AI-powered search and generation.

## 🏗️ Architecture

```
├── backend/                 # FastAPI backend service
│   ├── app/                # Application code
│   │   ├── api/           # API routes and middleware
│   │   ├── core/          # Configuration and logging
│   │   ├── schemas/       # Request/response models
│   │   ├── services/      # Business logic (RAG, LLM, storage)
│   │   └── utils/         # Utilities
│   ├── pyproject.toml     # Python dependencies
│   ├── Dockerfile         # Backend container
│   └── scripts/           # Development scripts
├── frontend/               # React frontend application
│   ├── src/               # React source code
│   ├── public/            # Static assets
│   └── package.json       # Node.js dependencies
└── README.md              # This file
```

## 🚀 Features

- **📄 Document Upload**: Support for PDF, DOCX, and TXT files
- **🔍 Vector Search**: ChromaDB-based semantic search
- **🤖 AI Chat**: OpenAI-powered question answering with source attribution
- **📊 Document Statistics**: Track uploaded documents and chunks
- **🎨 Modern UI**: Responsive React interface with drag-and-drop upload
- **🔒 Source Attribution**: Every answer includes source document references
- **⚡ Fast Performance**: Optimized chunking and retrieval

## 📋 Prerequisites

- Python 3.11+
- Node.js 16+
- [uv](https://github.com/astral-sh/uv) package manager
- Docker (optional)

## 🛠️ Installation

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install Python dependencies:**
   ```bash
   uv sync --dev
   ```

3. **Set up environment variables:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

4. **Start the backend server:**
   ```bash
   uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the frontend development server:**
   ```bash
   npm start
   ```

## 🏃‍♂️ Quick Start

### Using Development Scripts

**Backend:**
```bash
cd backend
./scripts/dev.sh  # Install + test + start server
```

**Frontend:**
```bash
cd frontend
npm start
```

### Using Docker

**Backend:**
```bash
cd backend
docker build -t rag-backend .
docker run -p 8080:8080 rag-backend
```

**Frontend:**
```bash
cd frontend
npm run build
# Serve the build folder with any static server
```

## 🔧 Configuration

### Backend Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Core Settings
ENV=dev
PORT=8080
LOCAL_BUCKET_DIR=/tmp/rag-documents

# LLM Integration
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=your-openai-api-key
LLM_DEFAULT_MODEL=gpt-3.5-turbo
LLM_DEFAULT_TEMPERATURE=0.1

# Vector Database
VECTOR_DB_PATH=/tmp/rag-documents/chroma_db
```

### Frontend Configuration

The frontend automatically connects to `http://localhost:8080` by default. To change this, set the `REACT_APP_API_URL` environment variable:

```bash
REACT_APP_API_URL=http://your-backend-url:8080 npm start
```

## 📚 API Documentation

### Backend Endpoints

- `GET /health` - Health check
- `POST /v1/uploads` - Upload documents
- `POST /v1/chat/message` - Send chat message
- `POST /v1/chat/documents/add` - Add document to RAG system
- `GET /v1/chat/documents/stats` - Get document statistics
- `DELETE /v1/chat/documents/clear` - Clear all documents

### Example Usage

**Upload a document:**
```bash
curl -F "file=@document.pdf" http://localhost:8080/v1/uploads
```

**Add document to RAG system:**
```bash
curl -X POST http://localhost:8080/v1/chat/documents/add \
  -H "Content-Type: application/json" \
  -d '{"upload_id": "uploads/abc123/document.pdf"}'
```

**Send a chat message:**
```bash
curl -X POST http://localhost:8080/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What is this document about?"}'
```

## 🧪 Testing

**Backend:**
```bash
cd backend
uv run pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

## 🚀 Deployment

### Production Deployment

1. **Build backend:**
   ```bash
   cd backend
   docker build -t rag-backend .
   ```

2. **Build frontend:**
   ```bash
   cd frontend
   npm run build
   ```

3. **Deploy with Docker Compose:**
   ```yaml
   version: '3.8'
   services:
     backend:
       image: rag-backend
       ports:
         - "8080:8080"
       environment:
         - ENV=prod
         - LLM_API_KEY=${LLM_API_KEY}
     
     frontend:
       image: nginx:alpine
       ports:
         - "80:80"
       volumes:
         - ./frontend/build:/usr/share/nginx/html
   ```

## 🔍 How It Works

1. **Document Upload**: Users upload PDF, DOCX, or TXT files
2. **Text Extraction**: Documents are processed to extract text content
3. **Chunking**: Text is split into overlapping chunks for better retrieval
4. **Vectorization**: Chunks are converted to embeddings using sentence transformers
5. **Storage**: Embeddings are stored in ChromaDB vector database
6. **Query Processing**: User questions are vectorized and matched against stored chunks
7. **Context Retrieval**: Most relevant chunks are retrieved as context
8. **Answer Generation**: LLM generates answers based on retrieved context
9. **Source Attribution**: Answers include references to source documents

## 🛡️ Security & Privacy

- Documents are processed locally
- No data is sent to external services except for LLM API calls
- Vector database is stored locally
- CORS is configured for frontend-backend communication

## 📊 Monitoring

The application includes structured logging and health checks:

- JSON-formatted logs for easy parsing
- Request/response tracking
- Error handling and reporting
- Document processing metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions, please open an issue in the repository.

---

**🚀 Built with FastAPI, React, ChromaDB, and OpenAI for modern RAG-powered conversations**
