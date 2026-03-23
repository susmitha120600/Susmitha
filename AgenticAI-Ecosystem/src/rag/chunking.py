from typing import List, Optional
from langchain.text_splitter import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    TokenTextSplitter
)
from langchain.schema import Document
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class TextChunker:
    
    def __init__(
        self,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None,
        strategy: str = "recursive"
    ):
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP
        self.strategy = strategy
        
        self.splitter = self._get_splitter()
    
    def _get_splitter(self):
        if self.strategy == "recursive":
            return RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", ". ", " ", ""]
            )
        elif self.strategy == "character":
            return CharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separator="\n"
            )
        elif self.strategy == "token":
            return TokenTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        else:
            raise ValueError(f"Unknown chunking strategy: {self.strategy}")
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        if not documents:
            logger.warning("No documents provided for chunking")
            return []
        
        try:
            chunks = self.splitter.split_documents(documents)
            
            for i, chunk in enumerate(chunks):
                chunk.metadata['chunk_id'] = i
                chunk.metadata['chunk_size'] = len(chunk.page_content)
            
            logger.info(
                f"Chunked {len(documents)} documents into {len(chunks)} chunks "
                f"(strategy={self.strategy}, size={self.chunk_size}, overlap={self.chunk_overlap})"
            )
            
            return chunks
            
        except Exception as e:
            logger.error(f"Error during chunking: {str(e)}")
            raise
    
    def chunk_text(self, text: str, metadata: Optional[dict] = None) -> List[Document]:
        doc = Document(page_content=text, metadata=metadata or {})
        return self.chunk_documents([doc])
    
    def get_optimal_chunk_size(self, documents: List[Document]) -> int:
        if not documents:
            return self.chunk_size
        
        total_length = sum(len(doc.page_content) for doc in documents)
        avg_length = total_length // len(documents)
        
        if avg_length < 500:
            return 500
        elif avg_length < 1000:
            return 800
        elif avg_length < 2000:
            return 1200
        else:
            return 1500
    
    def adaptive_chunk(self, documents: List[Document]) -> List[Document]:
        optimal_size = self.get_optimal_chunk_size(documents)
        
        logger.info(f"Using adaptive chunk size: {optimal_size}")
        
        adaptive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=optimal_size,
            chunk_overlap=optimal_size // 5,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        chunks = adaptive_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = i
            chunk.metadata['chunk_size'] = len(chunk.page_content)
            chunk.metadata['chunking_strategy'] = 'adaptive'
        
        logger.info(f"Adaptive chunking created {len(chunks)} chunks")
        return chunks
