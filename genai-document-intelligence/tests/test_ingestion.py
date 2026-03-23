import pytest
from fastapi.testclient import TestClient
from app.main import app
import os

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "version" in data


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not configured"
)
def test_document_ingestion():
    test_file_content = b"This is a test document for ingestion testing."
    
    files = {
        "file": ("test_document.txt", test_file_content, "text/plain")
    }
    
    response = client.post("/api/v1/ingest", files=files)
    
    assert response.status_code == 200
    data = response.json()
    
    assert "document_id" in data
    assert "total_chunks" in data
    assert data["status"] == "success"
    assert data["total_chunks"] > 0


def test_invalid_file_type():
    test_file_content = b"Invalid file content"
    
    files = {
        "file": ("test_document.xyz", test_file_content, "application/octet-stream")
    }
    
    response = client.post("/api/v1/ingest", files=files)
    
    assert response.status_code == 400


@pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY") or not os.getenv("PINECONE_API_KEY"),
    reason="API keys not configured"
)
def test_get_stats():
    response = client.get("/api/v1/stats")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "vector_store" in data
    assert "bm25_index" in data
