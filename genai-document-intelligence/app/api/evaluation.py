from fastapi import APIRouter, HTTPException
from typing import List
from app.core.logging import get_logger
from app.models.schemas import EvaluationRequest, EvaluationResponse
from app.services.evaluator import Evaluator
from app.services.rag_pipeline import RAGPipeline
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.bm25_service import BM25Service
from app.services.reranker import Reranker

logger = get_logger(__name__)
router = APIRouter()

evaluator = Evaluator()

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


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_system(request: EvaluationRequest):
    try:
        logger.info(f"Received evaluation request with {len(request.questions)} questions")
        
        answers = request.answers
        contexts = request.contexts
        
        if not answers or not contexts:
            logger.info("Generating answers and contexts from RAG pipeline")
            
            answers = []
            contexts = []
            
            for question in request.questions:
                response = await rag_pipeline.query(
                    query=question,
                    top_k=5,
                    use_reranking=True
                )
                
                answers.append(response.answer)
                
                question_contexts = [chunk.text for chunk in response.retrieved_chunks]
                contexts.append(question_contexts)
        
        evaluation_result = await evaluator.evaluate_rag_system(
            questions=request.questions,
            answers=answers,
            contexts=contexts,
            ground_truths=request.ground_truths
        )
        
        logger.info("Evaluation completed successfully")
        
        return evaluation_result
        
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate system: {str(e)}"
        )


@router.post("/evaluate-single")
async def evaluate_single_query(
    question: str,
    answer: str = None,
    contexts: List[str] = None,
    ground_truth: str = None
):
    try:
        logger.info(f"Evaluating single query: {question[:100]}...")
        
        if not answer or not contexts:
            response = await rag_pipeline.query(
                query=question,
                top_k=5,
                use_reranking=True
            )
            
            answer = response.answer
            contexts = [chunk.text for chunk in response.retrieved_chunks]
        
        scores = await evaluator.evaluate_single_response(
            question=question,
            answer=answer,
            contexts=contexts,
            ground_truth=ground_truth
        )
        
        return {
            "question": question,
            "answer": answer,
            "scores": scores
        }
        
    except Exception as e:
        logger.error(f"Single evaluation error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to evaluate query: {str(e)}"
        )
