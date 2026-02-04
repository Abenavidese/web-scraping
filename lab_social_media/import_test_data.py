"""
Automated import of test data
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.data_unifier import DataUnifier

def import_test_data():
    print("="*60)
    print("  IMPORTING TEST DATA")
    print("="*60)
    
    # Configuration
    user_id = "default"
    network = "x"
    query = "Test Query"
    query_slug = "test_query"
    
    # Paths
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'social_media.db')
    sentiment_results_path = os.path.join(
        os.path.dirname(__file__), 
        '..', 'users', user_id, network, query_slug, 
        'sentiment_results.csv'
    )
    
    print(f"\n📋 Configuration:")
    print(f"   User ID: {user_id}")
    print(f"   Network: {network}")
    print(f"   Query: {query}")
    print(f"   CSV Path: {sentiment_results_path}")
    
    # Verify file exists
    if not os.path.exists(sentiment_results_path):
        print(f"\n❌ Error: File not found: {sentiment_results_path}")
        return False
    
    print(f"   ✅ File found ({os.path.getsize(sentiment_results_path)} bytes)")
    
    # Initialize database
    print(f"\n📦 Initializing database...")
    unifier = DataUnifier(DB_PATH)
    
    # Import data
    print(f"\n📥 Importing data...")
    try:
        unifier.import_from_csv(
            network=network,
            sentiment_results_path=sentiment_results_path,
            query=query,
            user_id=user_id
        )
        print(f"   ✅ Import successful!")
        return True
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_import():
    print("\n" + "="*60)
    print("  VERIFYING IMPORT")
    print("="*60)
    
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'social_media.db')
    unifier = DataUnifier(DB_PATH)
    
    # Get posts for Test Query
    print(f"\n🔍 Querying posts for 'Test Query'...")
    df = unifier.get_all_posts(user_id='default', query='Test Query', limit=10)
    
    print(f"   ✅ Found {len(df)} posts")
    
    if len(df) > 0:
        print(f"\n📊 Sample Data:")
        for idx, row in df.iterrows():
            print(f"\n   Post {idx + 1}:")
            print(f"      ID: {row['post_id']}")
            print(f"      Author: {row['author']}")
            print(f"      Text: {row['text'][:50]}...")
            print(f"      Sentiment: {row['sentiment']}")
            print(f"      User ID: {row['user_id']}")
            print(f"      Query: {row['query']}")
    
    # Get stats
    print(f"\n📈 Statistics:")
    stats = unifier.get_stats(user_id='default')
    print(f"   Total Posts: {stats['total_posts']}")
    print(f"   Total Comments: {stats['total_comments']}")
    print(f"   Sentiment Distribution: {stats['sentiment_distribution']}")
    
    return len(df) > 0

if __name__ == "__main__":
    success = import_test_data()
    
    if success:
        verify_import()
        
        print("\n" + "="*60)
        print("  SUCCESS!")
        print("="*60)
        print("\n✅ Test data imported and verified successfully!")
        print("\n📍 Next: Query API to verify endpoints")
        print("   python test_direct_methods.py")
    else:
        print("\n" + "="*60)
        print("  FAILED")
        print("="*60)
        print("\n❌ Import failed. Check errors above.")
