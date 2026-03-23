from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.models.schemas import QueryRequest, QueryResponse
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.bm25_service import BM25Service
from app.services.reranker import Reranker
from app.services.rag_pipeline import RAGPipeline

logger = get_logger(__name__)
router = APIRouter()

embedding_service = EmbeddingService()
vector_store = VectorStore()
bm25_service = BM25Service()
reranker = Reranker()

rag_pipeline = RAGPipeline(
    embedding_service=embedding_service,
    vector_store=vector_store,
    bm25_service=bm25_service,
    reranker=reranker
)


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    try:
        logger.info(f"Received query: {request.query[:100]}...")
        
        response = await rag_pipeline.query(
            query=request.query,
            top_k=request.top_k,
            use_reranking=request.use_reranking,
            filters=request.filters
        )
        
        logger.info(f"Query processed successfully, returned {response.total_chunks_retrieved} chunks")
        
        return response
        
    except Exception as e:
        logger.error(f"Query error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.post("/search")
async def search_documents(request: QueryRequest):
    try:
        logger.info(f"Received search request: {request.query[:100]}...")
        
        query_embedding = await embedding_service.generate_embedding(request.query)
        
        dense_results = await vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k,
            filter_dict=request.filters
        )
        
        sparse_results = await bm25_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_dict=request.filters
        )
        
        return {
            "query": request.query,
            "dense_results": [
                {
                    "chunk_id": r.chunk_id,
                    "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                    "score": r.score,
                    "source": r.source
                }
                for r in dense_results
            ],
            "sparse_results": [
                {
                    "chunk_id": r.chunk_id,
                    "text": r.text[:200] + "..." if len(r.text) > 200 else r.text,
                    "score": r.score,
                    "source": r.source
                }
                for r in sparse_results
            ]
        }
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search documents: {str(e)}"
        )
