import requests
import json


BASE_URL = "http://localhost:8000"


def test_health():
    print("\n" + "="*80)
    print("Testing Health Endpoint")
    print("="*80)
    
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")


def test_basic_query():
    print("\n" + "="*80)
    print("Testing Basic Query")
    print("="*80)
    
    payload = {
        "query": "What are the benefits of machine learning?",
        "use_rag": False,
        "use_sql": False,
        "use_api": True,
        "enable_self_correction": True,
        "max_iterations": 2
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nMetadata:")
        print(json.dumps(result['metadata'], indent=2))
    else:
        print(f"Error: {response.text}")


def test_document_ingestion():
    print("\n" + "="*80)
    print("Testing Document Ingestion")
    print("="*80)
    
    payload = {
        "text": "Artificial Intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of intelligent agents: any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals.",
        "metadata": {
            "source": "test_document",
            "topic": "AI"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/ingest", json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response:\n{json.dumps(response.json(), indent=2)}")


def test_rag_query():
    print("\n" + "="*80)
    print("Testing RAG Query")
    print("="*80)
    
    payload = {
        "query": "What is artificial intelligence?",
        "use_rag": True,
        "use_sql": False,
        "use_api": False,
        "enable_self_correction": True,
        "max_iterations": 3
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nMetadata:")
        print(json.dumps(result['metadata'], indent=2))
    else:
        print(f"Error: {response.text}")


def test_conversation_memory():
    print("\n" + "="*80)
    print("Testing Conversation Memory")
    print("="*80)
    
    session_id = "test_session_123"
    
    queries = [
        "What is Python?",
        "What are its main features?",
        "How is it used in data science?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- Query {i} ---")
        payload = {
            "query": query,
            "use_rag": False,
            "use_sql": False,
            "use_api": True,
            "enable_self_correction": False,
            "session_id": session_id
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/query", json=payload)
        if response.status_code == 200:
            result = response.json()
            print(f"Q: {query}")
            print(f"A: {result['answer'][:200]}...")
    
    print("\n--- Retrieving Conversation History ---")
    response = requests.get(f"{BASE_URL}/api/v1/memory/{session_id}")
    if response.status_code == 200:
        memory = response.json()
        print(f"Total messages: {len(memory['conversation_history'])}")
    
    print("\n--- Clearing Memory ---")
    response = requests.delete(f"{BASE_URL}/api/v1/memory/{session_id}")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")


def main():
    print("\n" + "="*80)
    print("Agentic AI Ecosystem - API Client Examples")
    print("="*80)
    
    try:
        test_health()
        
        test_basic_query()
        
        test_document_ingestion()
        
        test_rag_query()
        
        test_conversation_memory()
        
        print("\n" + "="*80)
        print("All tests completed!")
        print("="*80 + "\n")
        
    except requests.exceptions.ConnectionError:
        print("\nError: Could not connect to the API server.")
        print("Please ensure the server is running at http://localhost:8000")
        print("Start the server with: uvicorn src.api.main:app --reload")
    except Exception as e:
        print(f"\nError: {str(e)}")


if __name__ == "__main__":
    main()
