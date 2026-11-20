"""
Test and verify backend endpoints and frontend server.
"""
import sys
import json
import httpx

def test_endpoints():
    client = httpx.Client(timeout=30.0)
    
    print("=== 1. Testing GET http://127.0.0.1:8000/health ===")
    try:
        r = client.get("http://127.0.0.1:8000/health")
        print(f"Status: {r.status_code}")
        print(f"Body: {json.dumps(r.json(), indent=2)}")
    except Exception as e:
        print(f"Health check failed: {e}")

    print("\n=== 2. Testing GET http://127.0.0.1:8000/documents ===")
    try:
        r = client.get("http://127.0.0.1:8000/documents")
        print(f"Status: {r.status_code}")
        docs = r.json()
        print(f"Document count: {len(docs)}")
        for d in docs:
            print(f"  - {d.get('title')} ({d.get('filename')}), source={d.get('source_type')}, pages={d.get('page_count')}")
    except Exception as e:
        print(f"Documents check failed: {e}")

    print("\n=== 3. Testing GET http://127.0.0.1:8000/api/docs ===")
    try:
        r = client.get("http://127.0.0.1:8000/api/docs")
        print(f"Status: {r.status_code}")
        print(f"Content type: {r.headers.get('content-type')}")
    except Exception as e:
        print(f"Docs check failed: {e}")

    print("\n=== 4. Testing GET http://127.0.0.1:5500/ ===")
    try:
        r = client.get("http://127.0.0.1:5500/")
        print(f"Status: {r.status_code}")
        print(f"HTML Title check: {'IndicRAG-QA' in r.text}")
    except Exception as e:
        print(f"Frontend server check failed: {e}")

if __name__ == "__main__":
    test_endpoints()

