from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
import uuid
from datetime import datetime

from .models import (
    QueryRequest,
    QueryResponse,
    DocumentIngestRequest,
    DocumentIngestResponse,
    HealthResponse,
    EvaluationRequest,
    EvaluationResponse,
    ErrorResponse
)
from src.graph import AgenticWorkflow
from src.rag import DocumentIngestion, TextChunker, HybridRetriever, CrossEncoderReranker
from src.tools import SQLTools, APITools
from src.memory import ConversationMemory
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import AgenticAIException

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["agentic-ai"])

workflow_instance: AgenticWorkflow = None
retriever_instance: HybridRetriever = None
conversation_memories: Dict[str, ConversationMemory] = {}


def get_workflow() -> AgenticWorkflow:
    global workflow_instance, retriever_instance
    
    if workflow_instance is None:
        try:
            retriever_instance = HybridRetriever()
            try:
                retriever_instance.load_index()
                logger.info("Loaded existing vector index")
            except:
                logger.warning("No existing index found, will create on first ingestion")
            
            reranker = CrossEncoderReranker()
            
            try:
                sql_tools = SQLTools()
            except Exception as e:
                logger.warning(f"SQL tools initialization failed: {str(e)}")
                sql_tools = None
            
            api_tools = APITools()
            
            workflow_instance = AgenticWorkflow(
                retriever=retriever_instance,
                reranker=reranker,
                sql_tools=sql_tools,
                api_tools=api_tools
            )
            
            logger.info("Workflow initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {str(e)}")
            raise
    
    return workflow_instance


@router.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest) -> QueryResponse:
    try:
        workflow = get_workflow()
        
        session_id = request.session_id or str(uuid.uuid4())
        
        if session_id not in conversation_memories:
            conversation_memories[session_id] = ConversationMemory(session_id)
        
        memory = conversation_memories[session_id]
        memory.add_user_message(request.query)
        
        result = await workflow.arun(
            query=request.query,
            use_rag=request.use_rag,
            use_sql=request.use_sql,
            use_api=request.use_api,
            enable_self_correction=request.enable_self_correction,
            max_iterations=request.max_iterations,
            quality_threshold=request.quality_threshold
        )
        
        memory.add_ai_message(result["answer"])
        
        return QueryResponse(
            answer=result["answer"],
            metadata=result["metadata"],
            iterations=result["iterations"],
            session_id=session_id
        )
        
    except AgenticAIException as e:
        logger.error(f"Agentic AI error: {str(e)}")
        raise HTTPException(status_code=500, detail=e.to_dict())
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest", response_model=DocumentIngestResponse)
async def ingest_documents(
    request: DocumentIngestRequest,
    background_tasks: BackgroundTasks
) -> DocumentIngestResponse:
    try:
        ingestion = DocumentIngestion()
        
        if request.text:
            documents = [ingestion.load_from_text(request.text, request.metadata)]
        elif request.file_path:
            documents = ingestion.load_file(request.file_path)
        elif request.directory_path:
            documents = ingestion.load_directory(request.directory_path)
        else:
            raise HTTPException(
                status_code=400,
                detail="Must provide text, file_path, or directory_path"
            )
        
        chunker = TextChunker()
        chunks = chunker.chunk_documents(documents)
        
        global retriever_instance
        if retriever_instance is None:
            retriever_instance = HybridRetriever()
        
        retriever_instance.build_index(chunks)
        
        background_tasks.add_task(retriever_instance.save_index)
        
        logger.info(f"Ingested {len(documents)} documents, created {len(chunks)} chunks")
        
        return DocumentIngestResponse(
            success=True,
            message="Documents ingested successfully",
            documents_processed=len(documents),
            chunks_created=len(chunks),
            index_updated=True
        )
        
    except Exception as e:
        logger.error(f"Error ingesting documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    components = {
        "api": "healthy",
        "workflow": "not_initialized",
        "vector_db": "not_initialized",
        "sql_db": "not_initialized"
    }
    
    try:
        workflow = get_workflow()
        components["workflow"] = "healthy"
        
        if retriever_instance and retriever_instance.vectorstore:
            components["vector_db"] = "healthy"
        
        if workflow.sql_tools:
            components["sql_db"] = "healthy"
    except:
        pass
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat(),
        components=components
    )


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate_response(request: EvaluationRequest) -> EvaluationResponse:
    try:
        from src.evaluation.metrics import evaluate_response
        
        metrics = evaluate_response(
            query=request.query,
            answer=request.answer,
            ground_truth=request.ground_truth,
            contexts=request.contexts
        )
        
        return EvaluationResponse(
            metrics=metrics,
            details={"query": request.query}
        )
        
    except Exception as e:
        logger.error(f"Error during evaluation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/memory/{session_id}")
async def clear_memory(session_id: str) -> Dict[str, str]:
    if session_id in conversation_memories:
        conversation_memories[session_id].clear()
        del conversation_memories[session_id]
        return {"message": f"Memory cleared for session {session_id}"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/memory/{session_id}")
async def get_memory(session_id: str) -> Dict[str, Any]:
    if session_id in conversation_memories:
        memory = conversation_memories[session_id]
        return {
            "session_id": session_id,
            "conversation_history": memory.get_conversation_history()
        }
    else:
        raise HTTPException(status_code=404, detail="Session not found")
