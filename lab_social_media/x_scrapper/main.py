import asyncio
import os
import sys
import argparse
import pandas as pd
from scraper import XScraper
from processor import process_data_parallel
from visualization import generate_wordcloud, plot_top_words

# CONFIGURATION
# PLEASE UPDATE THESE VALUES OR SET ENVIRONMENT VARIABLES
USERNAME = os.getenv("X_USERNAME", "@jsudbs61239")
PASSWORD = os.getenv("X_PASSWORD", "xxKPeYAEI00fohS")

async def main():
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
    print("\nStarting Parallel Processing...")
    df_processed = process_data_parallel(flattened_data)
    df_processed.to_csv("output/tweets_processed.csv", index=False, encoding='utf-8')
    print("Processed data saved to output/tweets_processed.csv")

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
    
    print("\n=== Pipeline Completed Successfully ===")

if __name__ == "__main__":
    asyncio.run(main())
