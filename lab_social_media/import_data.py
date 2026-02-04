# -*- coding: utf-8 -*-
"""
Import Script - Import all scraper data into unified database
Run this after executing scrapers to populate the database
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.data_unifier import DataUnifier

def main():
    """Import all scraper data into the database"""
    print("=" * 70)
    print("📥 IMPORTING SCRAPER DATA INTO UNIFIED DATABASE")
    print("=" * 70)
    
    # Initialize database
    unifier = DataUnifier('data/social_media.db')
    
    # Get user_id from environment or input
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    user_id = os.getenv("USER_ID")
    if not user_id:
        user_id = input("\nEnter user ID (default: default): ").strip()
        if not user_id:
            user_id = "default"
    
    print(f"\n🔐 User ID: '{user_id}'")
    
    # Define query
    query = input("\nEnter the search query used for scraping: ").strip()
    if not query:
        query = "Nicolas Muñoz"  # Default
    
    print(f"🔍 Using query: '{query}'")
    
    # Convert query to slug format
    import re
    query_slug = query.lower()
    query_slug = re.sub(r'[^\w\s-]', '', query_slug)
    query_slug = re.sub(r'[-\s]+', '_', query_slug).strip('_')
    
    print(f"📁 Query slug: '{query_slug}'")
    
    # Import X/Twitter data
    print("\n" + "-" * 70)
    print("1. X/TWITTER")
    print("-" * 70)
    x_sentiment = f"users/{user_id}/x/{query_slug}/sentiment_results.csv"
    x_metrics = f"users/{user_id}/x/{query_slug}/metrics.json"
    
    if os.path.exists(x_sentiment):
        unifier.import_from_csv('x', x_sentiment, query, user_id)
        if os.path.exists(x_metrics):
            unifier.import_metrics('x', x_metrics, user_id)
    else:
        print(f"⚠️ File not found: {x_sentiment}")
    
    # Import Instagram data
    print("\n" + "-" * 70)
    print("2. INSTAGRAM")
    print("-" * 70)
    # Instagram usa sentiment_results_{query}.csv
    ig_sentiment = f"users/{user_id}/instagram/{query_slug}/sentiment_results_{query_slug}.csv"
    if not os.path.exists(ig_sentiment):
        # Fallback: buscar sentiment_results.csv sin nombre de query
        ig_sentiment = f"users/{user_id}/instagram/{query_slug}/sentiment_results.csv"
    ig_metrics = f"users/{user_id}/instagram/{query_slug}/metrics.json"
    
    if os.path.exists(ig_sentiment):
        unifier.import_from_csv('instagram', ig_sentiment, query, user_id)
        if os.path.exists(ig_metrics):
            unifier.import_metrics('instagram', ig_metrics, user_id)
    else:
        print(f"⚠️ File not found: {ig_sentiment}")
    
    # Import Facebook data
    print("\n" + "-" * 70)
    print("3. FACEBOOK")
    print("-" * 70)
    # Facebook ahora usa datos_extraidos_deepseek.csv igual que LinkedIn
    fb_sentiment = f"users/{user_id}/facebook/{query_slug}/datos_extraidos_deepseek.csv"
    if not os.path.exists(fb_sentiment):
        # Fallback a formatos antiguos
        fb_sentiment = f"users/{user_id}/facebook/{query_slug}/sentiment_results_{query_slug}.csv"
    if not os.path.exists(fb_sentiment):
        fb_sentiment = f"users/{user_id}/facebook/{query_slug}/sentiment_results.csv"
    if not os.path.exists(fb_sentiment):
        fb_sentiment = f"users/{user_id}/facebook/{query_slug}/processed_facebook_{query_slug}.csv"
    fb_metrics = f"users/{user_id}/facebook/{query_slug}/metrics.json"
    
    if os.path.exists(fb_sentiment):
        unifier.import_from_csv('facebook', fb_sentiment, query, user_id)
        if os.path.exists(fb_metrics):
            unifier.import_metrics('facebook', fb_metrics, user_id)
    else:
        print(f"⚠️ File not found: {fb_sentiment}")
    
    # Import LinkedIn data
    print("\n" + "-" * 70)
    print("4. LINKEDIN")
    print("-" * 70)
    # LinkedIn usa datos_extraidos_deepseek.csv
    li_sentiment = f"users/{user_id}/linkedin/{query_slug}/datos_extraidos_deepseek.csv"
    if not os.path.exists(li_sentiment):
        # Fallback
        li_sentiment = f"users/{user_id}/linkedin/{query_slug}/sentiment_results.csv"
    li_metrics = f"users/{user_id}/linkedin/{query_slug}/metrics.json"
    
    if os.path.exists(li_sentiment):
        unifier.import_from_csv('linkedin', li_sentiment, query, user_id)
        if os.path.exists(li_metrics):
            unifier.import_metrics('linkedin', li_metrics, user_id)
    else:
        print(f"⚠️ File not found: {li_sentiment}")
    
    # Display final statistics
    print("\n" + "=" * 70)
    print("📊 FINAL DATABASE STATISTICS")
    print("=" * 70)
    
    stats = unifier.get_stats()
    
    print(f"\n✅ Total Posts: {stats['total_posts']}")
    print(f"✅ Total Comments: {stats['total_comments']}")
    print(f"✅ Total Queries: {stats['total_queries']}")
    
    if stats['posts_by_network']:
        print("\n📱 Posts by Network:")
        for network, count in stats['posts_by_network'].items():
            print(f"   • {network.capitalize()}: {count}")
    
    if stats['sentiment_distribution']:
        print("\n💭 Sentiment Distribution:")
        for sentiment, count in stats['sentiment_distribution'].items():
            print(f"   • {sentiment.capitalize()}: {count}")
    
    # Show sentiment by network
    print("\n" + "=" * 70)
    print("📈 SENTIMENT BY NETWORK")
    print("=" * 70)
    sentiment_df = unifier.get_sentiment_distribution()
    if len(sentiment_df) > 0:
        print(sentiment_df.to_string(index=False))
    else:
        print("No sentiment data available")
    
    # Export to JSON
    export_path = f'data/export_{query.replace(" ", "_")}.json'
    unifier.export_to_json(export_path, query=query)
    
    print("\n" + "=" * 70)
    print("✅ IMPORT COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print(f"\n📦 Database: data/social_media.db")
    print(f"📄 Export: {export_path}")
    print("\n💡 Next step: Start the API server with:")
    print("   cd api")
    print("   python app.py")
    print("=" * 70 + "\n")
    
    unifier.close()


if __name__ == "__main__":
    main()
