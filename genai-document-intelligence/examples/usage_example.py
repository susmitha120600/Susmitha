import requests
import json
from pathlib import Path


BASE_URL = "http://localhost:8000"


def check_health():
    print("=== Checking API Health ===")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def ingest_document(file_path: str):
    print(f"=== Ingesting Document: {file_path} ===")
    
    with open(file_path, 'rb') as f:
        files = {'file': (Path(file_path).name, f)}
        response = requests.post(f"{BASE_URL}/api/v1/ingest", files=files)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Document ID: {data['document_id']}")
        print(f"Total Chunks: {data['total_chunks']}")
        print(f"Processing Time: {data['processing_time']:.2f}s")
        return data['document_id']
    else:
        print(f"Error: {response.text}")
        return None
    print()


def query_documents(query: str, top_k: int = 5, use_reranking: bool = True):
    print(f"=== Querying: {query} ===")
    
    payload = {
        "query": query,
        "top_k": top_k,
        "use_reranking": use_reranking
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"\nAnswer:\n{data['answer']}\n")
        print(f"Confidence Score: {data['confidence_score']:.2f}")
        print(f"Retrieved Chunks: {data['total_chunks_retrieved']}")
        print(f"Processing Time: {data['processing_time']:.2f}s")
        
        print("\nTop Retrieved Chunks:")
        for chunk in data['retrieved_chunks'][:3]:
            print(f"\n  Rank {chunk['rank']} (Score: {chunk['score']:.4f}):")
            print(f"  {chunk['text'][:200]}...")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None
    print()


def search_documents(query: str, top_k: int = 5):
    print(f"=== Searching: {query} ===")
    
    payload = {
        "query": query,
        "top_k": top_k
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/search", json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        
        print(f"\nDense Results: {len(data['dense_results'])}")
        for idx, result in enumerate(data['dense_results'][:3], 1):
            print(f"  {idx}. Score: {result['score']:.4f} - {result['text'][:100]}...")
        
        print(f"\nSparse Results: {len(data['sparse_results'])}")
        for idx, result in enumerate(data['sparse_results'][:3], 1):
            print(f"  {idx}. Score: {result['score']:.4f} - {result['text'][:100]}...")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None
    print()


def evaluate_system(questions: list, ground_truths: list = None):
    print(f"=== Evaluating System with {len(questions)} Questions ===")
    
    payload = {
        "questions": questions,
        "ground_truths": ground_truths
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/evaluate", json=payload)
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        
        print("\nAverage Scores:")
        for metric, score in data['average_scores'].items():
            print(f"  {metric}: {score:.4f}")
        
        print(f"\nEvaluation Time: {data['evaluation_time']:.2f}s")
        
        return data
    else:
        print(f"Error: {response.text}")
        return None
    print()


def get_stats():
    print("=== Getting System Stats ===")
    response = requests.get(f"{BASE_URL}/api/v1/stats")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
        return data
    else:
        print(f"Error: {response.text}")
        return None
    print()


def delete_document(document_id: str):
    print(f"=== Deleting Document: {document_id} ===")
    response = requests.delete(f"{BASE_URL}/api/v1/document/{document_id}")
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print(response.json())
    else:
        print(f"Error: {response.text}")
    print()


def main():
    print("=" * 60)
    print("GenAI Document Intelligence Platform - Usage Example")
    print("=" * 60)
    print()
    
    check_health()
    
    print("\n" + "=" * 60 + "\n")
    
    get_stats()
    
    print("\n" + "=" * 60 + "\n")
    
    query_documents(
        query="What are the key features of the system?",
        top_k=5,
        use_reranking=True
    )
    
    print("\n" + "=" * 60 + "\n")
    
    search_documents(
        query="machine learning artificial intelligence",
        top_k=5
    )
    
    print("\n" + "=" * 60 + "\n")
    
    questions = [
        "What is RAG?",
        "How does hybrid search work?",
        "What are the benefits of cross-encoder reranking?"
    ]
    
    ground_truths = [
        "RAG stands for Retrieval-Augmented Generation.",
        "Hybrid search combines dense and sparse retrieval methods.",
        "Cross-encoder reranking improves retrieval precision."
    ]
    
    evaluate_system(questions, ground_truths)
    
    print("\n" + "=" * 60)
    print("Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
