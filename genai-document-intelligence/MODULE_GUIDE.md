# Module Guide

Complete explanation of each module in the GenAI Document Intelligence Platform.

## Table of Contents

1. [Core Configuration](#core-configuration)
2. [Services Layer](#services-layer)
3. [API Layer](#api-layer)
4. [Models](#models)
5. [Utilities](#utilities)

---

## Core Configuration

### `app/core/config.py`

**Purpose**: Centralized configuration management using Pydantic Settings

**Key Features**:
- Environment variable loading from `.env`
- Type validation and conversion
- Default values for all settings
- Singleton pattern with `@lru_cache`

**Main Settings**:
```python
- OPENAI_API_KEY: OpenAI authentication
- PINECONE_API_KEY: Pinecone authentication
- CHUNK_SIZE: Document chunk size (default: 512)
- TOP_K_RETRIEVAL: Number of candidates (default: 20)
- DENSE_WEIGHT: Semantic search weight (default: 0.7)
- SPARSE_WEIGHT: Keyword search weight (default: 0.3)
```

### `app/core/logging.py`

**Purpose**: Structured logging with JSON output

**Features**:
- Structlog integration
- JSON or console output
- Contextual logging
- Log level configuration

**Usage**:
```python
from app.core.logging import get_logger
logger = get_logger(__name__)
logger.info("Processing document", document_id=doc_id)
```

### `app/core/exceptions.py`

**Purpose**: Custom exception hierarchy for error handling

**Exception Classes**:
- `BaseAPIException`: Base class with status codes
- `DocumentProcessingError`: Document handling errors
- `EmbeddingGenerationError`: Embedding failures
- `VectorStoreError`: Vector DB operations
- `RetrievalError`: Search failures
- `RerankingError`: Reranking issues
- `RAGPipelineError`: Pipeline errors
- `EvaluationError`: Evaluation failures

---

## Services Layer

### `app/services/document_processor.py`

**Purpose**: Extract and chunk documents from multiple formats

**Supported Formats**:
- PDF (pypdf)
- DOCX (python-docx)
- TXT (plain text)
- PPTX (python-pptx)

**Key Methods**:
- `process_document()`: Main entry point
- `_extract_text()`: Format-specific extraction
- `_chunk_text()`: Recursive chunking with overlap

**Chunking Strategy**:
```python
RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ". ", " ", ""]
)
```

**Output**: List of `DocumentChunk` objects with metadata

### `app/services/embedding_service.py`

**Purpose**: Generate embeddings using OpenAI API

**Features**:
- Single embedding generation
- Batch processing (100 texts/batch)
- Cosine similarity calculation
- Vector normalization

**Model**: `text-embedding-3-small` (1536 dimensions)

**Key Methods**:
```python
- generate_embedding(text): Single embedding
- generate_embeddings_batch(texts): Batch processing
- cosine_similarity(vec1, vec2): Similarity score
```

**Performance**: Batching reduces API calls and improves throughput

### `app/services/vector_store.py`

**Purpose**: Pinecone vector database integration

**Features**:
- Index creation and management
- Batch upsert (100 vectors/batch)
- Similarity search
- Metadata filtering
- Document deletion

**Key Methods**:
```python
- upsert_chunks(chunks): Add vectors to index
- search(query_embedding, top_k): Dense retrieval
- delete_by_document_id(doc_id): Remove document
- get_stats(): Index statistics
```

**Index Configuration**:
- Metric: Cosine similarity
- Dimension: 1536
- Serverless deployment

### `app/services/bm25_service.py`

**Purpose**: BM25 sparse retrieval with local index

**Features**:
- Okapi BM25 algorithm
- Persistent local index (pickle)
- Tokenization and scoring
- Document filtering

**Key Methods**:
```python
- add_documents(docs): Index documents
- search(query, top_k): Keyword search
- delete_by_document_id(doc_id): Remove docs
- clear_index(): Reset index
```

**Storage**: Serialized to `data/bm25_index.pkl`

**Algorithm**: BM25Okapi from rank-bm25 library

### `app/services/reranker.py`

**Purpose**: Cross-encoder reranking for precision improvement

**Model**: `cross-encoder/ms-marco-MiniLM-L-6-v2`

**Features**:
- Query-document pair scoring
- Top-k selection
- Score normalization

**Key Methods**:
```python
- rerank(query, results, top_k): Rerank results
- score_pairs(query, texts): Score multiple pairs
```

**Performance**: ~100ms for 20 candidates

**Improvement**: Typically 10-15% precision gain over bi-encoder alone

### `app/services/rag_pipeline.py`

**Purpose**: Orchestrate hybrid search and answer generation

**Workflow**:
1. Generate query embedding
2. Dense search (Pinecone)
3. Sparse search (BM25)
4. Combine and normalize scores
5. Cross-encoder reranking
6. Build optimized context
7. Generate answer with LLM

**Key Methods**:
```python
- query(query, top_k, use_reranking): Main pipeline
- _hybrid_search(): Combine dense + sparse
- _combine_results(): Score fusion
- _build_context(): Context optimization
- _generate_answer(): LLM generation
```

**Score Fusion**:
```python
combined_score = (0.7 * normalized_dense) + (0.3 * normalized_sparse)
```

**Context Optimization**:
- Token counting with tiktoken
- Truncation to max context length
- Intelligent chunk selection

### `app/services/evaluator.py`

**Purpose**: RAGAS-based evaluation framework

**Metrics**:
- **Faithfulness**: Answer grounded in context (0-1)
- **Answer Relevancy**: Answer addresses question (0-1)
- **Context Precision**: Relevant chunks ranked higher (0-1)
- **Context Recall**: All relevant info retrieved (0-1)
- **Context Relevancy**: Retrieved chunks are relevant (0-1)

**Key Methods**:
```python
- evaluate_rag_system(questions, answers, contexts, ground_truths)
- evaluate_single_response(question, answer, contexts)
- calculate_custom_metrics(retrieved, relevant)
```

**Output**: Individual and average scores for all metrics

---

## API Layer

### `app/api/ingestion.py`

**Endpoints**:

#### `POST /api/v1/ingest`
Upload and process documents

**Request**: Multipart form with file
**Response**: Document ID, chunk count, processing time

**Process**:
1. Validate file type and size
2. Extract text
3. Chunk document
4. Generate embeddings
5. Index in Pinecone and BM25
6. Return metadata

#### `DELETE /api/v1/document/{document_id}`
Remove document from all indexes

#### `GET /api/v1/stats`
Get system statistics (vector count, index size)

### `app/api/query.py`

**Endpoints**:

#### `POST /api/v1/query`
Main RAG query endpoint

**Request**:
```json
{
  "query": "What is machine learning?",
  "top_k": 5,
  "use_reranking": true,
  "filters": {"source": "research.pdf"}
}
```

**Response**:
```json
{
  "query": "...",
  "answer": "...",
  "retrieved_chunks": [...],
  "confidence_score": 0.85,
  "processing_time": 1.23
}
```

#### `POST /api/v1/search`
Search-only endpoint (no answer generation)

**Returns**: Dense and sparse search results separately

### `app/api/evaluation.py`

**Endpoints**:

#### `POST /api/v1/evaluate`
Evaluate system with multiple questions

**Request**:
```json
{
  "questions": ["Q1", "Q2"],
  "ground_truths": ["A1", "A2"]
}
```

**Response**: RAGAS metrics and scores

#### `POST /api/v1/evaluate-single`
Evaluate single query-answer pair

---

## Models

### `app/models/schemas.py`

**Pydantic Models** for request/response validation:

**Request Models**:
- `IngestionRequest`: Document upload
- `QueryRequest`: Query with validation
- `EvaluationRequest`: Evaluation data

**Response Models**:
- `IngestionResponse`: Upload results
- `QueryResponse`: Query results with chunks
- `EvaluationResponse`: Metrics and scores
- `HealthResponse`: System health status
- `ErrorResponse`: Error details

**Data Models**:
- `DocumentChunk`: Chunk with metadata
- `ChunkMetadata`: Source, page, timestamps
- `SearchResult`: Retrieved chunk with score
- `RetrievedChunk`: Query result chunk
- `RAGASMetrics`: Evaluation metrics

**Features**:
- Automatic validation
- Type conversion
- Default values
- Custom validators

---

## Utilities

### `app/utils/text_utils.py`

**Text Processing Functions**:

- `clean_text(text)`: Remove extra whitespace
- `count_tokens(text, model)`: Token counting with tiktoken
- `truncate_text(text, max_tokens)`: Intelligent truncation
- `split_into_sentences(text)`: Sentence segmentation
- `extract_keywords(text, top_n)`: Keyword extraction
- `calculate_text_similarity(text1, text2)`: Jaccard similarity
- `optimize_context_window(chunks, max_tokens)`: Context optimization

**Key Algorithm - Context Optimization**:
```python
def optimize_context_window(chunks, max_tokens):
    optimized = []
    current_tokens = 0
    
    for chunk in chunks:
        chunk_tokens = count_tokens(chunk)
        if current_tokens + chunk_tokens <= max_tokens:
            optimized.append(chunk)
            current_tokens += chunk_tokens
        else:
            # Truncate last chunk if space remains
            remaining = max_tokens - current_tokens
            if remaining > 50:
                optimized.append(truncate_text(chunk, remaining))
            break
    
    return optimized
```

### `app/utils/metrics.py`

**Prometheus Metrics**:

- `query_counter`: Total queries processed
- `ingestion_counter`: Documents ingested
- `retrieval_latency`: Retrieval time histogram
- `reranking_latency`: Reranking time histogram
- `llm_latency`: LLM generation time
- `active_requests`: Current active requests
- `retrieval_precision`: Precision gauge

**Decorators**:
```python
@track_time(retrieval_latency)
async def search_function():
    # Automatically tracked
    pass
```

**Custom Metrics**:
- `calculate_precision_at_k(retrieved, relevant, k)`
- `calculate_recall_at_k(retrieved, relevant, k)`
- `calculate_mrr(retrieved, relevant)`: Mean Reciprocal Rank
- `calculate_ndcg_at_k(retrieved, scores, k)`: NDCG

---

## Main Application

### `app/main.py`

**FastAPI Application Setup**:

**Features**:
- CORS middleware
- Request logging middleware
- Exception handlers
- Health check endpoint
- Metrics endpoint (Prometheus)
- API documentation (Swagger/ReDoc)

**Middleware**:
```python
@app.middleware("http")
async def log_requests(request, call_next):
    # Log all requests with timing
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("Request", path=request.url.path, duration=duration)
    return response
```

**Exception Handling**:
- Custom exceptions → Structured error responses
- Unhandled exceptions → 500 with details (dev mode)
- Logging for all errors

**Startup/Shutdown Events**:
- Initialize services
- Log startup information
- Graceful shutdown

---

## Integration Flow

### Document Ingestion Flow

```
User uploads file
    ↓
FastAPI receives (ingestion.py)
    ↓
DocumentProcessor extracts text
    ↓
Text chunked with overlap
    ↓
EmbeddingService generates vectors (batch)
    ↓
VectorStore upserts to Pinecone
    ↓
BM25Service indexes locally
    ↓
Return document_id and stats
```

### Query Flow

```
User sends query
    ↓
FastAPI receives (query.py)
    ↓
RAGPipeline.query()
    ↓
├─ EmbeddingService: Generate query embedding
├─ VectorStore: Dense search (top 20)
├─ BM25Service: Sparse search (top 20)
└─ Combine scores (70% dense + 30% sparse)
    ↓
Reranker: Cross-encoder scoring (top 5)
    ↓
Build optimized context (max 4000 tokens)
    ↓
LLM: Generate grounded answer
    ↓
Return answer + chunks + metadata
```

---

## Best Practices

### Error Handling
```python
try:
    result = await service.process()
except SpecificError as e:
    logger.error("Specific error", error=str(e))
    raise CustomException(f"Failed: {str(e)}")
```

### Logging
```python
logger.info("Operation started", 
    document_id=doc_id,
    chunk_count=len(chunks))
```

### Configuration
```python
from app.core.config import settings
chunk_size = settings.CHUNK_SIZE
```

### Testing
```python
@pytest.mark.asyncio
async def test_function():
    result = await async_function()
    assert result is not None
```

---

## Performance Considerations

### Batching
- Embeddings: 100 texts per batch
- Vector upserts: 100 vectors per batch
- Reduces API calls by 100x

### Caching
- Redis for query results (future)
- Embedding cache (future)
- BM25 index persistence

### Async Operations
- All I/O operations are async
- Non-blocking API calls
- Concurrent processing where possible

### Context Optimization
- Token counting before LLM call
- Intelligent truncation
- 25% cost reduction achieved

---

## Extension Points

### Adding New Document Types
1. Add parser in `document_processor.py`
2. Update `DocumentType` enum
3. Add extraction method

### Custom Retrieval Strategies
1. Implement in new service class
2. Integrate in `rag_pipeline.py`
3. Add configuration options

### Additional Metrics
1. Define in `metrics.py`
2. Track in relevant services
3. Expose via `/metrics` endpoint

### New Evaluation Metrics
1. Add to `evaluator.py`
2. Integrate RAGAS or custom logic
3. Update response schemas
