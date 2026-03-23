import pytest
from pathlib import Path
from src.rag import DocumentIngestion, TextChunker, EmbeddingGenerator
from langchain.schema import Document


class TestDocumentIngestion:
    
    @pytest.fixture
    def ingestion(self):
        return DocumentIngestion()
    
    def test_initialization(self, ingestion):
        assert ingestion.documents == []
        assert len(ingestion.SUPPORTED_EXTENSIONS) > 0
    
    def test_load_from_text(self, ingestion):
        text = "This is a test document"
        doc = ingestion.load_from_text(text, {"source": "test"})
        
        assert isinstance(doc, Document)
        assert doc.page_content == text
        assert doc.metadata["source"] == "test"
    
    def test_get_statistics_empty(self, ingestion):
        stats = ingestion.get_statistics()
        assert stats["total_documents"] == 0
        assert stats["total_characters"] == 0
    
    def test_get_statistics_with_docs(self, ingestion):
        ingestion.load_from_text("Test 1")
        ingestion.load_from_text("Test 2")
        
        stats = ingestion.get_statistics()
        assert stats["total_documents"] == 2
        assert stats["total_characters"] > 0


class TestTextChunker:
    
    @pytest.fixture
    def chunker(self):
        return TextChunker(chunk_size=100, chunk_overlap=20)
    
    def test_initialization(self, chunker):
        assert chunker.chunk_size == 100
        assert chunker.chunk_overlap == 20
    
    def test_chunk_text(self, chunker):
        text = "This is a test. " * 50
        chunks = chunker.chunk_text(text)
        
        assert len(chunks) > 0
        assert all(isinstance(chunk, Document) for chunk in chunks)
    
    def test_chunk_documents(self, chunker):
        docs = [
            Document(page_content="Test content " * 20, metadata={"source": "test1"}),
            Document(page_content="More content " * 20, metadata={"source": "test2"})
        ]
        
        chunks = chunker.chunk_documents(docs)
        
        assert len(chunks) > 0
        assert all('chunk_id' in chunk.metadata for chunk in chunks)


class TestEmbeddingGenerator:
    
    @pytest.fixture
    def mock_embeddings(self):
        with pytest.mock.patch('src.rag.embeddings.OpenAIEmbeddings') as mock:
            mock_instance = mock.return_value
            mock_instance.embed_query.return_value = [0.1] * 1536
            mock_instance.embed_documents.return_value = [[0.1] * 1536, [0.2] * 1536]
            yield mock_instance
    
    def test_cosine_similarity(self):
        from src.rag.embeddings import EmbeddingGenerator
        
        gen = EmbeddingGenerator.__new__(EmbeddingGenerator)
        
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [1.0, 0.0, 0.0]
        similarity = gen.cosine_similarity(vec1, vec2)
        
        assert abs(similarity - 1.0) < 0.001
        
        vec3 = [0.0, 1.0, 0.0]
        similarity2 = gen.cosine_similarity(vec1, vec3)
        
        assert abs(similarity2) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
