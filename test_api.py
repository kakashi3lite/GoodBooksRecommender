import requests
import json

def test_recommendations():
    """Test the recommendation API endpoint"""
    url = "http://127.0.0.1:8000/recommendations"
    
    # Test with user_id
    payload = {
        "user_id": 1,
        "num_recommendations": 10
    }
    
    try:
        response = requests.post(url, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            recommendations = response.json().get('recommendations', [])
            print(f"\nReceived {len(recommendations)} recommendations")
            for i, rec in enumerate(recommendations[:5], 1):
                print(f"{i}. {rec.get('title', 'Unknown')} by {rec.get('authors', 'Unknown')} (Score: {rec.get('score', 'N/A')})")
        
    except Exception as e:
        print(f"Error: {e}")

def test_health():
    """Test the health endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        print(f"Health Check - Status: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"Health check error: {e}")

def test_root():
    """Test the root endpoint"""
    try:
        response = requests.get("http://127.0.0.1:8000/")
        print(f"Root - Status: {response.status_code}, Response: {response.json()}")
    except Exception as e:
        print(f"Root endpoint error: {e}")

if __name__ == "__main__":
    print("Testing Book Recommendation API...\n")
    
    print("1. Testing root endpoint:")
    test_root()
    
    print("\n2. Testing health endpoint:")
    test_health()
    
    print("\n3. Testing recommendations endpoint:")
    test_recommendations()