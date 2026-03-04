# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import argparse
import pandas as pd

# Fix Windows encoding issues for emojis
# if sys.platform == 'win32':
#     import io
#     sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
#     sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scraper import XScraper
from visualization import generate_wordcloud, plot_top_words

# Load environment variables from .env file
# This is critical for multiprocessing on Windows
try:
    from dotenv import load_dotenv
    # Use absolute path to .env file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_path = os.path.join(script_dir, '.env')
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("WARNING: python-dotenv not installed. Environment variables may not load correctly.")

import re

def slugify(text):
    """Convert text to slug format for directory names"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

# CONFIGURATION
# PLEASE UPDATE THESE VALUES OR SET ENVIRONMENT VARIABLES
USERNAME = os.getenv("X_USERNAME", "@jsudbs61239")
PASSWORD = os.getenv("X_PASSWORD", "xxKPeYAEI00fohS")

# HARDCODED API KEY FALLBACK (for multiprocessing compatibility)
# If .env doesn't load properly in subprocess, this ensures it works
if not os.getenv("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = ""

async def main():
    import time
    start_total_time = time.time()
    
    print("=== Starting Lab Social Media Extraction ===")
    
    # ARGUMENT PARSING
    parser = argparse.ArgumentParser(description="X/Twitter Scraper")
    parser.add_argument("--query", type=str, default=None, help="Search topic")
    parser.add_argument("--year", type=int, default=None, help="Year to filter (e.g., 2023)")
    parser.add_argument("--month", type=int, default=None, help="Month to filter (1-12)")
    parser.add_argument("--posts", type=int, default=None, help="Number of posts to scrape (old mode)")
    parser.add_argument("--comments", type=int, default=None, help="Number of comments per post (old mode)")
    # NEW: Comment-based scraping
    parser.add_argument("--target-comments", type=int, default=None, help="Target number of total comments (new mode)")
    parser.add_argument("--max-posts", type=int, default=200, help="Maximum posts to scrape (safety limit)")
    
    args = parser.parse_args()
    
    # Usar argumentos de línea de comandos con valores por defecto
    print("\n--- Configuration ---")
    
    SEARCH_QUERY = args.query if args.query else "Inteligencia Artificial"
    
    # Añadir filtro por fecha si se especifica año
    if args.year:
        if args.month:
            import calendar
            _, last_day = calendar.monthrange(args.year, args.month)
            since_date = f"{args.year}-{args.month:02d}-01"
            until_date = f"{args.year}-{args.month:02d}-{last_day}"
        else:
            since_date = f"{args.year}-01-01"
            until_date = f"{args.year}-12-31"
            
        SEARCH_QUERY += f" since:{since_date} until:{until_date}"
        print(f"Date filter applied: {since_date} to {until_date}")
    
    # Determine scraping mode
    if args.target_comments:
        # NEW MODE: Comment-based scraping
        TARGET_COMMENTS = args.target_comments
        MAX_POSTS = args.max_posts
        TWEET_COUNT = None  # Will scrape until target is reached
        COMMENT_COUNT = 10  # Default comments per post to try
        print(f"[MODE] Comment-based scraping")
        print(f"Search topic: {SEARCH_QUERY}")
        print(f"Target comments: {TARGET_COMMENTS}")
        print(f"Max posts (safety): {MAX_POSTS}")
    else:
        # OLD MODE: Post-based scraping
        TWEET_COUNT = args.posts if args.posts is not None else 10
        COMMENT_COUNT = args.comments if args.comments is not None else 0
        TARGET_COMMENTS = None
        MAX_POSTS = TWEET_COUNT
        print(f"[MODE] Post-based scraping")
        print(f"Search topic: {SEARCH_QUERY}")
        print(f"Number of posts: {TWEET_COUNT}")
        print(f"Comments per post: {COMMENT_COUNT}")
    
    # User system configuration
    user_id = os.getenv("USER_ID", "default")
    query_slug = slugify(SEARCH_QUERY)
    
    # Create output directory with user system structure
    output_dir = os.path.join("..", "users", user_id, "x", query_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nUser ID: {user_id}")
    print(f"Output directory: {output_dir}")
    
    if USERNAME == "YOUR_USERNAME_HERE":
        print("WARNING: Username not set. Please edit main.py or set X_USERNAME env var.")
    
    # 1. Extraction
    start_scraping_time = time.time()
    scraper = XScraper(headless=False) 
    await scraper.start()
    
    tweets = []
    total_comments_collected = 0
    
    try:
        await scraper.login(USERNAME, PASSWORD)
        
        if TARGET_COMMENTS:
            # NEW MODE: Comment-based scraping
            print(f"\n[STARTING] Comment-based scraping...")
            print(f"Target: {TARGET_COMMENTS} comments | Max posts: {MAX_POSTS}")
            
            posts_scraped = 0
            while total_comments_collected < TARGET_COMMENTS and posts_scraped < MAX_POSTS:
                # Scrape more posts (in batches of 10)
                batch_size = min(10, MAX_POSTS - posts_scraped)
                new_tweets = await scraper.scrape_search(SEARCH_QUERY, count=batch_size)
                
                if not new_tweets:
                    print(f"[WARNING] No more posts found. Stopping.")
                    break
                
                # Scrape comments for each post
                for i, tweet in enumerate(new_tweets):
                    if total_comments_collected >= TARGET_COMMENTS:
                        break
                    
                    print(f"[Post {posts_scraped + i + 1}/{MAX_POSTS}] Getting comments for tweet by {tweet['author']}")
                    comments = await scraper.scrape_comments(tweet.get('url'), max_comments=COMMENT_COUNT)
                    tweet['comments'] = comments
                    total_comments_collected += len(comments)
                    
                    print(f"   [PROGRESS] {total_comments_collected}/{TARGET_COMMENTS} comments")
                
                tweets.extend(new_tweets)
                posts_scraped += len(new_tweets)
                
                if total_comments_collected >= TARGET_COMMENTS:
                    print(f"\n[SUCCESS] Target reached! Collected {total_comments_collected} comments from {posts_scraped} posts")
                    break
        else:
            # OLD MODE: Post-based scraping
            tweets = await scraper.scrape_search(SEARCH_QUERY, count=TWEET_COUNT)
            
            # Scrape Comments if requested
            if COMMENT_COUNT > 0 and tweets:
                print(f"\nExample: Extracting {COMMENT_COUNT} comments for each of the {len(tweets)} tweets...")
                for i, tweet in enumerate(tweets):
                    print(f"[{i+1}/{len(tweets)}] Getting comments for tweet by {tweet['author']}")
                    comments = await scraper.scrape_comments(tweet.get('url'), max_comments=COMMENT_COUNT)
                    tweet['comments'] = comments
                    total_comments_collected += len(comments)
                
    except Exception as e:
        print(f"An error occurred during scraping: {e}")
    finally:
        await scraper.close()
    
    end_scraping_time = time.time()

    if not tweets:
        print("No tweets collected. Exiting.")
        return

    print(f"\nCollected {len(tweets)} tweets.")
    
    # Ensure output directory exists
    os.makedirs("output", exist_ok=True)
    
    # Save Raw Data
    # Flatten data for CSV: main tweet text + comments text
    import uuid
    flattened_data = []
    for t in tweets:
        post_url = t.get('url', '')
        post_id = post_url.split('/')[-1] if post_url else str(uuid.uuid4())[:8]
        # Main tweet
        flattened_data.append({
            "type": "post",
            "author": t.get('author'),
            "text": t.get('text'),
            "parent_url": post_url,
            "timestamp": t.get('timestamp'),
            "item_id": post_id
        })
        # Comments
        for c in t.get('comments', []):
            comment_id = c.get('comment_id')
            if not comment_id:
                comment_id = str(uuid.uuid4())[:10]
            flattened_data.append({
                "type": "comment",
                "author": c.get('author'),
                "text": c.get('text'),
                "parent_url": post_url,
                "timestamp": c.get('timestamp'),
                "item_id": comment_id
            })

    df_raw = pd.DataFrame(flattened_data)
    tweets_raw_path = os.path.join(output_dir, "tweets_raw.csv")
    df_raw.to_csv(tweets_raw_path, index=False, encoding='utf-8')
    print(f"Raw data saved to {tweets_raw_path}")

    # 2. Processing (ETL Phase 2 - Centralized)
    start_processing_time = time.time()
    print("\nStarting Phase 2 ETL Processing...")
    
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from shared.data_cleaner import ETLProcessor
    
    etl = ETLProcessor()
    # Pass search query as topic keyword for relevance
    topic_kws = [args.query] if args.query else []
    
    # Run the full Phase 2 pipeline
    df_processed = etl.run_etl_pipeline(df_raw, platform='x', run_id=f"run_x_{int(time.time())}", topic_keywords=topic_kws)
    
    # Actively FILTER NOISE to improve dataset quality
    if 'is_noise' in df_processed.columns:
        initial_count = len(df_processed)
        df_processed = df_processed[~df_processed['is_noise']].copy()
        removed = initial_count - len(df_processed)
        if removed > 0:
            print(f"🧹 Noise Filter: Removed {removed} noisy comments (laughs, emojis, <3 words)")
            
    # Optional Relevance warning (we don't drop them yet, let LLM decide)
    if 'is_relevant' in df_processed.columns:
        irrelevant_count = len(df_processed[~df_processed['is_relevant']])
        if irrelevant_count > 0:
            print(f"⚠️  Relevance: {irrelevant_count} items do not contain keywords '{args.query}' (Kept in dataset)")
    
    # Save processed to CSV to debug locally
    tweets_processed_path = os.path.join(output_dir, "tweets_processed.csv")
    df_processed.to_csv(tweets_processed_path, index=False, encoding='utf-8')
    
    # Save to Parquet as requested in Phase 2
    staged_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'staged', 'x')
    os.makedirs(staged_dir, exist_ok=True)
    
    # Try to extract a representative year-month for the staged filename
    if not df_processed.empty:
        yr = args.year if args.year else df_processed['year'].mode().iloc[0] if 'year' in df_processed.columns and not df_processed['year'].isna().all() else datetime.datetime.now().year
        mo = args.month if args.month else df_processed['month'].mode().iloc[0] if 'month' in df_processed.columns and not df_processed['month'].isna().all() else datetime.datetime.now().month
        staged_parquet_path = os.path.join(staged_dir, f"{int(yr)}-{int(mo):02d}.parquet")
        
        # We must filter out duplicates and non-spanish for the deep sentiment analysis if strictly academic,
        # but the prompt says Q1/Q2 filters it. Let's keep it in the dataframe but flag it.
        # Save full staged dataset
        try:
            df_processed.to_parquet(staged_parquet_path, index=False)
            print(f"✅ Staged Parquet saved to {staged_parquet_path}")
        except Exception as e:
            print(f"⚠️ Could not save Parquet (install pyarrow/fastparquet): {e}")

    print(f"Processed data saved to {tweets_processed_path}")
    end_processing_time = time.time()

    # 3. Analysis & Visualization
    print("\nGenerating Visualizations...")
    
    # --- Create a "More Clean" / Refined Dataset ---
    df_refined = df_processed[['type', 'text', 'text_clean_semantic']].copy()
    
    # Basic Length Filter (Noise removal)
    # df_refined = df_refined[df_refined['text_clean_semantic'].str.split().str.len() > 2] # Relaxed filter
    
    df_refined.to_csv(os.path.join(output_dir, "tweets_refined.csv"), index=False, encoding='utf-8')
    print(f"Refined data saved to {output_dir}/tweets_refined.csv")
    
    # Drop NAs
    clean_texts = [str(x) for x in df_refined['text_clean_semantic'].tolist() if pd.notna(x)]
    all_text_corpus = ' '.join(clean_texts)
    
    generate_wordcloud(all_text_corpus, output_path=os.path.join(output_dir, "wordcloud.png"))
    
    # Re-create tokens for frequency plot
    df_processed['temp_tokens'] = df_processed['text_clean_semantic'].apply(lambda x: str(x).split() if pd.notna(x) else [])
    plot_top_words(df_processed['temp_tokens'], n=20, output_path=os.path.join(output_dir, "frequency_plot.png"))
    
    # 4. Sentiment Analysis Preparation
    print("\nPreparing Sentiment Analysis Data...")
    from sentiment_prep import prepare_sentiment_data_with_processed
    
    df_sentiment = prepare_sentiment_data_with_processed(df_processed)
    sentiment_input_path = os.path.join(output_dir, "sentiment_input.csv")
    df_sentiment.to_csv(sentiment_input_path, index=False, encoding='utf-8')
    print(f"Sentiment data saved to {sentiment_input_path}")
    
    # 5. Sentiment Analysis with DeepSeek (Automatic & Robust)
    start_sentiment_time = time.time()
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
    total_items_analyzed = 0
    
    print("\n" + "="*60)
    print("Starting Automatic Sentiment Analysis with DeepSeek (Phases 3 & 4)...")
    print("="*60)
    
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer
        
        analyzer = DeepSeekSentimentAnalyzer()
        
        # Inject year/month if available from args for harmonization
        if args.year and args.month:
            df_sentiment['year'] = args.year
            df_sentiment['month'] = args.month
            
        # Phase 3: Harmonize Dataset
        df_harmonized = analyzer.harmonize_dataset(df_sentiment, platform="x", target_per_month=1000)
        
        # Phase 4: Process Robustly
        df_results = analyzer.process_dataset_robustly(
            df_harmonized, 
            platform="x", 
            text_col='post_text', 
            comments_col='comments_json'
        )
        
        # Save results locally for this run
        results_csv_path = os.path.join(output_dir, "sentiment_results.csv")
        df_results.to_csv(results_csv_path, index=False, encoding='utf-8')
        
        if df_results is not None and not df_results.empty and 'sentiment' in df_results.columns:
            print(f"\nOptimization: Using centralized DeepSeek Analyzer")
            
            # Calculate sentiment distribution from results
            sentiment_counts = df_results['sentiment'].value_counts()
            
            # Update distribution for final report
            sentiment_distribution['positive'] = int(sentiment_counts.get('positive', 0))
            sentiment_distribution['negative'] = int(sentiment_counts.get('negative', 0))
            sentiment_distribution['neutral'] = int(sentiment_counts.get('neutral', 0))
            sentiment_distribution['mixed'] = int(sentiment_counts.get('mixed', 0))
            
            total_items_analyzed = len(df_results)
            
            # ✅ NUEVO: Generar CSV unificado en formato de investigación
            try:
                from shared.unified_csv_exporter import convert_x_twitter_to_unified
                
                unified_csv_path = os.path.join(output_dir, "formato_investigacion.csv")
                convert_x_twitter_to_unified(
                    results_csv_path,
                    unified_csv_path
                )
                print(f"📋 CSV Unificado (Formato Investigación): {unified_csv_path}")
            except Exception as e:
                print(f"⚠️  Error generando CSV unificado: {e}")
            
        else:
            print("\nScaling Warning: No results returned from analysis")
            
    except Exception as e:
        print(f"\nSentiment analysis failed: {e}")
        import traceback
        traceback.print_exc()
    
    end_sentiment_time = time.time()
    end_total_time = time.time()
    
    # --- PERFORMANCE METRICS REPORT ---
    scraping_duration = end_scraping_time - start_scraping_time
    processing_duration = end_processing_time - start_processing_time
    sentiment_duration = end_sentiment_time - start_sentiment_time
    total_duration = end_total_time - start_total_time
    
    # Count total items
    total_tweets = len(tweets)
    total_comments = sum(len(t.get('comments', [])) for t in tweets)
    total_items = total_tweets + total_comments
    
    print("\n" + "="*50)
    print(f"       PERFORMANCE REPORT: {SEARCH_QUERY.upper()}")
    print("="*50)
    print(f"Total Tweets Extracted: {total_tweets}")
    print(f"Total Comments:         {total_comments}")
    print(f"Items Analyzed:         {total_items_analyzed}")
    print("-" * 50)
    print(f"1. Scraping Phase:      {scraping_duration:.2f} seconds")
    print(f"   (Avg per tweet:      {scraping_duration/total_tweets if total_tweets else 0:.2f}s)")
    print(f"2. Text Processing:     {processing_duration:.2f} seconds")
    print(f"3. Sentiment Analysis:  {sentiment_duration:.2f} seconds (OpenAI)")
    print(f"   (Avg per item:       {sentiment_duration/total_items_analyzed if total_items_analyzed else 0:.2f}s)")
    print("-" * 50)
    print(f"TOTAL EXECUTION TIME:   {total_duration:.2f} seconds")
    print("="*50)
    
    # Generate metrics JSON for master scraper
    # Convert numpy int64 to native Python int for JSON serialization
    sentiment_dist_serializable = {
        k: int(v) for k, v in sentiment_distribution.items()
    }
    
    metrics = {
        "social_network": "X (Twitter)",
        "llm_used": "DeepSeek",
        "query": SEARCH_QUERY,
        "execution_times": {
            "scraping": round(scraping_duration, 2),
            "text_processing": round(processing_duration, 2),
            "sentiment_analysis": round(sentiment_duration, 2),
            "total": round(total_duration, 2)
        },
        "data_metrics": {
            "posts_extracted": int(total_tweets),
            "comments_extracted": int(total_comments),
            "comments_analyzed": int(total_items_analyzed),
            "total_text_items": int(total_items)
        },
        "sentiment_distribution": sentiment_dist_serializable,
        "performance_metrics": {
            "posts_per_second": round(total_tweets / scraping_duration if scraping_duration > 0 else 0, 2),
            "comments_per_second": round(total_items_analyzed / sentiment_duration if sentiment_duration > 0 else 0, 2),
            "avg_time_per_post": round(scraping_duration / total_tweets if total_tweets > 0 else 0, 2)
        }
    }
    
    # Save metrics JSON
    import json
    metrics_filename = os.path.join(output_dir, "metrics.json")
    with open(metrics_filename, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False)
    print(f"\n📊 Metrics saved to: {metrics_filename}")
    
    # Print metrics in JSON format for master scraper to capture
    print("\n### METRICS_JSON_START ###")
    print(json.dumps(metrics, ensure_ascii=False))
    print("### METRICS_JSON_END ###")
    
    print("\n=== Pipeline Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(main())
