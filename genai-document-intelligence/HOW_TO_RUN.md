# How to Run the GenAI Document Intelligence Platform

This guide provides step-by-step instructions for running the application in different environments.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Running with Python](#running-with-python)
4. [Running with Docker](#running-with-docker)
5. [Running with Docker Compose](#running-with-docker-compose)
6. [Verifying the Installation](#verifying-the-installation)
7. [Using the Application](#using-the-application)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Python 3.9 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** (optional, for cloning)
- **Docker** (optional, for containerized deployment) ([Download](https://www.docker.com/get-started))

### Required API Keys

1. **OpenAI API Key**
   - Sign up at https://platform.openai.com/
   - Navigate to API Keys section
   - Create a new secret key
   - Copy and save it securely

2. **Pinecone API Key**
   - Sign up at https://www.pinecone.io/
   - Create a new project
   - Get your API key from the dashboard
   - Note your environment (e.g., `us-east-1-aws`)

---

## Local Development Setup

### Step 1: Navigate to Project Directory

```bash
cd "C:\Users\e410030\DAAiS\GenAI- Intelligence"
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
```

**macOS/Linux:**
```bash
python3 -m venv venv
```

### Step 3: Activate Virtual Environment

**Windows (Command Prompt):**
```bash
venv\Scripts\activate
```

**Windows (PowerShell):**
```bash
venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` prefix in your terminal.

### Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI
- Uvicorn
- LangChain
- OpenAI
- Pinecone
- Sentence Transformers
- RAGAS
- And all other dependencies

**Installation time:** ~5-10 minutes depending on your internet speed.

### Step 5: Configure Environment Variables

**Create `.env` file:**

**Windows:**
```bash
copy .env.example .env
```

**macOS/Linux:**
```bash
cp .env.example .env
```

**Edit `.env` file** with your favorite text editor:

```env
# Required - Add your actual API keys
OPENAI_API_KEY=sk-your-actual-openai-key-here
PINECONE_API_KEY=your-actual-pinecone-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=doc-intelligence

# Optional - Adjust as needed
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=512
CHUNK_OVERLAP=50
TOP_K_RETRIEVAL=20
TOP_K_RERANK=5
```

**Important:** Replace the placeholder values with your actual API keys!

---

## Running with Python

### Method 1: Using Uvicorn Directly (Recommended for Development)

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Options explained:**
- `app.main:app` - Points to the FastAPI app instance
- `--reload` - Auto-reload on code changes (development only)
- `--host 0.0.0.0` - Listen on all network interfaces
- `--port 8000` - Port number (change if needed)

**Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using StatReload
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Method 2: Production Mode (Multiple Workers)

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Note:** Don't use `--reload` with multiple workers.

### Method 3: Using Python Directly

```bash
python -m uvicorn app.main:app --reload
```

### Method 4: Custom Configuration

Create a file `run.py`:

```python
import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        workers=settings.API_WORKERS if not settings.API_RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower()
    )
```

Then run:
```bash
python run.py
```

---

## Running with Docker

### Step 1: Build Docker Image

```bash
docker build -f docker/Dockerfile -t genai-doc-intelligence:latest .
```

**Build time:** ~5-10 minutes (first time)

### Step 2: Run Container

```bash
docker run -d \
  --name genai-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-openai-key \
  -e PINECONE_API_KEY=your-pinecone-key \
  -e PINECONE_ENVIRONMENT=us-east-1-aws \
  -e PINECONE_INDEX_NAME=doc-intelligence \
  -v "%cd%\data:/app/data" \
  genai-doc-intelligence:latest
```

**Windows PowerShell:**
```powershell
docker run -d `
  --name genai-api `
  -p 8000:8000 `
  -e OPENAI_API_KEY=your-openai-key `
  -e PINECONE_API_KEY=your-pinecone-key `
  -e PINECONE_ENVIRONMENT=us-east-1-aws `
  -e PINECONE_INDEX_NAME=doc-intelligence `
  -v "${PWD}\data:/app/data" `
  genai-doc-intelligence:latest
```

**macOS/Linux:**
```bash
docker run -d \
  --name genai-api \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your-openai-key \
  -e PINECONE_API_KEY=your-pinecone-key \
  -e PINECONE_ENVIRONMENT=us-east-1-aws \
  -e PINECONE_INDEX_NAME=doc-intelligence \
  -v "$(pwd)/data:/app/data" \
  genai-doc-intelligence:latest
```

### Step 3: View Logs

```bash
docker logs -f genai-api
```

### Step 4: Stop Container

```bash
docker stop genai-api
docker rm genai-api
```

---

## Running with Docker Compose (Recommended for Production)

### Step 1: Create `.env` File

Ensure you have a `.env` file in the project root with your API keys.

### Step 2: Navigate to Docker Directory

```bash
cd docker
```

### Step 3: Start Services

```bash
docker-compose up -d
```

**This will start:**
- API service (port 8000)
- Redis service (port 6379)
- Prometheus metrics (port 9090)

**First run:** ~5-10 minutes to build images

### Step 4: View Logs

**All services:**
```bash
docker-compose logs -f
```

**API only:**
```bash
docker-compose logs -f api
```

**Redis only:**
```bash
docker-compose logs -f redis
```

### Step 5: Check Service Status

```bash
docker-compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
genai-doc-intelligence  running             0.0.0.0:8000->8000/tcp
genai-redis             running             0.0.0.0:6379->6379/tcp
```

### Step 6: Stop Services

```bash
docker-compose down
```

**To remove volumes as well:**
```bash
docker-compose down -v
```

### Step 7: Rebuild After Code Changes

```bash
docker-compose up -d --build
```

---

## Verifying the Installation

### 1. Check Health Endpoint

**Using Browser:**
Navigate to: http://localhost:8000/health

**Using curl:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-03-22T11:48:00.000Z",
  "services": {
    "api": true,
    "vector_store": true,
    "bm25_index": true,
    "openai": true
  }
}
```

### 2. Access API Documentation

Open in browser: http://localhost:8000/docs

You should see the interactive Swagger UI with all available endpoints.

### 3. Check Metrics

Open in browser: http://localhost:8000/metrics

You should see Prometheus metrics.

### 4. Test Basic Endpoint

```bash
curl http://localhost:8000/
```

**Expected response:**
```json
{
  "name": "GenAI Document Intelligence Platform",
  "version": "1.0.0",
  "description": "Production-ready RAG system...",
  "docs": "/docs",
  "health": "/health"
}
```

---

## Using the Application

### 1. Upload a Document

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@path/to/your/document.pdf"
```

**Using Python:**
```python
import requests

with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/api/v1/ingest", files=files)
    print(response.json())
```

**Expected response:**
```json
{
  "document_id": "uuid-here",
  "file_name": "document.pdf",
  "total_chunks": 25,
  "status": "success",
  "message": "Document ingested successfully with 25 chunks",
  "processing_time": 12.34
}
```

### 2. Query Documents

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main findings?",
    "top_k": 5,
    "use_reranking": true
  }'
```

**Using Python:**
```python
import requests

query_data = {
    "query": "What are the main findings?",
    "top_k": 5,
    "use_reranking": True
}

response = requests.post(
    "http://localhost:8000/api/v1/query",
    json=query_data
)

result = response.json()
print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence_score']}")
```

### 3. Run Evaluation

**Using Python:**
```python
import requests

eval_data = {
    "questions": [
        "What is the main topic?",
        "What are the key findings?"
    ],
    "ground_truths": [
        "The main topic is AI research.",
        "The key findings include improved accuracy."
    ]
}

response = requests.post(
    "http://localhost:8000/api/v1/evaluate",
    json=eval_data
)

print(response.json())
```

### 4. Interactive API Testing

1. Open http://localhost:8000/docs
2. Click on any endpoint (e.g., `/api/v1/query`)
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"
6. View the response

---

## Troubleshooting

### Issue 1: Port Already in Use

**Error:**
```
ERROR: [Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000)
```

**Solution:**

**Option A - Use Different Port:**
```bash
uvicorn app.main:app --reload --port 8001
```

**Option B - Kill Process on Port 8000:**

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**macOS/Linux:**
```bash
lsof -ti:8000 | xargs kill -9
```

### Issue 2: Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```bash
# Ensure virtual environment is activated
# Then reinstall dependencies
pip install -r requirements.txt
```

### Issue 3: API Key Errors

**Error:**
```
openai.error.AuthenticationError: Incorrect API key provided
```

**Solution:**
1. Check `.env` file exists in project root
2. Verify API keys are correct (no extra spaces)
3. Ensure `.env` is loaded:
   ```bash
   # Windows
   type .env
   
   # macOS/Linux
   cat .env
   ```

### Issue 4: Pinecone Connection Failed

**Error:**
```
PineconeException: Failed to connect to Pinecone
```

**Solution:**
1. Verify Pinecone API key is correct
2. Check environment name matches your Pinecone dashboard
3. Ensure index name is correct
4. Check internet connectivity

### Issue 5: Docker Build Fails

**Error:**
```
ERROR: failed to solve: process "/bin/sh -c pip install..." did not complete successfully
```

**Solution:**
```bash
# Clear Docker cache and rebuild
docker system prune -a
docker build -f docker/Dockerfile -t genai-doc-intelligence:latest . --no-cache
```

### Issue 6: Out of Memory

**Error:**
```
MemoryError: Unable to allocate array
```

**Solution:**

**For Docker:**
```bash
# Increase Docker memory limit
# Docker Desktop: Settings > Resources > Memory (set to 4GB+)
```

**For Python:**
```bash
# Reduce batch size in .env
RAGAS_BATCH_SIZE=5
```

### Issue 7: Slow Performance

**Solutions:**
1. **Enable caching:** Add Redis (already in docker-compose)
2. **Reduce top_k:** Use smaller values (3-5 instead of 20)
3. **Disable reranking for testing:**
   ```json
   {"query": "test", "use_reranking": false}
   ```
4. **Use multiple workers:**
   ```bash
   uvicorn app.main:app --workers 4
   ```

### Issue 8: Import Errors in IDE

**Solution:**
```bash
# Ensure IDE is using the correct Python interpreter
# VS Code: Ctrl+Shift+P > "Python: Select Interpreter" > Choose venv
# PyCharm: Settings > Project > Python Interpreter > Choose venv
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | ✅ Yes | - | OpenAI API key |
| `PINECONE_API_KEY` | ✅ Yes | - | Pinecone API key |
| `PINECONE_ENVIRONMENT` | ✅ Yes | - | Pinecone environment |
| `PINECONE_INDEX_NAME` | No | doc-intelligence | Index name |
| `CHUNK_SIZE` | No | 512 | Chunk size in tokens |
| `CHUNK_OVERLAP` | No | 50 | Overlap between chunks |
| `TOP_K_RETRIEVAL` | No | 20 | Candidates for reranking |
| `TOP_K_RERANK` | No | 5 | Final results |
| `DENSE_WEIGHT` | No | 0.7 | Dense search weight |
| `SPARSE_WEIGHT` | No | 0.3 | Sparse search weight |
| `API_PORT` | No | 8000 | API server port |
| `LOG_LEVEL` | No | INFO | Logging level |

---

## Quick Reference Commands

### Start Application
```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --workers 4

# Docker Compose
cd docker && docker-compose up -d
```

### Stop Application
```bash
# Python: Press Ctrl+C

# Docker Compose
cd docker && docker-compose down
```

### View Logs
```bash
# Docker Compose
docker-compose logs -f api
```

### Run Tests
```bash
pytest tests/ -v
```

### Access Documentation
```
http://localhost:8000/docs
```

---

## Next Steps

1. ✅ Application is running
2. 📄 Upload your first document
3. 🔍 Test a query
4. 📊 Check the metrics
5. 🚀 Deploy to production (see `DEPLOYMENT.md`)

---

## Support

- **Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Architecture:** See `ARCHITECTURE.md`
- **Deployment:** See `DEPLOYMENT.md`

**Happy querying! 🚀**
