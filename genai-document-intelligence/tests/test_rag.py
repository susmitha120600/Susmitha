import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not configured"
)
def test_query_endpoint():
    query_data = {
        "query": "What is machine learning?",
        "top_k": 3,
        "use_reranking": True
    }
    
    response = client.post("/api/v1/query", json=query_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "query" in data
    assert "answer" in data
    assert "retrieved_chunks" in data
    assert "confidence_score" in data


def test_query_validation():
    query_data = {
        "query": "",
        "top_k": 5
    }
    
    response = client.post("/api/v1/query", json=query_data)
    
    assert response.status_code == 422


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not configured"
)
def test_search_endpoint():
    query_data = {
        "query": "artificial intelligence",
        "top_k": 5
    }
    
    response = client.post("/api/v1/search", json=query_data)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "dense_results" in data
    assert "sparse_results" in data


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not configured"
)
def test_evaluation_endpoint():
    eval_data = {
        "questions": ["What is AI?"],
        "ground_truths": ["AI is artificial intelligence."]
    }
    
    response = client.post("/api/v1/evaluate", json=eval_data)
    
    if response.status_code == 200:
        data = response.json()
        assert "metrics" in data
        assert "average_scores" in data


def test_invalid_query_parameters():
    query_data = {
        "query": "test",
        "top_k": 100
    }
    
    response = client.post("/api/v1/query", json=query_data)
    
    assert response.status_code == 422
