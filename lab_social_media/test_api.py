# -*- coding: utf-8 -*-
"""
Test API Endpoints
Quick test script to verify API is working correctly
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_endpoint(name, url):
    """Test an API endpoint"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📄 Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            if len(json.dumps(data)) > 500:
                print("... (truncated)")
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error - Is the API server running?")
        print("   Start it with: cd api && python app.py")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all tests"""
    print("="*60)
    print("🧪 API ENDPOINT TESTS")
    print("="*60)
    print("\n⚠️  Make sure the API server is running!")
    print("   Start it with: cd api && python app.py\n")
    
    input("Press Enter to start tests...")
    
    # Test all endpoints
    test_endpoint("Root", f"{BASE_URL}/")
    test_endpoint("Stats", f"{BASE_URL}/api/stats")
    test_endpoint("Networks", f"{BASE_URL}/api/networks")
    test_endpoint("Posts (All)", f"{BASE_URL}/api/posts?limit=5")
    test_endpoint("Posts (X/Twitter)", f"{BASE_URL}/api/posts?network=x&limit=3")
    test_endpoint("Posts (Positive)", f"{BASE_URL}/api/posts?sentiment=positive&limit=3")
    test_endpoint("Sentiments", f"{BASE_URL}/api/sentiments")
    test_endpoint("Analytics", f"{BASE_URL}/api/analytics")
    test_endpoint("Queries", f"{BASE_URL}/api/queries")
    
    print("\n" + "="*60)
    print("✅ TESTS COMPLETED")
    print("="*60)


if __name__ == "__main__":
    main()
