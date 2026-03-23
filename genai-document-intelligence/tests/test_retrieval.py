import pytest
from app.services.embedding_service import EmbeddingService
from app.services.bm25_service import BM25Service
from app.utils.text_utils import clean_text, count_tokens
import os


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not configured"
)
@pytest.mark.asyncio
async def test_embedding_generation():
    service = EmbeddingService()
    
    text = "This is a test sentence for embedding generation."
    embedding = await service.generate_embedding(text)
    
    assert embedding is not None
    assert len(embedding) == 1536
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_bm25_search():
    service = BM25Service(index_path="data/test_bm25_index.pkl")
    
    documents = [
        {
            "chunk_id": "chunk_1",
            "text": "Machine learning is a subset of artificial intelligence.",
            "document_id": "doc_1",
            "source": "test.txt",
            "metadata": {}
        },
        {
            "chunk_id": "chunk_2",
            "text": "Deep learning uses neural networks with multiple layers.",
            "document_id": "doc_1",
            "source": "test.txt",
            "metadata": {}
        }
    ]
    
    await service.add_documents(documents)
    
    results = await service.search("machine learning", top_k=2)
    
    assert len(results) > 0
    assert results[0].score > 0
    
    await service.clear_index()


def test_text_cleaning():
    dirty_text = "This   is  a\n\n\ntest   text."
    clean = clean_text(dirty_text)
    
    assert "  " not in clean
    assert "\n\n\n" not in clean


def test_token_counting():
    text = "This is a test sentence."
    token_count = count_tokens(text)
    
    assert token_count > 0
    assert isinstance(token_count, int)


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="OpenAI API key not configured"
)
@pytest.mark.asyncio
async def test_batch_embedding_generation():
    service = EmbeddingService()
    
    texts = [
        "First test sentence.",
        "Second test sentence.",
        "Third test sentence."
    ]
    
    embeddings = await service.generate_embeddings_batch(texts)
    
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 1536 for emb in embeddings)


def test_cosine_similarity():
    service = EmbeddingService()
    
    vec1 = [1.0, 0.0, 0.0]
    vec2 = [1.0, 0.0, 0.0]
    vec3 = [0.0, 1.0, 0.0]
    
    sim_same = service.cosine_similarity(vec1, vec2)
    sim_diff = service.cosine_similarity(vec1, vec3)
    
    assert sim_same > sim_diff
    assert 0.99 <= sim_same <= 1.01
    assert -0.01 <= sim_diff <= 0.01
