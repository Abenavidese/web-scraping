import os
import sys
import argparse
import random
import time
import json
import re
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def slugify(text):
    """Convert text to slug format for directory names"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def smart_sleep(min_seconds=0.5, max_seconds=2, probability=0.5):
    """
    Sleeps conditionally to simulate human behavior and avoid detection.
    
    Args:
        min_seconds: Minimum sleep time
        max_seconds: Maximum sleep time  
        probability: Probability of actually sleeping (0.0 to 1.0)
    """
    if random.random() < probability:
        time.sleep(random.uniform(min_seconds, max_seconds))

def format_hashtag(query):
    """
    Converts multi-word queries to CamelCase hashtags.
    Example: "Cristian Zamora" -> "CristianZamora"
    """
    # Remove special characters and extra spaces
    query = query.strip()
    
    # If contains spaces, convert to CamelCase
    if ' ' in query:
        words = query.split()
        # Capitalize first letter of each word and join
        camel_case = ''.join(word.capitalize() for word in words)
        return camel_case
    
    # If no spaces, return as-is (single word)
    return query

def run(search_query=None, num_posts=None, num_comments=None):
    import time
    start_total_time = time.time()
    
    # Argumentos compatibles con master_scraper.py
    parser = argparse.ArgumentParser(description="Instagram Scraper - Extracción de Posts y Comentarios")
    parser.add_argument("--query", type=str, default="python", help="Término de búsqueda")
    parser.add_argument("--posts", type=int, default=5, help="Número de posts a extraer")
    parser.add_argument("--comments", type=int, default=5, help="Número de comentarios por post")
    
    args = parser.parse_args()
    
    search_query = args.query
    num_posts_to_scrape = args.posts
    num_comments_to_scrape = args.comments
    
    print(f"Search topic: {search_query}")
    print(f"Number of posts: {num_posts_to_scrape}")
    print(f"Comments per post: {num_comments_to_scrape}")

    # User system configuration
    user_id = os.getenv("USER_ID", "default")
    query_slug = slugify(search_query)
    
    # Create output directory with user system structure
    output_dir = os.path.join("..", "users", user_id, "instagram", query_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nUser ID: {user_id}")
    print(f"Output directory: {output_dir}")
    
    with sync_playwright() as p:
        # Launch with slow_mo to mimic human speed slightly, using Microsoft Edge
        browser = p.chromium.launch(headless=False, slow_mo=100, channel="msedge")
        
        # Load the saved session
        try:
            context = browser.new_context(storage_state="auth.json")
        except FileNotFoundError:
            print("Session file 'auth.json' not found. Starting automatic login...")
            try:
                import login_auto
                login_auto.run()
                # Re-attempt to load the session after login
                context = browser.new_context(storage_state="auth.json")
            except Exception as e:
                 print(f"Auto-login failed: {e}")
                 browser.close()
                 return

        page = context.new_page()
        
        print("Navigating to Instagram...")
        page.goto("https://www.instagram.com/")
        smart_sleep(2, 3, probability=1.0)  # Always wait for initial load
        
        # Search functionality
        print(f"Searching for '{search_query}'...")
        
        # Format hashtag for multi-word queries
        formatted_query = format_hashtag(search_query)
        print(f"Formatted hashtag: #{formatted_query}")
        
        # Click search icon (SVG or aria-label) - Instagram UI changes frequently, so we try a few strategies or go directly to URL
        # Strategy A: Go directly to explore/tags
        tag_url = f"https://www.instagram.com/explore/tags/{formatted_query}/"
        print(f"Direct navigation to: {tag_url}")
        page.goto(tag_url)
        smart_sleep(2, 4, probability=1.0)  # Always wait for search results
        
        # Check if login failed or page didn't load
        if "login" in page.url:
            print("Redirected to login page. Session might be invalid or expired.")
            return

        # Extract data with automatic scrolling
        posts_data = []
        
        print("Extracting posts with automatic scrolling...")
        
        # Process posts based on user input
        count = 0
        unique_links = set()
        processed_indices = set()
        
        # Scroll and load more posts dynamically
        max_scroll_attempts = 30  # Prevent infinite scrolling
        scroll_attempt = 0
        no_new_posts_count = 0
        
        print(f"Target: {num_posts_to_scrape} posts")
        
        while count < num_posts_to_scrape and scroll_attempt < max_scroll_attempts:
            # Get current post count
            thumbnails = page.locator('a[href^=\"/p/\"]')
            count_found = thumbnails.count()
            
            if scroll_attempt == 0:
                print(f"Initially detected {count_found} posts on page")
            
            # Process new posts
            new_posts_found = False
            for i in range(count_found):
                if count >= num_posts_to_scrape:
                    break
                
                # Skip already processed posts
                if i in processed_indices:
                    continue
                    
                try:
                    # Re-locate to avoid stale element errors
                    thumbnail = thumbnails.nth(i)
                    
                    # Get URL to check for duplicates
                    post_url_suffix = thumbnail.get_attribute("href")
                    if not post_url_suffix or post_url_suffix in unique_links:
                        processed_indices.add(i)
                        continue
                    
                    unique_links.add(post_url_suffix)
                    processed_indices.add(i)
                    new_posts_found = True
                    
                    print(f"Processing post {count + 1}/{num_posts_to_scrape}...")
                    
                    # Scroll into view
                    thumbnail.scroll_into_view_if_needed()
                    smart_sleep(0.5, 1, probability=0.3)
                    
                    full_url = f"https://www.instagram.com{post_url_suffix}"
                    
                    # Click to open modal
                    thumbnail.click()
                    smart_sleep(2, 3, probability=1.0)
                    
                    # Extract Data from Modal
                    try:
                        modal_img = page.locator('article img').nth(0)
                        image_url = modal_img.get_attribute("src")
                        caption_alt = modal_img.get_attribute("alt")
                    except:
                        image_url = "N/A"
                        caption_alt = "N/A"
                    
                    # Extract comments
                    print("  Extracting comments...")
                    comments_list = []
                    try:
                        page.wait_for_selector('article ul', timeout=5000)
                        comment_elements = page.locator('article ul li')
                        
                        c_count = 0
                        for j in range(comment_elements.count()):
                            if c_count >= num_comments_to_scrape:
                                break
                            
                            text_content = comment_elements.nth(j).inner_text()
                            lines = text_content.split('\n')
                            if len(lines) >= 2:
                                user = lines[0]
                                comment_text = lines[1]
                                comments_list.append({"user": user, "text": comment_text})
                                c_count += 1
                    except Exception as e:
                        print(f"  Could not extract comments: {e}")
                    
                    posts_data.append({
                        "post_url": full_url,
                        "caption_snippet": caption_alt[:100] + "..." if caption_alt and len(caption_alt) > 100 else caption_alt,
                        "image_url": image_url,
                        "comments": comments_list
                    })
                    
                    # Close modal
                    print("  Closing modal...")
                    page.keyboard.press("Escape")
                    smart_sleep(1, 2, probability=0.7)
                    
                    count += 1
                    
                except Exception as e:
                    print(f"  Error processing post {i}: {e}")
                    processed_indices.add(i)
                    # Close modal if it's open
                    try:
                        page.keyboard.press("Escape")
                        smart_sleep(0.5, 1, probability=0.5)
                    except:
                        pass
                    continue
            
            # Check if we found new posts
            if not new_posts_found:
                no_new_posts_count += 1
                if no_new_posts_count >= 3:
                    print(f"\nNo new posts found after {no_new_posts_count} scroll attempts.")
                    print(f"Instagram may have limited results for this hashtag.")
                    break
            else:
                no_new_posts_count = 0
            
            # If we need more posts, scroll down to load more
            if count < num_posts_to_scrape:
                print(f"Scrolling to load more posts... ({count}/{num_posts_to_scrape} collected)")
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                smart_sleep(2, 4, probability=1.0)  # Wait for new posts to load
                scroll_attempt += 1
            
        print(f"Found {len(posts_data)} posts.")
        
        # Save to file in Resultados folder
        filename = os.path.join(output_dir, f"results_{search_query}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        
        browser.close()
        end_scraping_time = time.time()
        
        # --- Integration with NLP Pipeline ---
        try:
            print("\n--- Starting Automatic Text Processing ---")
            import procesamiento_texto
            
            # Reprocess all files or just the current one? 
            # The user asked to "do the cleaning and everything else" after searching.
            # We will process just the current result to show immediate feedback.
            
            datos_nuevos = procesamiento_texto.cargar_datos_json(filename)
            tokens_limpios, tokens_stemmed = procesamiento_texto.procesar_texto(datos_nuevos)
            
            print(f"Processed {len(datos_nuevos)} new posts.")
            
            # Save processed data to JSON
            processed_filename = os.path.join(output_dir, f"processed_{search_query}.json")
            processed_data = {
                "search_query": search_query,
                "total_posts": len(datos_nuevos),
                "tokens_limpios": tokens_limpios,
                "tokens_stemmed": tokens_stemmed
            }
            
            with open(processed_filename, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            
            print(f"Processed text saved to: {processed_filename}")

            # Save processed data to CSV
            import csv
            csv_filename = os.path.join(output_dir, f"processed_{search_query}.csv")
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Token"])
                for token in tokens_limpios:
                    writer.writerow(["Limpio", token])
                for token in tokens_stemmed:
                    writer.writerow(["Stemmed", token])
            
            print(f"Processed text saved to: {csv_filename}")

            # Visualizar solo para este término
            output_img = os.path.join(output_dir, f"frecuencia_{search_query}.png")
            procesamiento_texto.visualizar_nube_palabras(tokens_limpios, output_img)
            
            print(f"Analysis complete. Image saved to: {output_img}")
            end_text_processing_time = time.time()
            
            # --- Sentiment Analysis Integration ---
            start_sentiment_time = time.time()
            sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
            total_comments_analyzed = 0
            
            try:
                print("\n--- Starting Sentiment Analysis (DeepSeek) ---")
                import sentiment_prep
                import sentiment_analyzer_hf as sentiment_analyzer
                
                # Prepare sentiment data
                print("Preparing sentiment data...")
                df_sentiment = sentiment_prep.prepare_sentiment_data_instagram(filename)
                
                if not df_sentiment.empty:
                    # Save sentiment input
                    sentiment_input_path = os.path.join(output_dir, f"sentiment_input_{search_query}.csv")
                    df_sentiment.to_csv(sentiment_input_path, index=False, encoding='utf-8')
                    print(f"Sentiment input saved to: {sentiment_input_path}")
                    
                    # Generate LLM prompts
                    prompts_path = os.path.join(output_dir, f"llm_prompts_{search_query}.csv")
                    sentiment_prep.generate_llm_prompts_csv_instagram(df_sentiment, prompts_path)
                    
                    # Run sentiment analysis with Hugging Face (FREE!)
                    print("\nAnalyzing sentiment with DeepSeek...")
                    sentiment_results_path = os.path.join(output_dir, f"sentiment_results_{search_query}.csv")
                    df_results = sentiment_analyzer.main_sentiment_analysis_instagram(
                        input_csv=sentiment_input_path,
                        output_csv=sentiment_results_path
                    )
                    
                    print(f"\n✅ Sentiment analysis complete!")
                    print(f"Results saved to: {sentiment_results_path}")
                    
                    # Calculate sentiment distribution
                    if df_results is not None and not df_results.empty:
                        total_comments_analyzed = len(df_results)
                        sentiment_counts = df_results['sentiment'].value_counts().to_dict()
                        sentiment_distribution['positive'] = sentiment_counts.get('POSITIVE', sentiment_counts.get('positive', 0))
                        sentiment_distribution['negative'] = sentiment_counts.get('NEGATIVE', sentiment_counts.get('negative', 0))
                        sentiment_distribution['neutral'] = sentiment_counts.get('NEUTRAL', sentiment_counts.get('neutral', 0))
                else:
                    print("No posts with comments found for sentiment analysis.")
                    
            except ImportError as e:
                print(f"\n⚠️ Sentiment analysis modules not available: {e}")
                print("Install required packages: pip install requests python-dotenv")
            except Exception as e:
                print(f"\n⚠️ Error during sentiment analysis: {e}")
                print("Make sure HUGGINGFACE_API_KEY is set in .env")
                print("Get your FREE API key at: https://huggingface.co/settings/tokens")

            end_sentiment_time = time.time()
            end_total_time = time.time()
            
            # --- PERFORMANCE METRICS REPORT ---
            scraping_duration = end_scraping_time - start_total_time
            text_processing_duration = end_text_processing_time - end_scraping_time
            sentiment_duration = end_sentiment_time - start_sentiment_time
            total_duration = end_total_time - start_total_time
            
            # Count total comments
            total_comments = sum(len(post.get('comments', [])) for post in posts_data)
            
            print("\n" + "="*50)
            print(f"       PERFORMANCE REPORT: {search_query.upper()}")
            print("="*50)
            print(f"Total Posts Extracted:  {len(posts_data)}")
            print(f"Total Comments:         {total_comments}")
            print(f"Comments Analyzed:      {total_comments_analyzed}")
            print("-" * 50)
            print(f"1. Scraping Phase:      {scraping_duration:.2f} seconds")
            print(f"   (Avg per post:       {scraping_duration/len(posts_data) if len(posts_data) else 0:.2f}s)")
            print(f"2. Text Processing:     {text_processing_duration:.2f} seconds")
            print(f"3. Sentiment Analysis:  {sentiment_duration:.2f} seconds (DeepSeek)")
            print(f"   (Avg per comment:    {sentiment_duration/total_comments_analyzed if total_comments_analyzed else 0:.2f}s)")
            print("-" * 50)
            print(f"TOTAL EXECUTION TIME:   {total_duration:.2f} seconds")
            print("="*50)
            
            # Generate metrics JSON for master scraper
            metrics = {
                "social_network": "Instagram",
                "llm_used": "DeepSeek",
                "query": search_query,
                "execution_times": {
                    "scraping": round(scraping_duration, 2),
                    "text_processing": round(text_processing_duration, 2),
                    "sentiment_analysis": round(sentiment_duration, 2),
                    "total": round(total_duration, 2)
                },
                "data_metrics": {
                    "posts_extracted": len(posts_data),
                    "comments_extracted": total_comments,
                    "comments_analyzed": total_comments_analyzed,
                    "total_text_items": len(posts_data) + total_comments_analyzed
                },
                "sentiment_distribution": sentiment_distribution,
                "performance_metrics": {
                    "posts_per_second": round(len(posts_data) / scraping_duration if scraping_duration > 0 else 0, 2),
                    "comments_per_second": round(total_comments_analyzed / sentiment_duration if sentiment_duration > 0 else 0, 2),
                    "avg_time_per_post": round(scraping_duration / len(posts_data) if len(posts_data) > 0 else 0, 2)
                }
            }
            
            # Save metrics JSON
            metrics_filename = os.path.join(output_dir, "metrics.json")
            with open(metrics_filename, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=4, ensure_ascii=False)
            print(f"\n📊 Metrics saved to: {metrics_filename}")
            
            # Print metrics in JSON format for master scraper to capture
            print("\n### METRICS_JSON_START ###")
            print(json.dumps(metrics, ensure_ascii=False))
            print("### METRICS_JSON_END ###")
            
        except Exception as e:
            print(f"Error during text processing: {e}")


if __name__ == "__main__":
    run()
