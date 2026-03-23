# Quick Start Guide

Get the Agentic AI Ecosystem up and running in 5 minutes!

## Prerequisites

- Python 3.10+
- OpenAI API Key
- Docker (optional, for containerized deployment)

## Option 1: Quick Local Setup (No Database)

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Windows
set OPENAI_API_KEY=your-key-here

# Linux/Mac
export OPENAI_API_KEY=your-key-here
```

### 3. Run the API

```bash
uvicorn src.api.main:app --reload
```

### 4. Test It!

Open http://localhost:8000/docs and try the `/api/v1/query` endpoint with:

```json
{
  "query": "What are the benefits of AI?",
  "use_rag": false,
  "use_sql": false,
  "use_api": true,
  "enable_self_correction": true
}
```

## Option 2: Full Setup with Docker

### 1. Create .env File

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start All Services

```bash
docker-compose up -d
```

This starts:
- API server (port 8000)
- PostgreSQL (port 5432)
- Redis (port 6379)
- PgAdmin (port 5050)

### 3. Initialize Database

```bash
docker-compose exec api python scripts/init_db.py
```

### 4. Ingest Sample Documents

```bash
docker-compose exec api python scripts/ingest_documents.py --path ./data/documents
```

### 5. Test the API

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What products do we have?",
    "use_rag": true,
    "use_sql": true,
    "enable_self_correction": true
  }'
```

## Option 3: Python Script

Create `test.py`:

```python
import asyncio
from src.graph import AgenticWorkflow
from src.tools import APITools
import os

os.environ['OPENAI_API_KEY'] = 'your-key-here'

async def main():
    api_tools = APITools()
    workflow = AgenticWorkflow(api_tools=api_tools)
    
    result = await workflow.arun(
        query="What is machine learning?",
        use_api=True,
        enable_self_correction=True
    )
    
    print(f"Answer: {result['answer']}")
    print(f"Score: {result['metadata']['final_score']}")
    print(f"Iterations: {result['iterations']}")

asyncio.run(main())
```

Run it:
```bash
python test.py
```

## Common Use Cases

### 1. RAG Query (Knowledge Base)

```python
# First, ingest documents
python scripts/ingest_documents.py --path ./data/documents

# Then query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Summarize the main points from the documents",
    "use_rag": true,
    "use_sql": false,
    "use_api": false
  }'
```

### 2. SQL Query (Database)

```python
# Initialize database first
python scripts/init_db.py

# Query
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top 5 products by price?",
    "use_rag": false,
    "use_sql": true,
    "use_api": false
  }'
```

### 3. Multi-Source Query

```python
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Analyze our product inventory and market trends",
    "use_rag": true,
    "use_sql": true,
    "use_api": true,
    "enable_self_correction": true,
    "max_iterations": 3
  }'
```

## Next Steps

1. **Read the Documentation**: Check `README.md` for detailed features
2. **Explore Examples**: Run scripts in `examples/` directory
3. **Customize Configuration**: Edit `.env` for your needs
4. **Deploy to Production**: Follow `DEPLOYMENT.md`
5. **Review Architecture**: Read `ARCHITECTURE.md` for system design

## Troubleshooting

**API won't start?**
- Check if port 8000 is available
- Verify OPENAI_API_KEY is set
- Check logs: `docker-compose logs -f api`

**Database connection error?**
- Ensure PostgreSQL is running
- Check DATABASE_URL in .env
- Wait 10 seconds after `docker-compose up`

**Vector index not found?**
- Run document ingestion first
- Check `./data/vectorstore/` exists
- Verify file permissions

## Support

- Documentation: `README.md`, `ARCHITECTURE.md`, `DEPLOYMENT.md`
- Examples: `examples/` directory
- Tests: `pytest tests/ -v`

Happy coding! 🚀
