# Quick Start Guide

Get the GenAI Document Intelligence Platform running in 5 minutes!

## Prerequisites

- Python 3.9+
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))
- Pinecone API key ([Get one here](https://www.pinecone.io/))

## Installation

### 1. Set Up Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy environment template
copy .env.example .env  # Windows
cp .env.example .env    # macOS/Linux
```

Edit `.env` and add your keys:
```env
OPENAI_API_KEY=sk-your-key-here
PINECONE_API_KEY=your-key-here
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=doc-intelligence
```

### 3. Start the Server

```bash
uvicorn app.main:app --reload
```

The API will be available at: http://localhost:8000

## First Steps

### 1. Check Health

```bash
curl http://localhost:8000/health
```

### 2. Upload a Document

```bash
curl -X POST "http://localhost:8000/api/v1/ingest" \
  -F "file=@your_document.pdf"
```

### 3. Query the System

```bash
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is this document about?",
    "top_k": 5,
    "use_reranking": true
  }'
```

## Using the Interactive API Docs

Visit http://localhost:8000/docs for a full interactive API documentation where you can:
- Upload documents
- Test queries
- Run evaluations
- View all endpoints

## Python Client Example

```python
import requests

BASE_URL = "http://localhost:8000"

# 1. Upload a document
with open("document.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/api/v1/ingest", files=files)
    print(f"Document ID: {response.json()['document_id']}")

# 2. Query the document
query_data = {
    "query": "What are the main findings?",
    "top_k": 5,
    "use_reranking": True
}
response = requests.post(f"{BASE_URL}/api/v1/query", json=query_data)
result = response.json()

print(f"Answer: {result['answer']}")
print(f"Confidence: {result['confidence_score']:.2f}")
print(f"Retrieved {result['total_chunks_retrieved']} chunks")
```

## Docker Quick Start

```bash
# Navigate to docker directory
cd docker

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

## Common Commands

### Run Tests
```bash
pytest tests/ -v
```

### Check Code Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

### View Metrics
```bash
curl http://localhost:8000/metrics
```

### Get System Stats
```bash
curl http://localhost:8000/api/v1/stats
```

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env
API_PORT=8001

# Or specify when running
uvicorn app.main:app --port 8001
```

### API Key Errors
- Verify keys in `.env` file
- Check key validity on provider websites
- Ensure no extra spaces in keys

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Pinecone Index Issues
- Verify index name matches `.env`
- Check Pinecone dashboard for index status
- Ensure environment/region is correct

## Next Steps

1. **Read the Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
2. **Deployment Guide**: See [DEPLOYMENT.md](DEPLOYMENT.md)
3. **Full Documentation**: Visit http://localhost:8000/docs
4. **Run Examples**: Check `examples/usage_example.py`

## Support

- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **GitHub Issues**: [Report a bug](https://github.com/yourusername/genai-doc-intelligence/issues)

## Key Features to Try

### 1. Hybrid Search
Compare dense vs sparse vs hybrid retrieval:
```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "machine learning", "top_k": 5}'
```

### 2. Reranking
Test with and without reranking:
```bash
# With reranking
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "use_reranking": true}'

# Without reranking
curl -X POST "http://localhost:8000/api/v1/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "use_reranking": false}'
```

### 3. Evaluation
Evaluate system performance:
```bash
curl -X POST "http://localhost:8000/api/v1/evaluate" \
  -H "Content-Type: application/json" \
  -d '{
    "questions": ["What is RAG?"],
    "ground_truths": ["RAG is Retrieval-Augmented Generation"]
  }'
```

## Performance Tips

1. **Batch Upload**: Upload multiple documents for better throughput
2. **Cache Results**: Use Redis for frequently asked queries
3. **Adjust top_k**: Lower values = faster responses
4. **Monitor Metrics**: Track performance at `/metrics`

## Configuration Tuning

Edit `.env` to optimize for your use case:

```env
# Chunking
CHUNK_SIZE=512          # Smaller = more chunks, better precision
CHUNK_OVERLAP=50        # Higher = better context continuity

# Retrieval
TOP_K_RETRIEVAL=20      # More candidates for reranking
TOP_K_RERANK=5          # Final results returned

# Weights
DENSE_WEIGHT=0.7        # Semantic search importance
SPARSE_WEIGHT=0.3       # Keyword search importance
```

Happy building! 🚀
