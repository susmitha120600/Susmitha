import re
import tiktoken
from typing import List, Optional
from app.core.logging import get_logger

logger = get_logger(__name__)


def clean_text(text: str) -> str:
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\n+', '\n', text)
    text = text.strip()
    return text


def count_tokens(text: str, model: str = "gpt-4") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}, using character approximation")
        return len(text) // 4


def truncate_text(text: str, max_tokens: int, model: str = "gpt-4") -> str:
    try:
        encoding = tiktoken.encoding_for_model(model)
        tokens = encoding.encode(text)
        
        if len(tokens) <= max_tokens:
            return text
        
        truncated_tokens = tokens[:max_tokens]
        return encoding.decode(truncated_tokens)
    except Exception as e:
        logger.error(f"Error truncating text: {e}")
        return text


def split_into_sentences(text: str) -> List[str]:
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    sentences = sentence_endings.split(text)
    return [s.strip() for s in sentences if s.strip()]


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    
    words = text.split()
    
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
        'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
        'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they'
    }
    
    words = [w for w in words if w not in stop_words and len(w) > 2]
    
    word_freq = {}
    for word in words:
        word_freq[word] = word_freq.get(word, 0) + 1
    
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    return [word for word, freq in sorted_words[:top_n]]


def calculate_text_similarity(text1: str, text2: str) -> float:
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if len(union) == 0:
        return 0.0
    
    return len(intersection) / len(union)


def merge_overlapping_chunks(chunks: List[str], overlap_threshold: float = 0.3) -> List[str]:
    if not chunks:
        return []
    
    merged = [chunks[0]]
    
    for i in range(1, len(chunks)):
        current_chunk = chunks[i]
        previous_chunk = merged[-1]
        
        similarity = calculate_text_similarity(current_chunk, previous_chunk)
        
        if similarity > overlap_threshold:
            merged[-1] = previous_chunk + " " + current_chunk
        else:
            merged.append(current_chunk)
    
    return merged


def optimize_context_window(
    chunks: List[str],
    max_tokens: int,
    model: str = "gpt-4"
) -> List[str]:
    optimized_chunks = []
    current_tokens = 0
    
    for chunk in chunks:
        chunk_tokens = count_tokens(chunk, model)
        
        if current_tokens + chunk_tokens <= max_tokens:
            optimized_chunks.append(chunk)
            current_tokens += chunk_tokens
        else:
            remaining_tokens = max_tokens - current_tokens
            if remaining_tokens > 50:
                truncated_chunk = truncate_text(chunk, remaining_tokens, model)
                optimized_chunks.append(truncated_chunk)
            break
    
    return optimized_chunks
