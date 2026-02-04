"""
Simplified test to verify user system directory structure
Creates mock data in the new directory structure
"""
import os
import json
import csv
from datetime import datetime

def slugify(text):
    """Convert text to slug format"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def create_test_data():
    print("="*60)
    print("  TESTING USER SYSTEM - Directory Structure")
    print("="*60)
    
    # Configuration
    user_id = os.getenv("USER_ID", "default")
    query = "Test Query"
    query_slug = slugify(query)
    network = "x"
    
    print(f"\n📋 Configuration:")
    print(f"   User ID: {user_id}")
    print(f"   Query: {query}")
    print(f"   Query Slug: {query_slug}")
    print(f"   Network: {network}")
    
    # Create directory structure
    output_dir = os.path.join("..", "users", user_id, network, query_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n📁 Created directory: {output_dir}")
    
    # Create mock sentiment_results.csv
    sentiment_data = [
        {
            "post_id": "test_001",
            "network": "x",
            "post_author": "TestUser1",
            "post_text": "This is a test post about AI",
            "post_url": "https://x.com/test/001",
            "post_processed": "test post ai",
            "sentiment": "positive",
            "sentiment_score": 0.8,
            "sentiment_reasoning": "Positive tone about AI",
            "num_comments": 2,
            "comment_id": "comment_001",
            "comment_author": "Commenter1",
            "comment_text": "Great post!",
            "comment_processed": "great post"
        },
        {
            "post_id": "test_002",
            "network": "x",
            "post_author": "TestUser2",
            "post_text": "Another test about technology",
            "post_url": "https://x.com/test/002",
            "post_processed": "test technology",
            "sentiment": "neutral",
            "sentiment_score": 0.5,
            "sentiment_reasoning": "Neutral informational content",
            "num_comments": 1,
            "comment_id": "comment_002",
            "comment_author": "Commenter2",
            "comment_text": "Interesting",
            "comment_processed": "interesting"
        },
        {
            "post_id": "test_003",
            "network": "x",
            "post_author": "TestUser3",
            "post_text": "Testing negative sentiment",
            "post_url": "https://x.com/test/003",
            "post_processed": "testing negative sentiment",
            "sentiment": "negative",
            "sentiment_score": 0.3,
            "sentiment_reasoning": "Negative sentiment detected",
            "num_comments": 0,
            "comment_id": "",
            "comment_author": "",
            "comment_text": "",
            "comment_processed": ""
        }
    ]
    
    # Save sentiment_results.csv
    csv_path = os.path.join(output_dir, "sentiment_results.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=sentiment_data[0].keys())
        writer.writeheader()
        writer.writerows(sentiment_data)
    
    print(f"   ✅ Created: sentiment_results.csv ({len(sentiment_data)} rows)")
    
    # Create mock metrics.json
    metrics = {
        "social_network": "X (Twitter)",
        "llm_used": "DeepSeek",
        "query": query,
        "execution_times": {
            "scraping": 10.5,
            "text_processing": 2.3,
            "sentiment_analysis": 5.7,
            "total": 18.5
        },
        "data_metrics": {
            "posts_extracted": 3,
            "comments_extracted": 3,
            "comments_analyzed": 3,
            "total_text_items": 6
        },
        "sentiment_distribution": {
            "positive": 1,
            "negative": 1,
            "neutral": 1
        },
        "performance_metrics": {
            "posts_per_second": 0.29,
            "comments_per_second": 0.53,
            "avg_time_per_post": 3.5
        }
    }
    
    metrics_path = os.path.join(output_dir, "metrics.json")
    with open(metrics_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    
    print(f"   ✅ Created: metrics.json")
    
    # Verify directory structure
    print(f"\n📂 Directory Structure:")
    print(f"   {output_dir}/")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        size = os.path.getsize(file_path)
        print(f"   ├── {file} ({size} bytes)")
    
    print(f"\n✅ Test data created successfully!")
    print(f"\n📍 Full path: {os.path.abspath(output_dir)}")
    
    return output_dir, csv_path, query

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    output_dir, csv_path, query = create_test_data()
    
    print("\n" + "="*60)
    print("  Next Steps:")
    print("="*60)
    print(f"\n1. Import data:")
    print(f"   python import_data.py")
    print(f"   (Select network: x)")
    print(f"   (Enter query: {query})")
    print(f"\n2. Verify in database:")
    print(f"   python test_direct_methods.py")
    print(f"\n3. Query API:")
    print(f"   curl \"http://localhost:5000/api/posts?user_id=default&query={query}\"")
    print("\n" + "="*60)
