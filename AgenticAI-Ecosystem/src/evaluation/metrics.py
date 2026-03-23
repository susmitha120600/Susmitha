from typing import Dict, List, Optional, Any
import numpy as np
from src.core.logging import get_logger

logger = get_logger(__name__)


def evaluate_response(
    query: str,
    answer: str,
    ground_truth: Optional[str] = None,
    contexts: Optional[List[str]] = None
) -> Dict[str, float]:
    metrics = {}
    
    metrics['answer_length'] = len(answer)
    metrics['answer_word_count'] = len(answer.split())
    
    if ground_truth:
        metrics['exact_match'] = 1.0 if answer.strip().lower() == ground_truth.strip().lower() else 0.0
        
        metrics['token_overlap'] = calculate_token_overlap(answer, ground_truth)
    
    if contexts:
        metrics['context_relevance'] = calculate_context_relevance(answer, contexts)
        metrics['context_utilization'] = calculate_context_utilization(answer, contexts)
    
    metrics['confidence_score'] = estimate_confidence(answer)
    
    logger.info(f"Evaluation metrics calculated: {metrics}")
    return metrics


def calculate_ragas_metrics(
    query: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None
) -> Dict[str, float]:
    try:
        from ragas import evaluate
        from ragas.metrics import (
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall
        )
        from datasets import Dataset
        
        data = {
            'question': [query],
            'answer': [answer],
            'contexts': [contexts],
        }
        
        if ground_truth:
            data['ground_truth'] = [ground_truth]
        
        dataset = Dataset.from_dict(data)
        
        metrics_to_use = [faithfulness, answer_relevancy, context_precision]
        if ground_truth:
            metrics_to_use.append(context_recall)
        
        result = evaluate(dataset, metrics=metrics_to_use)
        
        logger.info(f"RAGAS metrics calculated: {result}")
        return dict(result)
        
    except ImportError:
        logger.warning("RAGAS not available, using fallback metrics")
        return {
            'faithfulness': calculate_faithfulness_simple(answer, contexts),
            'answer_relevancy': calculate_relevancy_simple(query, answer),
            'context_precision': calculate_context_relevance(answer, contexts)
        }
    except Exception as e:
        logger.error(f"Error calculating RAGAS metrics: {str(e)}")
        return {}


def calculate_token_overlap(text1: str, text2: str) -> float:
    tokens1 = set(text1.lower().split())
    tokens2 = set(text2.lower().split())
    
    if not tokens1 or not tokens2:
        return 0.0
    
    intersection = tokens1.intersection(tokens2)
    union = tokens1.union(tokens2)
    
    return len(intersection) / len(union) if union else 0.0


def calculate_context_relevance(answer: str, contexts: List[str]) -> float:
    if not contexts:
        return 0.0
    
    answer_tokens = set(answer.lower().split())
    
    relevance_scores = []
    for context in contexts:
        context_tokens = set(context.lower().split())
        if context_tokens:
            overlap = len(answer_tokens.intersection(context_tokens))
            relevance = overlap / len(context_tokens)
            relevance_scores.append(relevance)
    
    return np.mean(relevance_scores) if relevance_scores else 0.0


def calculate_context_utilization(answer: str, contexts: List[str]) -> float:
    if not contexts:
        return 0.0
    
    answer_tokens = set(answer.lower().split())
    all_context_tokens = set()
    
    for context in contexts:
        all_context_tokens.update(context.lower().split())
    
    if not answer_tokens:
        return 0.0
    
    overlap = len(answer_tokens.intersection(all_context_tokens))
    return overlap / len(answer_tokens)


def calculate_faithfulness_simple(answer: str, contexts: List[str]) -> float:
    if not contexts:
        return 0.5
    
    answer_sentences = answer.split('.')
    answer_sentences = [s.strip() for s in answer_sentences if s.strip()]
    
    if not answer_sentences:
        return 0.0
    
    supported_count = 0
    for sentence in answer_sentences:
        sentence_tokens = set(sentence.lower().split())
        
        for context in contexts:
            context_tokens = set(context.lower().split())
            overlap = len(sentence_tokens.intersection(context_tokens))
            
            if overlap / len(sentence_tokens) > 0.5:
                supported_count += 1
                break
    
    return supported_count / len(answer_sentences)


def calculate_relevancy_simple(query: str, answer: str) -> float:
    query_tokens = set(query.lower().split())
    answer_tokens = set(answer.lower().split())
    
    if not query_tokens or not answer_tokens:
        return 0.0
    
    overlap = len(query_tokens.intersection(answer_tokens))
    return overlap / len(query_tokens)


def estimate_confidence(answer: str) -> float:
    confidence_indicators = {
        'high': ['definitely', 'certainly', 'clearly', 'obviously', 'undoubtedly'],
        'medium': ['likely', 'probably', 'generally', 'typically', 'usually'],
        'low': ['possibly', 'maybe', 'might', 'could', 'perhaps', 'uncertain']
    }
    
    answer_lower = answer.lower()
    
    high_count = sum(1 for word in confidence_indicators['high'] if word in answer_lower)
    medium_count = sum(1 for word in confidence_indicators['medium'] if word in answer_lower)
    low_count = sum(1 for word in confidence_indicators['low'] if word in answer_lower)
    
    if high_count > low_count:
        return 0.9
    elif low_count > high_count:
        return 0.5
    else:
        return 0.7


def calculate_hallucination_rate(
    answer: str,
    contexts: List[str],
    threshold: float = 0.3
) -> float:
    if not contexts:
        return 0.5
    
    answer_sentences = [s.strip() for s in answer.split('.') if s.strip()]
    
    if not answer_sentences:
        return 0.0
    
    hallucinated_count = 0
    
    for sentence in answer_sentences:
        sentence_tokens = set(sentence.lower().split())
        max_support = 0.0
        
        for context in contexts:
            context_tokens = set(context.lower().split())
            if sentence_tokens:
                overlap = len(sentence_tokens.intersection(context_tokens))
                support = overlap / len(sentence_tokens)
                max_support = max(max_support, support)
        
        if max_support < threshold:
            hallucinated_count += 1
    
    return hallucinated_count / len(answer_sentences)
