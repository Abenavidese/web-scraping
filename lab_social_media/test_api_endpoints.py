"""
Test script for API endpoints with user_id filter
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def test_endpoint(name, url):
    print(f"\n🧪 Testing: {name}")
    print(f"   URL: {url}")
    
    try:
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Status: {response.status_code}")
            print(f"   📊 Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500])
            if len(json.dumps(data)) > 500:
                print("   ... (truncated)")
            return True
        else:
            print(f"   ❌ Status: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection Error: API server not running")
        print(f"   💡 Start server with: cd api && python app.py")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print_section("API ENDPOINT TESTING - User ID Filter")
    
    # Test 1: Stats without filter
    print_section("Test 1: Stats (All Users)")
    test_endpoint("GET /api/stats", f"{BASE_URL}/api/stats")
    
    # Test 2: Stats with user_id filter
    print_section("Test 2: Stats (user_id=default)")
    test_endpoint("GET /api/stats?user_id=default", f"{BASE_URL}/api/stats?user_id=default")
    
    # Test 3: Analytics without filter
    print_section("Test 3: Analytics (All Users)")
    test_endpoint("GET /api/analytics", f"{BASE_URL}/api/analytics")
    
    # Test 4: Analytics with user_id filter
    print_section("Test 4: Analytics (user_id=default)")
    test_endpoint("GET /api/analytics?user_id=default", f"{BASE_URL}/api/analytics?user_id=default")
    
    # Test 5: Queries without filter
    print_section("Test 5: Queries (All Users)")
    test_endpoint("GET /api/queries", f"{BASE_URL}/api/queries")
    
    # Test 6: Queries with user_id filter
    print_section("Test 6: Queries (user_id=default)")
    test_endpoint("GET /api/queries?user_id=default", f"{BASE_URL}/api/queries?user_id=default")
    
    # Test 7: Posts with user_id filter
    print_section("Test 7: Posts (user_id=default, limit=5)")
    test_endpoint("GET /api/posts?user_id=default&limit=5", f"{BASE_URL}/api/posts?user_id=default&limit=5")
    
    # Test 8: Sentiments with user_id filter
    print_section("Test 8: Sentiments (user_id=default)")
    test_endpoint("GET /api/sentiments?user_id=default", f"{BASE_URL}/api/sentiments?user_id=default")
    
    print_section("Testing Complete")
    print("\n✅ All tests executed. Check results above.\n")

if __name__ == "__main__":
    main()
