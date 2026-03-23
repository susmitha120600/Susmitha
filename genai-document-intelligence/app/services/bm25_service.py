from typing import List, Dict, Any, Optional
import pickle
import os
from rank_bm25 import BM25Okapi
from app.core.logging import get_logger
from app.core.exceptions import RetrievalError
from app.models.schemas import SearchResult

logger = get_logger(__name__)


class BM25Service:
    
    def __init__(self, index_path: str = "data/bm25_index.pkl"):
        self.index_path = index_path
        self.bm25_index: Optional[BM25Okapi] = None
        self.corpus: List[Dict[str, Any]] = []
        self.tokenized_corpus: List[List[str]] = []
        
        self._load_index()
        logger.info("BM25Service initialized")
    
    def _tokenize(self, text: str) -> List[str]:
        text = text.lower()
        tokens = text.split()
        return tokens
    
    def _load_index(self):
        try:
            if os.path.exists(self.index_path):
                with open(self.index_path, 'rb') as f:
                    data = pickle.load(f)
                    self.corpus = data.get('corpus', [])
                    self.tokenized_corpus = data.get('tokenized_corpus', [])
                    
                    if self.tokenized_corpus:
                        self.bm25_index = BM25Okapi(self.tokenized_corpus)
                        logger.info(f"Loaded BM25 index with {len(self.corpus)} documents")
            else:
                logger.info("No existing BM25 index found, starting fresh")
        except Exception as e:
            logger.warning(f"Failed to load BM25 index: {str(e)}, starting fresh")
            self.corpus = []
            self.tokenized_corpus = []
            self.bm25_index = None
    
    def _save_index(self):
        try:
            os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
            
            data = {
                'corpus': self.corpus,
                'tokenized_corpus': self.tokenized_corpus
            }
            
            with open(self.index_path, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"Saved BM25 index with {len(self.corpus)} documents")
        except Exception as e:
            logger.error(f"Failed to save BM25 index: {str(e)}")
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        try:
            logger.info(f"Adding {len(documents)} documents to BM25 index")
            
            for doc in documents:
                text = doc.get('text', '')
                if not text:
                    continue
                
                tokenized_text = self._tokenize(text)
                
                self.corpus.append(doc)
                self.tokenized_corpus.append(tokenized_text)
            
            if self.tokenized_corpus:
                self.bm25_index = BM25Okapi(self.tokenized_corpus)
            
            self._save_index()
            
            logger.info(f"BM25 index now contains {len(self.corpus)} documents")
            
        except Exception as e:
            logger.error(f"Error adding documents to BM25: {str(e)}")
            raise RetrievalError(f"Failed to add documents to BM25 index: {str(e)}")
    
    async def search(
        self,
        query: str,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        try:
            if not self.bm25_index or not self.corpus:
                logger.warning("BM25 index is empty, returning no results")
                return []
            
            logger.info(f"Searching BM25 index with query: {query[:50]}...")
            
            tokenized_query = self._tokenize(query)
            
            scores = self.bm25_index.get_scores(tokenized_query)
            
            doc_scores = list(enumerate(scores))
            doc_scores.sort(key=lambda x: x[1], reverse=True)
            
            results = []
            for idx, score in doc_scores[:top_k]:
                if score <= 0:
                    continue
                
                doc = self.corpus[idx]
                
                if filter_dict:
                    if not self._matches_filter(doc, filter_dict):
                        continue
                
                result = SearchResult(
                    chunk_id=doc.get('chunk_id', f'bm25_{idx}'),
                    text=doc.get('text', ''),
                    score=float(score),
                    source=doc.get('source', ''),
                    metadata=doc.get('metadata', {})
                )
                results.append(result)
            
            logger.info(f"BM25 search returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"BM25 search error: {str(e)}")
            raise RetrievalError(f"BM25 search failed: {str(e)}")
    
    def _matches_filter(self, doc: Dict[str, Any], filter_dict: Dict[str, Any]) -> bool:
        for key, value in filter_dict.items():
            if key in doc and doc[key] != value:
                return False
            if key in doc.get('metadata', {}) and doc['metadata'][key] != value:
                return False
        return True
    
    async def delete_by_document_id(self, document_id: str):
        try:
            logger.info(f"Deleting documents with document_id: {document_id}")
            
            new_corpus = []
            new_tokenized_corpus = []
            
            for i, doc in enumerate(self.corpus):
                if doc.get('document_id') != document_id:
                    new_corpus.append(doc)
                    new_tokenized_corpus.append(self.tokenized_corpus[i])
            
            self.corpus = new_corpus
            self.tokenized_corpus = new_tokenized_corpus
            
            if self.tokenized_corpus:
                self.bm25_index = BM25Okapi(self.tokenized_corpus)
            else:
                self.bm25_index = None
            
            self._save_index()
            
            logger.info(f"Deleted documents for document_id: {document_id}")
            
        except Exception as e:
            logger.error(f"Error deleting from BM25: {str(e)}")
            raise RetrievalError(f"Failed to delete from BM25 index: {str(e)}")
    
    async def clear_index(self):
        try:
            logger.warning("Clearing BM25 index")
            
            self.corpus = []
            self.tokenized_corpus = []
            self.bm25_index = None
            
            if os.path.exists(self.index_path):
                os.remove(self.index_path)
            
            logger.info("BM25 index cleared")
            
        except Exception as e:
            logger.error(f"Error clearing BM25 index: {str(e)}")
            raise RetrievalError(f"Failed to clear BM25 index: {str(e)}")
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "total_documents": len(self.corpus),
            "index_exists": self.bm25_index is not None,
            "index_path": self.index_path
        }
