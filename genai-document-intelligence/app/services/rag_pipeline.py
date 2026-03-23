from typing import List, Dict, Any, Optional
import time
from openai import OpenAI
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import RAGPipelineError
from app.models.schemas import SearchResult, QueryResponse, RetrievedChunk
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.bm25_service import BM25Service
from app.services.reranker import Reranker
from app.utils.text_utils import optimize_context_window, count_tokens
from app.utils.metrics import track_time, retrieval_latency, llm_latency, query_counter

logger = get_logger(__name__)


class RAGPipeline:
    
    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore,
        bm25_service: BM25Service,
        reranker: Reranker
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store
        self.bm25_service = bm25_service
        self.reranker = reranker
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        logger.info("RAGPipeline initialized")
    
    async def query(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = True,
        filters: Optional[Dict[str, Any]] = None
    ) -> QueryResponse:
        try:
            start_time = time.time()
            query_counter.inc()
            
            logger.info(f"Processing query: {query[:100]}...")
            
            retrieved_chunks = await self._hybrid_search(
                query=query,
                top_k=top_k,
                use_reranking=use_reranking,
                filters=filters
            )
            
            if not retrieved_chunks:
                logger.warning("No chunks retrieved for query")
                return QueryResponse(
                    query=query,
                    answer="I couldn't find any relevant information to answer your question.",
                    retrieved_chunks=[],
                    total_chunks_retrieved=0,
                    confidence_score=0.0,
                    processing_time=time.time() - start_time,
                    metadata={"status": "no_results"}
                )
            
            context = self._build_context(retrieved_chunks)
            
            answer = await self._generate_answer(query, context)
            
            confidence_score = self._calculate_confidence(retrieved_chunks)
            
            retrieved_chunk_models = [
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    text=chunk.text,
                    score=chunk.score,
                    metadata=chunk.metadata,
                    rank=idx + 1
                )
                for idx, chunk in enumerate(retrieved_chunks)
            ]
            
            processing_time = time.time() - start_time
            
            logger.info(f"Query processed successfully in {processing_time:.2f}s")
            
            return QueryResponse(
                query=query,
                answer=answer,
                retrieved_chunks=retrieved_chunk_models,
                total_chunks_retrieved=len(retrieved_chunks),
                confidence_score=confidence_score,
                processing_time=processing_time,
                metadata={
                    "use_reranking": use_reranking,
                    "top_k": top_k,
                    "context_tokens": count_tokens(context)
                }
            )
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {str(e)}")
            raise RAGPipelineError(f"Query processing failed: {str(e)}")
    
    @track_time(retrieval_latency)
    async def _hybrid_search(
        self,
        query: str,
        top_k: int,
        use_reranking: bool,
        filters: Optional[Dict[str, Any]]
    ) -> List[SearchResult]:
        try:
            logger.info("Performing hybrid search (dense + sparse)")
            
            query_embedding = await self.embedding_service.generate_embedding(query)
            
            retrieval_k = settings.TOP_K_RETRIEVAL if use_reranking else top_k
            
            dense_results = await self.vector_store.search(
                query_embedding=query_embedding,
                top_k=retrieval_k,
                filter_dict=filters
            )
            
            sparse_results = await self.bm25_service.search(
                query=query,
                top_k=retrieval_k,
                filter_dict=filters
            )
            
            combined_results = self._combine_results(
                dense_results=dense_results,
                sparse_results=sparse_results,
                dense_weight=settings.DENSE_WEIGHT,
                sparse_weight=settings.SPARSE_WEIGHT
            )
            
            if use_reranking and settings.USE_RERANKING:
                logger.info("Applying cross-encoder reranking")
                reranked_results = await self.reranker.rerank(
                    query=query,
                    results=combined_results,
                    top_k=top_k
                )
                return reranked_results
            else:
                return combined_results[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            raise RAGPipelineError(f"Hybrid search failed: {str(e)}")
    
    def _combine_results(
        self,
        dense_results: List[SearchResult],
        sparse_results: List[SearchResult],
        dense_weight: float,
        sparse_weight: float
    ) -> List[SearchResult]:
        try:
            chunk_scores: Dict[str, Dict[str, Any]] = {}
            
            for result in dense_results:
                chunk_scores[result.chunk_id] = {
                    "result": result,
                    "dense_score": result.score,
                    "sparse_score": 0.0
                }
            
            for result in sparse_results:
                if result.chunk_id in chunk_scores:
                    chunk_scores[result.chunk_id]["sparse_score"] = result.score
                else:
                    chunk_scores[result.chunk_id] = {
                        "result": result,
                        "dense_score": 0.0,
                        "sparse_score": result.score
                    }
            
            max_dense = max([s["dense_score"] for s in chunk_scores.values()]) if chunk_scores else 1.0
            max_sparse = max([s["sparse_score"] for s in chunk_scores.values()]) if chunk_scores else 1.0
            
            max_dense = max_dense if max_dense > 0 else 1.0
            max_sparse = max_sparse if max_sparse > 0 else 1.0
            
            combined_results = []
            for chunk_id, scores in chunk_scores.items():
                normalized_dense = scores["dense_score"] / max_dense
                normalized_sparse = scores["sparse_score"] / max_sparse
                
                combined_score = (
                    dense_weight * normalized_dense +
                    sparse_weight * normalized_sparse
                )
                
                result = scores["result"]
                combined_result = SearchResult(
                    chunk_id=result.chunk_id,
                    text=result.text,
                    score=combined_score,
                    source=result.source,
                    metadata={
                        **result.metadata,
                        "dense_score": scores["dense_score"],
                        "sparse_score": scores["sparse_score"],
                        "combined_score": combined_score
                    }
                )
                combined_results.append(combined_result)
            
            combined_results.sort(key=lambda x: x.score, reverse=True)
            
            logger.info(f"Combined {len(dense_results)} dense + {len(sparse_results)} sparse = {len(combined_results)} unique results")
            return combined_results
            
        except Exception as e:
            logger.error(f"Result combination error: {str(e)}")
            return dense_results
    
    def _build_context(self, chunks: List[SearchResult]) -> str:
        try:
            chunk_texts = [chunk.text for chunk in chunks]
            
            if settings.CONTEXT_OPTIMIZATION:
                optimized_chunks = optimize_context_window(
                    chunks=chunk_texts,
                    max_tokens=settings.MAX_CONTEXT_LENGTH,
                    model=settings.OPENAI_MODEL
                )
                chunk_texts = optimized_chunks
            
            context_parts = []
            for idx, text in enumerate(chunk_texts, 1):
                context_parts.append(f"[Document {idx}]\n{text}")
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"Built context from {len(chunk_texts)} chunks, {count_tokens(context)} tokens")
            return context
            
        except Exception as e:
            logger.error(f"Context building error: {str(e)}")
            return "\n\n".join([chunk.text for chunk in chunks])
    
    @track_time(llm_latency)
    async def _generate_answer(self, query: str, context: str) -> str:
        try:
            logger.info("Generating answer with LLM")
            
            system_prompt = """You are a helpful AI assistant that answers questions based on the provided context.
Follow these guidelines:
1. Answer the question using ONLY the information from the provided context
2. If the context doesn't contain enough information, say so clearly
3. Be concise and accurate
4. Cite specific parts of the context when relevant
5. If you're uncertain, express that uncertainty"""
            
            user_prompt = f"""Context:
{context}

Question: {query}

Please provide a comprehensive answer based on the context above."""
            
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=settings.OPENAI_TEMPERATURE,
                max_tokens=settings.OPENAI_MAX_TOKENS
            )
            
            answer = response.choices[0].message.content
            
            logger.info("Answer generated successfully")
            return answer
            
        except Exception as e:
            logger.error(f"Answer generation error: {str(e)}")
            raise RAGPipelineError(f"Failed to generate answer: {str(e)}")
    
    def _calculate_confidence(self, chunks: List[SearchResult]) -> float:
        try:
            if not chunks:
                return 0.0
            
            scores = [chunk.score for chunk in chunks]
            
            avg_score = sum(scores) / len(scores)
            
            top_score = scores[0] if scores else 0.0
            
            score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            consistency = 1.0 / (1.0 + score_variance)
            
            confidence = (0.6 * top_score + 0.3 * avg_score + 0.1 * consistency)
            
            return min(max(confidence, 0.0), 1.0)
            
        except Exception as e:
            logger.error(f"Confidence calculation error: {str(e)}")
            return 0.5
