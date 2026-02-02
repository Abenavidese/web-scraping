# -*- coding: utf-8 -*-
import asyncio
import os
import sys
import argparse
import pandas as pd

# Fix Windows encoding issues for emojis
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from scraper import XScraper
from processor import process_data_parallel
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
    parser.add_argument("--posts", type=int, default=None, help="Number of posts to scrape")
    parser.add_argument("--comments", type=int, default=None, help="Number of comments per post")
    
    args = parser.parse_args()
    
    # Usar argumentos de línea de comandos con valores por defecto
    print("\n--- Configuration ---")
    
    SEARCH_QUERY = args.query if args.query else "Inteligencia Artificial"
    TWEET_COUNT = args.posts if args.posts is not None else 10
    COMMENT_COUNT = args.comments if args.comments is not None else 0
    
    print(f"Search topic: {SEARCH_QUERY}")
    print(f"Number of posts: {TWEET_COUNT}")
    print(f"Comments per post: {COMMENT_COUNT}")
    
    if USERNAME == "YOUR_USERNAME_HERE":
        print("WARNING: Username not set. Please edit main.py or set X_USERNAME env var.")
    
    # 1. Extraction
    start_scraping_time = time.time()
    scraper = XScraper(headless=False) 
    await scraper.start()
    
    tweets = []
    try:
        await scraper.login(USERNAME, PASSWORD)
        tweets = await scraper.scrape_search(SEARCH_QUERY, count=TWEET_COUNT)
        
        # Scrape Comments if requested
        if COMMENT_COUNT > 0 and tweets:
            print(f"\nExample: Extracting {COMMENT_COUNT} comments for each of the {len(tweets)} tweets...")
            for i, tweet in enumerate(tweets):
                print(f"[{i+1}/{len(tweets)}] Getting comments for tweet by {tweet['author']}")
                comments = await scraper.scrape_comments(tweet.get('url'), max_comments=COMMENT_COUNT)
                tweet['comments'] = comments
                
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
    flattened_data = []
    for t in tweets:
        # Main tweet
        flattened_data.append({
            "type": "post",
            "author": t.get('author'),
            "text": t.get('text'),
            "parent_url": t.get('url')
        })
        # Comments
        for c in t.get('comments', []):
             flattened_data.append({
                "type": "comment",
                "author": c.get('author'),
                "text": c.get('text'),
                "parent_url": t.get('url')
            })

    df_raw = pd.DataFrame(flattened_data)
    df_raw.to_csv("output/tweets_raw.csv", index=False, encoding='utf-8')
    print("Raw data saved to output/tweets_raw.csv")

    # 2. Processing (Parallel)
    # We pass the flattened data to processor
    start_processing_time = time.time()
    print("\nStarting Parallel Processing...")
    df_processed = process_data_parallel(flattened_data)
    df_processed.to_csv("output/tweets_processed.csv", index=False, encoding='utf-8')
    print("Processed data saved to output/tweets_processed.csv")
    end_processing_time = time.time()

    # 3. Analysis & Visualization
    print("\nGenerating Visualizations...")
    
    # --- Create a "More Clean" / Refined Dataset ---
    df_refined = df_processed[['type', 'text', 'processed_text']].copy()
    
    # Basic Length Filter (Noise removal)
    # df_refined = df_refined[df_refined['processed_text'].str.split().str.len() > 2] # Relaxed filter
    
    df_refined.to_csv("output/tweets_refined.csv", index=False, encoding='utf-8')
    print("Refined data (content only) saved to output/tweets_refined.csv")
    
    all_text_corpus = ' '.join(df_refined['processed_text'].tolist())
    
    generate_wordcloud(all_text_corpus, output_path="output/wordcloud.png")
    plot_top_words(df_processed['processed_tokens'], n=20, output_path="output/frequency_plot.png")
    
    # 4. Sentiment Analysis Preparation
    print("\nPreparing Sentiment Analysis Data...")
    from sentiment_prep import prepare_sentiment_data_with_processed, generate_llm_prompts_csv
    
    df_sentiment = prepare_sentiment_data_with_processed(df_processed)
    df_sentiment.to_csv("output/sentiment_input.csv", index=False, encoding='utf-8')
    print("Sentiment data saved to output/sentiment_input.csv")
    
    # Generate LLM prompts
    generate_llm_prompts_csv(df_sentiment, output_path="output/llm_prompts.csv")
    
    # 5. Sentiment Analysis with DeepSeek
    start_sentiment_time = time.time()
    sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
    total_items_analyzed = 0
    
    print("\n" + "="*60)
    print("Starting Automatic Sentiment Analysis with DeepSeek V3...")
    print("="*60)
    
    try:
        from sentiment_analyzer import analyze_batch_deepseek
        
        # Analizar sentimientos (el cliente se gestiona internamente)
        df_results = analyze_batch_deepseek(df_sentiment)
        
        # Guardar resultados
        df_results.to_csv("output/sentiment_results.csv", index=False, encoding='utf-8')
        print(f"\n💾 Sentiment results saved to output/sentiment_results.csv")
        
        # Mostrar resumen
        print("\n📊 Sentiment Summary:")
        if 'sentiment' in df_results.columns:
            sentiment_counts = df_results['sentiment'].value_counts()
            for sentiment, count in sentiment_counts.items():
                print(f"   {sentiment}: {count}")
        
            # Calculate sentiment distribution
            total_items_analyzed = len(df_results)
            sentiment_distribution['positive'] = sentiment_counts.get('POSITIVE', sentiment_counts.get('positive', 0))
            sentiment_distribution['negative'] = sentiment_counts.get('NEGATIVE', sentiment_counts.get('negative', 0))
            sentiment_distribution['neutral'] = sentiment_counts.get('NEUTRAL', sentiment_counts.get('neutral', 0))
        
        if 'sentiment_score' in df_results.columns:
            avg_score = df_results['sentiment_score'].astype(float).mean()
            print(f"\n📈 Average sentiment score: {avg_score:.2f}")

    except ImportError:
        print("\n⚠️ Could not import sentiment_analyzer. Make sure dependencies are installed.")
    except Exception as e:
        print(f"\n⚠️ Sentiment analysis failed: {e}")
        # print("   You can run it manually later with: python sentiment_analyzer.py")
    
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
        "llm_used": "OpenAI",
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
    metrics_filename = f"output/metrics_{SEARCH_QUERY}.json"
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
