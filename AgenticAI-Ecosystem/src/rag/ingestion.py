import os
from pathlib import Path
from typing import List, Dict, Optional
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
    CSVLoader,
    JSONLoader
)
from langchain.schema import Document
from src.core.logging import get_logger
from src.core.exceptions import RAGError

logger = get_logger(__name__)


class DocumentIngestion:
    
    SUPPORTED_EXTENSIONS = {
        '.pdf': PyPDFLoader,
        '.txt': TextLoader,
        '.md': UnstructuredMarkdownLoader,
        '.csv': CSVLoader,
        '.json': JSONLoader,
    }
    
    def __init__(self):
        self.documents: List[Document] = []
    
    def load_file(self, file_path: str) -> List[Document]:
        path = Path(file_path)
        
        if not path.exists():
            raise RAGError(f"File not found: {file_path}")
        
        extension = path.suffix.lower()
        
        if extension not in self.SUPPORTED_EXTENSIONS:
            raise RAGError(
                f"Unsupported file type: {extension}",
                details={"supported": list(self.SUPPORTED_EXTENSIONS.keys())}
            )
        
        try:
            loader_class = self.SUPPORTED_EXTENSIONS[extension]
            
            if extension == '.json':
                loader = loader_class(file_path, jq_schema='.', text_content=False)
            else:
                loader = loader_class(file_path)
            
            documents = loader.load()
            
            for doc in documents:
                doc.metadata['source'] = str(path)
                doc.metadata['file_type'] = extension
            
            logger.info(f"Loaded {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise RAGError(f"Failed to load file: {file_path}", details={"error": str(e)})
    
    def load_directory(self, directory_path: str, recursive: bool = True) -> List[Document]:
        path = Path(directory_path)
        
        if not path.exists() or not path.is_dir():
            raise RAGError(f"Directory not found: {directory_path}")
        
        all_documents = []
        
        if recursive:
            files = path.rglob('*')
        else:
            files = path.glob('*')
        
        for file_path in files:
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                try:
                    docs = self.load_file(str(file_path))
                    all_documents.extend(docs)
                except Exception as e:
                    logger.warning(f"Skipping file {file_path}: {str(e)}")
                    continue
        
        logger.info(f"Loaded {len(all_documents)} documents from directory {directory_path}")
        self.documents.extend(all_documents)
        return all_documents
    
    def load_from_text(self, text: str, metadata: Optional[Dict] = None) -> Document:
        doc = Document(
            page_content=text,
            metadata=metadata or {"source": "direct_input"}
        )
        self.documents.append(doc)
        return doc
    
    def get_documents(self) -> List[Document]:
        return self.documents
    
    def clear_documents(self):
        self.documents = []
        logger.info("Cleared all loaded documents")
    
    def get_statistics(self) -> Dict:
        if not self.documents:
            return {
                "total_documents": 0,
                "total_characters": 0,
                "file_types": {}
            }
        
        file_types = {}
        total_chars = 0
        
        for doc in self.documents:
            total_chars += len(doc.page_content)
            file_type = doc.metadata.get('file_type', 'unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
        
        return {
            "total_documents": len(self.documents),
            "total_characters": total_chars,
            "average_length": total_chars // len(self.documents) if self.documents else 0,
            "file_types": file_types
        }
