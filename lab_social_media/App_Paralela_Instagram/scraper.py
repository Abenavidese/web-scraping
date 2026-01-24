import os
import sys
import argparse
import random
import time
import json
from playwright.sync_api import sync_playwright

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

    # Create output directory
    output_dir = "Resultados"
    os.makedirs(output_dir, exist_ok=True)
    
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

        # Extract data
        # We'll try to get the first few posts
        posts_data = []
        
        # Select post elements - finding links that look like /p/
        # This selector targets anchors with href starting with /p/ which are posts
        print("Extracting posts...")
        post_links = page.locator('a[href^="/p/"]').all()
        
        # Process posts based on user input
        count = 0
        unique_links = set()
        
        # Locators are lazy, so we can iterate by index
        thumbnails = page.locator('a[href^="/p/"]')
        count_found = thumbnails.count()
        print(f"Detected {count_found} potential posts. We will process up to {num_posts_to_scrape}.")
        
        for i in range(min(num_posts_to_scrape, count_found)):
            if count >= num_posts_to_scrape:
                break
                
            print(f"Processing post {i+1}...")
            
            # Re-locate to avoid stale element errors
            thumbnail = thumbnails.nth(i)
            
            # Scroll into view if needed
            thumbnail.scroll_into_view_if_needed()
            smart_sleep(1, 2, probability=0.6)  # Sometimes wait before clicking
            
            # Get URL for reference
            post_url_suffix = thumbnail.get_attribute("href")
            full_url = f"https://www.instagram.com{post_url_suffix}"
            
            # Click to open modal
            thumbnail.click()
            
            # Wait for modal to appear.
            # Usually looking for an <article> inside a dialog or purely the URL change
            smart_sleep(2, 4, probability=1.0)  # Always wait for modal
            
            # Extract Data from Modal
            # 1. Image
            try:
                # Inside modal, the image is usually the first main img or inside a specific container
                # We try to find the image inside the dialogue
                modal_img = page.locator('article img').nth(0) # First image in article
                image_url = modal_img.get_attribute("src")
                caption_alt = modal_img.get_attribute("alt")
            except:
                image_url = "N/A"
                caption_alt = "N/A"

            # 2. Comments
            print("  Extracting comments...")
            comments_list = []
            try:
                # Wait for comments to load
                page.wait_for_selector('article ul', timeout=5000) 
                
                # Select all list items in the article (assumes right side is <ul>)
                comment_elements = page.locator('article ul li')
                
                # We take a few comments based on user input
                c_count = 0
                for j in range(comment_elements.count()):
                    if c_count >= num_comments_to_scrape: 
                        break
                    
                    # Get text
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
            
            # Close modal to go back to explore/grid
            # Find close button (SVG path usually X) or press Escape
            print("  Closing modal...")
            page.keyboard.press("Escape")
            smart_sleep(1.5, 3, probability=0.8)  # Usually wait after closing
            
            count += 1
            
        print(f"Found {len(posts_data)} posts.")
        
        # Save to file in Resultados folder
        filename = os.path.join(output_dir, f"results_{search_query}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        
        browser.close()
        
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
            
            # --- Sentiment Analysis Integration ---
            try:
                print("\n--- Starting Sentiment Analysis (Hugging Face - FREE) ---")
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
                    print("\nAnalyzing sentiment with Hugging Face (100% FREE)...")
                    sentiment_results_path = os.path.join(output_dir, f"sentiment_results_{search_query}.csv")
                    df_results = sentiment_analyzer.main_sentiment_analysis_instagram(
                        input_csv=sentiment_input_path,
                        output_csv=sentiment_results_path
                    )
                    
                    print(f"\n✅ Sentiment analysis complete!")
                    print(f"Results saved to: {sentiment_results_path}")
                else:
                    print("No posts with comments found for sentiment analysis.")
                    
            except ImportError as e:
                print(f"\n⚠️ Sentiment analysis modules not available: {e}")
                print("Install required packages: pip install requests python-dotenv")
            except Exception as e:
                print(f"\n⚠️ Error during sentiment analysis: {e}")
                print("Make sure HUGGINGFACE_API_KEY is set in .env")
                print("Get your FREE API key at: https://huggingface.co/settings/tokens")

            
        except Exception as e:
            print(f"Error during text processing: {e}")


if __name__ == "__main__":
    run()
