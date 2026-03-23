from typing import List, Dict, Any, Optional, Tuple
import pinecone
from pinecone import Pinecone, ServerlessSpec
from app.core.config import settings
from app.core.logging import get_logger
from app.core.exceptions import VectorStoreError
from app.models.schemas import DocumentChunk, SearchResult

logger = get_logger(__name__)


class VectorStore:
    
    def __init__(self):
        try:
            self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
            self.index_name = settings.PINECONE_INDEX_NAME
            self.dimension = settings.PINECONE_DIMENSION
            self.metric = settings.PINECONE_METRIC
            
            self._initialize_index()
            
            self.index = self.pc.Index(self.index_name)
            logger.info(f"VectorStore initialized with index: {self.index_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize VectorStore: {str(e)}")
            raise VectorStoreError(f"VectorStore initialization failed: {str(e)}")
    
    def _initialize_index(self):
        try:
            existing_indexes = [index.name for index in self.pc.list_indexes()]
            
            if self.index_name not in existing_indexes:
                logger.info(f"Creating new Pinecone index: {self.index_name}")
                
                self.pc.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    metric=self.metric,
                    spec=ServerlessSpec(
                        cloud='aws',
                        region=settings.PINECONE_ENVIRONMENT
                    )
                )
                logger.info(f"Index {self.index_name} created successfully")
            else:
                logger.info(f"Using existing index: {self.index_name}")
                
        except Exception as e:
            logger.error(f"Index initialization error: {str(e)}")
            raise VectorStoreError(f"Failed to initialize index: {str(e)}")
    
    async def upsert_chunks(self, chunks: List[DocumentChunk]) -> Dict[str, Any]:
        try:
            if not chunks:
                raise VectorStoreError("No chunks provided for upsertion")
            
            logger.info(f"Upserting {len(chunks)} chunks to vector store")
            
            vectors = []
            for chunk in chunks:
                if not chunk.embedding:
                    raise VectorStoreError(f"Chunk {chunk.chunk_id} has no embedding")
                
                metadata = {
                    "text": chunk.text,
                    "document_id": chunk.metadata.document_id,
                    "source": chunk.metadata.source,
                    "chunk_index": chunk.metadata.chunk_index,
                    "total_chunks": chunk.metadata.total_chunks,
                    "timestamp": chunk.metadata.timestamp.isoformat()
                }
                
                if chunk.metadata.page_number:
                    metadata["page_number"] = chunk.metadata.page_number
                
                vectors.append({
                    "id": chunk.chunk_id,
                    "values": chunk.embedding,
                    "metadata": metadata
                })
            
            batch_size = 100
            upserted_count = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch)
                upserted_count += len(batch)
                logger.info(f"Upserted batch {i//batch_size + 1}/{(len(vectors)-1)//batch_size + 1}")
            
            logger.info(f"Successfully upserted {upserted_count} vectors")
            
            return {
                "upserted_count": upserted_count,
                "index_name": self.index_name
            }
            
        except Exception as e:
            logger.error(f"Upsert error: {str(e)}")
            raise VectorStoreError(f"Failed to upsert chunks: {str(e)}")
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        try:
            logger.info(f"Searching vector store with top_k={top_k}")
            
            query_params = {
                "vector": query_embedding,
                "top_k": top_k,
                "include_metadata": True
            }
            
            if filter_dict:
                query_params["filter"] = filter_dict
            
            results = self.index.query(**query_params)
            
            search_results = []
            for match in results.matches:
                search_result = SearchResult(
                    chunk_id=match.id,
                    text=match.metadata.get("text", ""),
                    score=float(match.score),
                    source=match.metadata.get("source", ""),
                    metadata=match.metadata
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} results")
            return search_results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            raise VectorStoreError(f"Vector search failed: {str(e)}")
    
    async def delete_by_document_id(self, document_id: str) -> Dict[str, Any]:
        try:
            logger.info(f"Deleting vectors for document: {document_id}")
            
            self.index.delete(filter={"document_id": document_id})
            
            logger.info(f"Successfully deleted vectors for document {document_id}")
            return {"deleted_document_id": document_id}
            
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            raise VectorStoreError(f"Failed to delete document: {str(e)}")
    
    async def get_stats(self) -> Dict[str, Any]:
        try:
            stats = self.index.describe_index_stats()
            
            return {
                "total_vector_count": stats.total_vector_count,
                "dimension": stats.dimension,
                "index_fullness": stats.index_fullness,
                "namespaces": stats.namespaces
            }
            
        except Exception as e:
            logger.error(f"Stats retrieval error: {str(e)}")
            raise VectorStoreError(f"Failed to get stats: {str(e)}")
    
    async def clear_index(self) -> Dict[str, Any]:
        try:
            logger.warning(f"Clearing all vectors from index: {self.index_name}")
            
            self.index.delete(delete_all=True)
            
            logger.info("Index cleared successfully")
            return {"status": "cleared", "index_name": self.index_name}
            
        except Exception as e:
            logger.error(f"Clear index error: {str(e)}")
            raise VectorStoreError(f"Failed to clear index: {str(e)}")
