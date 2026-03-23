from typing import List, Dict, Optional, Tuple
import numpy as np
from pathlib import Path
import pickle
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from src.core.config import settings
from src.core.logging import get_logger
from src.core.exceptions import RAGError
from .embeddings import EmbeddingGenerator

logger = get_logger(__name__)


class HybridRetriever:
    
    def __init__(
        self,
        embedding_generator: Optional[EmbeddingGenerator] = None,
        index_path: Optional[str] = None
    ):
        self.embedding_generator = embedding_generator or EmbeddingGenerator()
        self.index_path = index_path or settings.FAISS_INDEX_PATH
        self.vectorstore: Optional[FAISS] = None
        self.bm25_index: Optional[Dict] = None
        self.documents: List[Document] = []
        
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
    
    def build_index(self, documents: List[Document]):
        if not documents:
            raise RAGError("No documents provided for indexing")
        
        try:
            self.documents = documents
            
            embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            self.vectorstore = FAISS.from_documents(documents, embeddings)
            
            self._build_bm25_index(documents)
            
            logger.info(f"Built index with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"Error building index: {str(e)}")
            raise RAGError("Failed to build index", details={"error": str(e)})
    
    def _build_bm25_index(self, documents: List[Document]):
        from collections import Counter
        import math
        
        self.bm25_index = {
            'documents': documents,
            'doc_freqs': {},
            'idf': {},
            'doc_len': [],
            'avgdl': 0
        }
        
        all_tokens = []
        for doc in documents:
            tokens = doc.page_content.lower().split()
            all_tokens.append(tokens)
            self.bm25_index['doc_len'].append(len(tokens))
            
            for token in set(tokens):
                self.bm25_index['doc_freqs'][token] = self.bm25_index['doc_freqs'].get(token, 0) + 1
        
        self.bm25_index['avgdl'] = sum(self.bm25_index['doc_len']) / len(documents)
        
        num_docs = len(documents)
        for token, freq in self.bm25_index['doc_freqs'].items():
            self.bm25_index['idf'][token] = math.log((num_docs - freq + 0.5) / (freq + 0.5) + 1)
        
        self.bm25_index['all_tokens'] = all_tokens
        
        logger.info("Built BM25 index")
    
    def _bm25_score(self, query: str, k1: float = 1.5, b: float = 0.75) -> List[float]:
        if not self.bm25_index:
            return [0.0] * len(self.documents)
        
        query_tokens = query.lower().split()
        scores = []
        
        for i, doc_tokens in enumerate(self.bm25_index['all_tokens']):
            score = 0.0
            doc_len = self.bm25_index['doc_len'][i]
            
            token_freqs = Counter(doc_tokens)
            
            for token in query_tokens:
                if token in self.bm25_index['idf']:
                    idf = self.bm25_index['idf'][token]
                    tf = token_freqs.get(token, 0)
                    
                    numerator = tf * (k1 + 1)
                    denominator = tf + k1 * (1 - b + b * (doc_len / self.bm25_index['avgdl']))
                    
                    score += idf * (numerator / denominator)
            
            scores.append(score)
        
        return scores
    
    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_hybrid: Optional[bool] = None,
        alpha: float = 0.5
    ) -> List[Tuple[Document, float]]:
        top_k = top_k or settings.TOP_K_RETRIEVAL
        use_hybrid = use_hybrid if use_hybrid is not None else settings.ENABLE_HYBRID_SEARCH
        
        if not self.vectorstore:
            raise RAGError("Index not built. Call build_index() first.")
        
        try:
            if use_hybrid and self.bm25_index:
                return self._hybrid_retrieve(query, top_k, alpha)
            else:
                return self._dense_retrieve(query, top_k)
                
        except Exception as e:
            logger.error(f"Error during retrieval: {str(e)}")
            raise RAGError("Failed to retrieve documents", details={"error": str(e)})
    
    def _dense_retrieve(self, query: str, top_k: int) -> List[Tuple[Document, float]]:
        results = self.vectorstore.similarity_search_with_score(query, k=top_k)
        
        results_with_similarity = [
            (doc, 1.0 / (1.0 + score)) for doc, score in results
        ]
        
        logger.info(f"Dense retrieval returned {len(results_with_similarity)} documents")
        return results_with_similarity
    
    def _hybrid_retrieve(
        self,
        query: str,
        top_k: int,
        alpha: float
    ) -> List[Tuple[Document, float]]:
        dense_results = self.vectorstore.similarity_search_with_score(query, k=len(self.documents))
        
        dense_scores = {}
        for doc, score in dense_results:
            doc_id = id(doc)
            dense_scores[doc_id] = 1.0 / (1.0 + score)
        
        bm25_scores_list = self._bm25_score(query)
        
        max_bm25 = max(bm25_scores_list) if bm25_scores_list else 1.0
        if max_bm25 > 0:
            bm25_scores_list = [s / max_bm25 for s in bm25_scores_list]
        
        hybrid_scores = []
        for i, doc in enumerate(self.documents):
            doc_id = id(doc)
            dense_score = dense_scores.get(doc_id, 0.0)
            bm25_score = bm25_scores_list[i]
            
            hybrid_score = alpha * dense_score + (1 - alpha) * bm25_score
            hybrid_scores.append((doc, hybrid_score))
        
        hybrid_scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"Hybrid retrieval returned {top_k} documents (alpha={alpha})")
        return hybrid_scores[:top_k]
    
    def save_index(self, path: Optional[str] = None):
        save_path = path or self.index_path
        
        if not self.vectorstore:
            raise RAGError("No index to save")
        
        try:
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            self.vectorstore.save_local(save_path)
            
            bm25_path = Path(save_path) / "bm25_index.pkl"
            with open(bm25_path, 'wb') as f:
                pickle.dump(self.bm25_index, f)
            
            logger.info(f"Saved index to {save_path}")
            
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise RAGError("Failed to save index", details={"error": str(e)})
    
    def load_index(self, path: Optional[str] = None):
        load_path = path or self.index_path
        
        if not Path(load_path).exists():
            raise RAGError(f"Index not found at {load_path}")
        
        try:
            embeddings = OpenAIEmbeddings(
                model=settings.EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            self.vectorstore = FAISS.load_local(
                load_path,
                embeddings,
                allow_dangerous_deserialization=True
            )
            
            bm25_path = Path(load_path) / "bm25_index.pkl"
            if bm25_path.exists():
                with open(bm25_path, 'rb') as f:
                    self.bm25_index = pickle.load(f)
                self.documents = self.bm25_index['documents']
            
            logger.info(f"Loaded index from {load_path}")
            
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            raise RAGError("Failed to load index", details={"error": str(e)})
