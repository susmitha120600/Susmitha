from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import Optional
import os
import time
import tempfile
import shutil
from app.core.logging import get_logger
from app.models.schemas import IngestionResponse, DocumentType
from app.services.document_processor import DocumentProcessor
from app.services.embedding_service import EmbeddingService
from app.services.vector_store import VectorStore
from app.services.bm25_service import BM25Service
from app.utils.metrics import ingestion_counter

logger = get_logger(__name__)
router = APIRouter()


document_processor = DocumentProcessor()
embedding_service = EmbeddingService()
vector_store = VectorStore()
bm25_service = BM25Service()


@router.post("/ingest", response_model=IngestionResponse)
async def ingest_document(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    start_time = time.time()
    temp_file_path = None
    
    try:
        logger.info(f"Received file for ingestion: {file.filename}")
        
        file_extension = os.path.splitext(file.filename)[1].lower().replace('.', '')
        
        try:
            document_type = DocumentType(file_extension)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {file_extension}. Supported types: pdf, docx, txt, pptx"
            )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{file_extension}") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        logger.info(f"File saved to temporary location: {temp_file_path}")
        
        document_processor.validate_file(temp_file_path)
        
        chunks = await document_processor.process_document(
            file_path=temp_file_path,
            document_type=document_type,
            metadata={"filename": file.filename}
        )
        
        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No chunks were created from the document"
            )
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        chunk_texts = [chunk.text for chunk in chunks]
        embeddings = await embedding_service.generate_embeddings_batch(chunk_texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        logger.info("Upserting chunks to vector store")
        await vector_store.upsert_chunks(chunks)
        
        logger.info("Adding chunks to BM25 index")
        bm25_documents = [
            {
                "chunk_id": chunk.chunk_id,
                "text": chunk.text,
                "document_id": chunk.metadata.document_id,
                "source": chunk.metadata.source,
                "metadata": chunk.metadata.dict()
            }
            for chunk in chunks
        ]
        await bm25_service.add_documents(bm25_documents)
        
        ingestion_counter.inc()
        
        processing_time = time.time() - start_time
        
        document_id = chunks[0].metadata.document_id
        
        logger.info(f"Document ingestion completed successfully in {processing_time:.2f}s")
        
        return IngestionResponse(
            document_id=document_id,
            file_name=file.filename,
            total_chunks=len(chunks),
            status="success",
            message=f"Document ingested successfully with {len(chunks)} chunks",
            processing_time=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {str(e)}")


@router.delete("/document/{document_id}")
async def delete_document(document_id: str):
    try:
        logger.info(f"Deleting document: {document_id}")
        
        await vector_store.delete_by_document_id(document_id)
        await bm25_service.delete_by_document_id(document_id)
        
        logger.info(f"Document {document_id} deleted successfully")
        
        return {
            "status": "success",
            "message": f"Document {document_id} deleted successfully"
        }
        
    except Exception as e:
        logger.error(f"Delete error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/stats")
async def get_ingestion_stats():
    try:
        vector_stats = await vector_store.get_stats()
        bm25_stats = bm25_service.get_stats()
        
        return {
            "vector_store": vector_stats,
            "bm25_index": bm25_stats
        }
        
    except Exception as e:
        logger.error(f"Stats retrieval error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve stats: {str(e)}"
        )
