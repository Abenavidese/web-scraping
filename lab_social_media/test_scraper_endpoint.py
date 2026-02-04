"""
Test script for /api/scrape endpoint
Tests multiprocessing execution of selected scrapers
"""
import requests
import json
import time

BASE_URL = "http://localhost:5000"

def print_section(title):
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def test_scrape_endpoint(networks, query, num_posts=3, num_comments=2):
    """
    Test the /api/scrape endpoint
    
    Args:
        networks (list): Networks to scrape
        query (str): Search query
        num_posts (int): Number of posts
        num_comments (int): Number of comments
    """
    print_section(f"Testing: {', '.join(networks)}")
    
    # Prepare request
    payload = {
        "networks": networks,
        "query": query,
        "num_posts": num_posts,
        "num_comments": num_comments
    }
    
    print(f"\n📤 Request:")
    print(json.dumps(payload, indent=2))
    
    # Send request
    print(f"\n⏳ Sending POST request to {BASE_URL}/api/scrape...")
    print(f"   (This may take a while - scrapers are running in parallel)")
    
    start_time = time.time()
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/scrape",
            json=payload,
            timeout=300  # 5 minute timeout
        )
        
        end_time = time.time()
        request_time = end_time - start_time
        
        print(f"\n✅ Response received in {request_time:.2f}s")
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"\n📊 Results Summary:")
            print(f"   Query: {data.get('query')}")
            print(f"   Networks Requested: {data.get('networks_requested')}")
            print(f"   Networks Completed: {data.get('networks_completed')}")
            print(f"   Successful: {data.get('successful')}")
            print(f"   Failed: {data.get('failed')}")
            print(f"   Total Execution Time: {data.get('total_execution_time')}s")
            
            print(f"\n📝 Individual Results:")
            for result in data.get('results', []):
                status_emoji = "✅" if result['status'] == 'success' else "❌"
                print(f"\n   {status_emoji} {result['name']}:")
                print(f"      Status: {result['status']}")
                print(f"      Execution Time: {result['execution_time']}s")
                
                if result.get('metrics'):
                    metrics = result['metrics']
                    print(f"      Posts Extracted: {metrics.get('data_metrics', {}).get('posts_extracted', 'N/A')}")
                    print(f"      Comments Extracted: {metrics.get('data_metrics', {}).get('comments_extracted', 'N/A')}")
                    print(f"      Sentiment Distribution: {metrics.get('sentiment_distribution', 'N/A')}")
                
                if result.get('error'):
                    print(f"      Error: {result['error'][:200]}...")
            
            return True
        else:
            print(f"\n❌ Error Response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Connection Error: API server not running")
        print(f"   💡 Start server with: cd api && python app.py")
        return False
    except requests.exceptions.Timeout:
        print(f"\n❌ Request Timeout: Scrapers took too long")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False

def main():
    print_section("API SCRAPER ENDPOINT TEST - Multiprocessing")
    
    print("\n📋 This test will execute scrapers in parallel using multiprocessing")
    print("   Each test uses small data (3 posts, 2 comments) for quick execution")
    
    # Test 1: Single network (X/Twitter)
    print_section("Test 1: Single Network (X/Twitter)")
    test_scrape_endpoint(
        networks=["x"],
        query="Test Single",
        num_posts=3,
        num_comments=2
    )
    
    # Test 2: Two networks (X + Facebook)
    print_section("Test 2: Two Networks (X + Facebook)")
    test_scrape_endpoint(
        networks=["x", "facebook"],
        query="Test Dual",
        num_posts=3,
        num_comments=2
    )
    
    # Test 3: All four networks
    print_section("Test 3: All Four Networks (Parallel)")
    test_scrape_endpoint(
        networks=["x", "instagram", "facebook", "linkedin"],
        query="Test All",
        num_posts=3,
        num_comments=2
    )
    
    # Test 4: Invalid network
    print_section("Test 4: Error Handling (Invalid Network)")
    test_scrape_endpoint(
        networks=["invalid_network"],
        query="Test Error",
        num_posts=3,
        num_comments=2
    )
    
    print_section("Testing Complete")
    print("\n✅ All tests executed. Check results above.\n")

if __name__ == "__main__":
    print("\n⚠️  IMPORTANT:")
    print("   1. Make sure the API server is running: cd api && python app.py")
    print("   2. These tests will actually execute scrapers (may take time)")
    print("   3. Make sure you have valid credentials in .env files")
    print("   4. Browser windows will open for each scraper")
    
    # input("\nPress Enter to continue with testing...")
    
    main()
