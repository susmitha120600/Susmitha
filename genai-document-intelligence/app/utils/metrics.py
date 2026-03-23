import time
from functools import wraps
from typing import Callable, Any
from prometheus_client import Counter, Histogram, Gauge
from app.core.logging import get_logger

logger = get_logger(__name__)

query_counter = Counter(
    'rag_queries_total',
    'Total number of RAG queries processed'
)

ingestion_counter = Counter(
    'documents_ingested_total',
    'Total number of documents ingested'
)

retrieval_latency = Histogram(
    'retrieval_latency_seconds',
    'Time spent on retrieval operations',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

reranking_latency = Histogram(
    'reranking_latency_seconds',
    'Time spent on reranking operations',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

llm_latency = Histogram(
    'llm_generation_latency_seconds',
    'Time spent on LLM generation',
    buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 20.0]
)

active_requests = Gauge(
    'active_requests',
    'Number of active requests being processed'
)

retrieval_precision = Gauge(
    'retrieval_precision',
    'Current retrieval precision score'
)


def track_time(metric: Histogram):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.observe(duration)
        
        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                metric.observe(duration)
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def calculate_precision_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    if not retrieved_ids or not relevant_ids:
        return 0.0
    
    retrieved_at_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    
    true_positives = len(retrieved_at_k.intersection(relevant_set))
    return true_positives / k if k > 0 else 0.0


def calculate_recall_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    if not retrieved_ids or not relevant_ids:
        return 0.0
    
    retrieved_at_k = set(retrieved_ids[:k])
    relevant_set = set(relevant_ids)
    
    true_positives = len(retrieved_at_k.intersection(relevant_set))
    return true_positives / len(relevant_set) if len(relevant_set) > 0 else 0.0


def calculate_mrr(retrieved_ids: list, relevant_ids: list) -> float:
    relevant_set = set(relevant_ids)
    
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_set:
            return 1.0 / rank
    
    return 0.0


def calculate_ndcg_at_k(retrieved_ids: list, relevance_scores: dict, k: int) -> float:
    import math
    
    if not retrieved_ids or not relevance_scores:
        return 0.0
    
    def dcg(scores: list) -> float:
        return sum(
            (2 ** score - 1) / math.log2(idx + 2)
            for idx, score in enumerate(scores)
        )
    
    retrieved_at_k = retrieved_ids[:k]
    actual_scores = [relevance_scores.get(doc_id, 0) for doc_id in retrieved_at_k]
    
    ideal_scores = sorted(relevance_scores.values(), reverse=True)[:k]
    
    actual_dcg = dcg(actual_scores)
    ideal_dcg = dcg(ideal_scores)
    
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0
