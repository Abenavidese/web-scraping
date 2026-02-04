"""
Direct test of data_unifier methods with user_id parameter
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shared.data_unifier import DataUnifier

def print_section(title):
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60)

def main():
    print_section("TESTING DATA_UNIFIER METHODS - User ID Filter")
    
    # Initialize database
    DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'social_media.db')
    unifier = DataUnifier(DB_PATH)
    
    # Test 1: get_stats() without user_id
    print_section("Test 1: get_stats() - All Users")
    try:
        stats = unifier.get_stats()
        print(f"✅ Success!")
        print(f"   Total Posts: {stats.get('total_posts')}")
        print(f"   Total Comments: {stats.get('total_comments')}")
        print(f"   Posts by Network: {stats.get('posts_by_network')}")
        print(f"   Sentiment Distribution: {stats.get('sentiment_distribution')}")
        print(f"   Total Queries: {stats.get('total_queries')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 2: get_stats() with user_id='default'
    print_section("Test 2: get_stats(user_id='default')")
    try:
        stats = unifier.get_stats(user_id='default')
        print(f"✅ Success!")
        print(f"   Total Posts: {stats.get('total_posts')}")
        print(f"   Total Comments: {stats.get('total_comments')}")
        print(f"   Posts by Network: {stats.get('posts_by_network')}")
        print(f"   Sentiment Distribution: {stats.get('sentiment_distribution')}")
        print(f"   Total Queries: {stats.get('total_queries')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 3: get_analytics_summary() without user_id
    print_section("Test 3: get_analytics_summary() - All Users")
    try:
        df = unifier.get_analytics_summary()
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Data:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 4: get_analytics_summary() with user_id='default'
    print_section("Test 4: get_analytics_summary(user_id='default')")
    try:
        df = unifier.get_analytics_summary(user_id='default')
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Data:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 5: get_queries() without user_id
    print_section("Test 5: get_queries() - All Users")
    try:
        df = unifier.get_queries()
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Data:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 6: get_queries() with user_id='default'
    print_section("Test 6: get_queries(user_id='default')")
    try:
        df = unifier.get_queries(user_id='default')
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Data:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 7: get_all_posts() with user_id='default'
    print_section("Test 7: get_all_posts(user_id='default', limit=5)")
    try:
        df = unifier.get_all_posts(user_id='default', limit=5)
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Sample Data (first 3 rows):")
            for idx, row in df.head(3).iterrows():
                print(f"\n   Post {idx + 1}:")
                print(f"      ID: {row.get('post_id')}")
                print(f"      Network: {row.get('network')}")
                print(f"      Author: {row.get('author')}")
                print(f"      Sentiment: {row.get('sentiment')}")
                print(f"      User ID: {row.get('user_id')}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test 8: get_sentiment_distribution() with user_id='default'
    print_section("Test 8: get_sentiment_distribution(user_id='default')")
    try:
        df = unifier.get_sentiment_distribution(user_id='default')
        print(f"✅ Success!")
        print(f"   Rows returned: {len(df)}")
        if len(df) > 0:
            print(f"   Columns: {list(df.columns)}")
            print(f"\n   Data:")
            print(df.to_string(index=False))
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print_section("Testing Complete")
    print("\n✅ All direct method tests executed successfully!\n")

if __name__ == "__main__":
    main()
