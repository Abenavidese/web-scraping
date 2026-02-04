"""
Smoke test for API Scraper Endpoint
Verifies connection and validation logic immediately
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_validation():
    print("="*60)
    print("  API SMOKE TEST - Validation")
    print("="*60)
    
    # Test 1: Missing Query
    print("\n🔍 Test 1: Missing Query Payload")
    try:
        response = requests.post(f"{BASE_URL}/api/scrape", json={"networks": ["x"]}, timeout=5)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 400:
            print("   ✅ Validated missing query correctly")
        else:
            print("   ❌ Validation failed")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return

    # Test 2: Invalid Network
    print("\n🔍 Test 2: Invalid Network logic (should check later but accepted if structure valid)")
    # Note: Our implementation checks valid networks inside run_scrapers logic 
    # but let's check basic structure validation
    try:
        response = requests.post(f"{BASE_URL}/api/scrape", json={"networks": "string_not_list", "query": "test"}, timeout=5)
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.json()}")
        if response.status_code == 400:
            print("   ✅ Validated networks type correctly")
        else:
            print("   ❌ Validation failed")
            
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")

if __name__ == "__main__":
    test_validation()
