from typing import List, Dict, Any, Optional
from langchain.tools import Tool
from langchain.schema import Document
from src.rag import HybridRetriever, CrossEncoderReranker
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class RAGTools:
    
    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        reranker: Optional[CrossEncoderReranker] = None
    ):
        self.retriever = retriever
        self.reranker = reranker
    
    def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        use_reranking: bool = True
    ) -> List[Dict[str, Any]]:
        if not self.retriever:
            logger.warning("No retriever configured")
            return []
        
        try:
            top_k = top_k or settings.TOP_K_RETRIEVAL
            
            results = self.retriever.retrieve(query, top_k=top_k * 2 if use_reranking else top_k)
            
            if use_reranking and self.reranker and len(results) > 0:
                results = self.reranker.rerank(query, results, top_k=top_k)
            else:
                results = results[:top_k]
            
            formatted_results = [
                {
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': score
                }
                for doc, score in results
            ]
            
            logger.info(f"Retrieved {len(formatted_results)} documents for query")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            return []
    
    def format_context_for_prompt(self, contexts: List[Dict[str, Any]]) -> str:
        if not contexts:
            return "No relevant context found."
        
        formatted = []
        for i, ctx in enumerate(contexts, 1):
            source = ctx['metadata'].get('source', 'Unknown')
            content = ctx['content']
            score = ctx.get('score', 0.0)
            
            formatted.append(
                f"[Context {i}] (Relevance: {score:.2f}, Source: {source})\n{content}\n"
            )
        
        return "\n".join(formatted)
    
    def get_langchain_tools(self) -> List[Tool]:
        def retrieve_documents(query: str) -> str:
            contexts = self.retrieve_context(query)
            return self.format_context_for_prompt(contexts)
        
        def retrieve_with_metadata(query: str) -> str:
            contexts = self.retrieve_context(query)
            import json
            return json.dumps(contexts, indent=2)
        
        return [
            Tool(
                name="retrieve_context",
                func=retrieve_documents,
                description="Retrieve relevant context from the knowledge base. "
                           "Input should be a search query or question. "
                           "Returns formatted context with sources and relevance scores."
            ),
            Tool(
                name="retrieve_context_with_metadata",
                func=retrieve_with_metadata,
                description="Retrieve relevant context with full metadata from the knowledge base. "
                           "Input should be a search query. "
                           "Returns JSON with content, metadata, and scores."
            )
        ]
