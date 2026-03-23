# How to Run the Agentic AI Ecosystem

This guide provides step-by-step instructions for running the application locally and with Docker.

---

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Running Locally](#running-locally)
3. [Running with Docker](#running-with-docker)
4. [Verification](#verification)
5. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required
- **Python 3.10 or higher**
- **OpenAI API Key** (get one from https://platform.openai.com/api-keys)

### Optional (for full features)
- **PostgreSQL 15+** (for SQL tool functionality)
- **Redis 7+** (for caching and session management)
- **Docker & Docker Compose** (for containerized deployment)

---

## Running Locally

### Step 1: Clone and Navigate to Project

```bash
cd C:\Users\e410030\DAAiS\AgenticAI-Ecosystem
```

### Step 2: Create Virtual Environment

**Windows (Command Prompt):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This will install all required packages including:
- LangChain & LangGraph
- FastAPI & Uvicorn
- OpenAI
- FAISS
- SQLAlchemy
- Redis client
- And all other dependencies

### Step 4: Configure Environment Variables

**Option A: Using .env file (Recommended)**

1. Copy the example file:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

2. Edit `.env` and add your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

3. (Optional) Configure other settings:
```bash
# Database (if you have PostgreSQL running)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenticai

# Redis (if you have Redis running)
REDIS_URL=redis://localhost:6379/0

# Agent Configuration
MAX_ITERATIONS=3
QUALITY_THRESHOLD=0.85
ENABLE_SELF_CORRECTION=true
```

**Option B: Using Environment Variables**

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-actual-openai-api-key-here
set VECTOR_DB_TYPE=faiss
set LOG_LEVEL=INFO
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-actual-openai-api-key-here"
$env:VECTOR_DB_TYPE="faiss"
$env:LOG_LEVEL="INFO"
```

**Linux/Mac:**
```bash
export OPENAI_API_KEY=sk-your-actual-openai-api-key-here
export VECTOR_DB_TYPE=faiss
export LOG_LEVEL=INFO
```

### Step 5: (Optional) Initialize Database

**If you have PostgreSQL installed and want to use SQL tools:**

1. Ensure PostgreSQL is running
2. Create the database:
```bash
# Using psql
psql -U postgres -c "CREATE DATABASE agenticai;"
```

3. Run the initialization script:
```bash
python scripts/init_db.py
```

This creates sample tables (products, sales, customers) with demo data.

### Step 6: (Optional) Ingest Sample Documents

**If you want to use RAG functionality:**

1. Create sample documents in `data/documents/`:
```bash
mkdir -p data\documents
```

2. Add some text files or use the ingestion script:
```bash
# Ingest a single file
python scripts/ingest_documents.py --path data/documents/sample.txt

# Ingest entire directory
python scripts/ingest_documents.py --path data/documents
```

### Step 7: Run the Application

**Method 1: Using Uvicorn directly**
```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Method 2: Using Python**
```bash
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Method 3: Using the Makefile (if make is installed)**
```bash
make run
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 8: Access the Application

- **API Base URL**: http://localhost:8000
- **Interactive API Docs (Swagger)**: http://localhost:8000/docs
- **Alternative API Docs (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/api/v1/health

---

## Running with Docker

### Step 1: Install Docker

**Windows:**
- Download and install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)
- Ensure WSL 2 is enabled

**Linux:**
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

**Mac:**
- Download and install [Docker Desktop for Mac](https://www.docker.com/products/docker-desktop)

### Step 2: Verify Docker Installation

```bash
docker --version
docker-compose --version
```

### Step 3: Configure Environment

1. Create `.env` file from template:
```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

2. Edit `.env` and set your OpenAI API key:
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

**Note**: Other settings (DATABASE_URL, REDIS_URL) are automatically configured in docker-compose.yml

### Step 4: Build and Start Services

**Option A: Build and start in one command**
```bash
docker-compose up -d --build
```

**Option B: Build first, then start**
```bash
# Build images
docker-compose build

# Start services
docker-compose up -d
```

The `-d` flag runs containers in detached mode (background).

### Step 5: Verify Services are Running

```bash
docker-compose ps
```

You should see:
```
NAME                    STATUS              PORTS
agenticai-api           Up                  0.0.0.0:8000->8000/tcp
agenticai-postgres      Up                  0.0.0.0:5432->5432/tcp
agenticai-redis         Up                  0.0.0.0:6379->6379/tcp
agenticai-pgadmin       Up                  0.0.0.0:5050->80/tcp
```

### Step 6: View Logs

**All services:**
```bash
docker-compose logs -f
```

**Specific service:**
```bash
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f redis
```

Press `Ctrl+C` to stop viewing logs.

### Step 7: Initialize Database (Inside Container)

```bash
docker-compose exec api python scripts/init_db.py
```

### Step 8: (Optional) Ingest Documents

**Copy documents to container:**
```bash
# Create documents directory locally
mkdir -p data\documents

# Add your documents to data/documents/

# Ingest from inside container
docker-compose exec api python scripts/ingest_documents.py --path ./data/documents
```

### Step 9: Access the Application

- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/health
- **PgAdmin** (Database UI): http://localhost:5050
  - Email: admin@agenticai.com
  - Password: admin

### Step 10: Managing Docker Services

**Stop services:**
```bash
docker-compose stop
```

**Start services:**
```bash
docker-compose start
```

**Restart services:**
```bash
docker-compose restart
```

**Stop and remove containers:**
```bash
docker-compose down
```

**Stop and remove containers + volumes (deletes data):**
```bash
docker-compose down -v
```

**View resource usage:**
```bash
docker stats
```

**Scale API service:**
```bash
docker-compose up -d --scale api=3
```

---

## Verification

### Test the API is Running

**1. Ping endpoint:**
```bash
curl http://localhost:8000/ping
```

Expected response:
```json
{"status":"ok","message":"pong"}
```

**2. Health check:**
```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T12:00:00",
  "components": {
    "api": "healthy",
    "workflow": "healthy",
    "vector_db": "healthy",
    "sql_db": "healthy"
  }
}
```

### Test a Simple Query

**Using curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What is artificial intelligence?\", \"use_rag\": false, \"use_sql\": false, \"use_api\": true, \"enable_self_correction\": true}"
```

**Using Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/query",
    json={
        "query": "What is artificial intelligence?",
        "use_rag": False,
        "use_sql": False,
        "use_api": True,
        "enable_self_correction": True
    }
)

print(response.json())
```

**Using the Interactive Docs:**
1. Go to http://localhost:8000/docs
2. Click on `POST /api/v1/query`
3. Click "Try it out"
4. Enter your query in the request body
5. Click "Execute"

---

## Troubleshooting

### Local Deployment Issues

**Problem: `ModuleNotFoundError` when running**
```bash
# Solution: Ensure virtual environment is activated and dependencies installed
pip install -r requirements.txt
```

**Problem: `OPENAI_API_KEY not found`**
```bash
# Solution: Set the environment variable
# Windows CMD
set OPENAI_API_KEY=sk-your-key-here

# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-key-here"

# Linux/Mac
export OPENAI_API_KEY=sk-your-key-here
```

**Problem: Port 8000 already in use**
```bash
# Solution: Use a different port
uvicorn src.api.main:app --reload --port 8001

# Or find and kill the process using port 8000
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

**Problem: Database connection error**
```bash
# Solution: Check PostgreSQL is running
# Windows
sc query postgresql-x64-15

# Linux
sudo systemctl status postgresql

# Or use SQLite by commenting out DATABASE_URL in .env
```

### Docker Deployment Issues

**Problem: Docker daemon not running**
```bash
# Solution: Start Docker Desktop (Windows/Mac)
# Or start Docker service (Linux)
sudo systemctl start docker
```

**Problem: Permission denied (Linux)**
```bash
# Solution: Add user to docker group
sudo usermod -aG docker $USER
# Log out and log back in
```

**Problem: Port conflicts**
```bash
# Solution: Change ports in docker-compose.yml
# Edit the ports section for conflicting services
ports:
  - "8001:8000"  # Changed from 8000:8000
```

**Problem: Container keeps restarting**
```bash
# Solution: Check logs for errors
docker-compose logs api

# Common causes:
# 1. Missing OPENAI_API_KEY in .env
# 2. Database connection issues
# 3. Port conflicts
```

**Problem: Out of disk space**
```bash
# Solution: Clean up Docker resources
docker system prune -a
docker volume prune
```

**Problem: Slow performance on Windows**
```bash
# Solution: Ensure WSL 2 is being used
wsl --set-default-version 2

# Move project to WSL filesystem for better performance
# Access via \\wsl$\Ubuntu\home\user\project
```

### API Issues

**Problem: 500 Internal Server Error**
```bash
# Solution: Check logs
# Local
tail -f logs/app.log

# Docker
docker-compose logs -f api
```

**Problem: Slow response times**
```bash
# Solution: 
# 1. Check OpenAI API status
# 2. Enable Redis caching
# 3. Reduce MAX_ITERATIONS in .env
# 4. Use smaller embedding model
```

**Problem: Vector index not found**
```bash
# Solution: Ingest documents first
python scripts/ingest_documents.py --path ./data/documents

# Or in Docker
docker-compose exec api python scripts/ingest_documents.py --path ./data/documents
```

---

## Quick Reference Commands

### Local Development
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run application
uvicorn src.api.main:app --reload

# Run tests
pytest tests/ -v

# Initialize database
python scripts/init_db.py

# Ingest documents
python scripts/ingest_documents.py --path ./data/documents
```

### Docker Deployment
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build

# Execute commands in container
docker-compose exec api python scripts/init_db.py

# Access container shell
docker-compose exec api bash
```

---

## Environment Variables Reference

### Required
```bash
OPENAI_API_KEY=sk-...          # Your OpenAI API key
```

### Optional (with defaults)
```bash
MODEL_NAME=gpt-4o              # LLM model
TEMPERATURE=0.1                # LLM temperature
VECTOR_DB_TYPE=faiss           # Vector database type
MAX_ITERATIONS=3               # Self-correction iterations
QUALITY_THRESHOLD=0.85         # Quality threshold
LOG_LEVEL=INFO                 # Logging level
API_PORT=8000                  # API port
```

### Database (auto-configured in Docker)
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/agenticai
REDIS_URL=redis://localhost:6379/0
```

---

## Next Steps

After successfully running the application:

1. **Explore the API**: Visit http://localhost:8000/docs
2. **Run Examples**: Check the `examples/` directory
3. **Ingest Your Data**: Use `scripts/ingest_documents.py`
4. **Read Documentation**: See `ARCHITECTURE.md` and `DEPLOYMENT.md`
5. **Run Tests**: Execute `pytest tests/ -v`

---

For production deployment, refer to `DEPLOYMENT.md`.
