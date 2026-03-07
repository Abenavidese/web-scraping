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

def _is_profile_text(text):
    """Detect avatar/profile placeholder text from Instagram UI."""
    if not text:
        return False
    low = text.lower()
    return ("profile picture" in low) or ("foto del perfil" in low)

def _extract_text_from_li(li):
    """Extract user/comment from a single Instagram comment row."""
    try:
        user = li.locator("h3, a[href^='/']").first.inner_text().strip()
    except Exception:
        user = "IG User"

    try:
        raw_lines = [x.strip() for x in li.inner_text().split("\n") if x.strip()]
    except Exception:
        raw_lines = []

    cleaned = []
    for line in raw_lines:
        low = line.lower()
        if user and line == user:
            continue
        if _is_profile_text(line):
            continue
        if low in {"reply", "responder", "like", "me gusta", "follow", "seguir", "edited", "editado"}:
            continue
        if re.fullmatch(r"\d+[smhdwy]", low):
            continue
        if re.fullmatch(r"\d+\s+likes?", low):
            continue
        if re.fullmatch(r"\d+\s+me gusta", low):
            continue
        cleaned.append(line)

    return user if user else "IG User", " ".join(cleaned).strip()

def _is_timestamp_line(line):
    if not line:
        return False
    low = line.lower().strip()
    return re.fullmatch(r"\d+\s*(s|m|h|d|w|y|sem)", low) is not None

def _clean_segment_lines(lines):
    cleaned = []
    for line in lines:
        low = line.lower().strip()
        if not low:
            continue
        if _is_profile_text(line):
            continue
        if low in {
            "responder", "reply", "seguir", "follow",
            "editado", "edited", "ver traducción", "see translation",
            "más", "more", "me gusta", "like"
        }:
            continue
        if re.fullmatch(r"\d+\s+likes?", low):
            continue
        if re.fullmatch(r"\d+\s+me gusta", low):
            continue
        cleaned.append(line)
    return cleaned

def _parse_main_text(main_text, num_comments_to_scrape):
    lines = [x.strip() for x in main_text.split("\n") if x and x.strip()]
    ts_idx = [i for i, line in enumerate(lines) if _is_timestamp_line(line)]
    if not ts_idx:
        return "N/A", []

    entries = []
    for pos, idx in enumerate(ts_idx):
        next_idx = ts_idx[pos + 1] if pos + 1 < len(ts_idx) else len(lines)

        # Guess user scanning backward near timestamp.
        user = "IG User"
        for b in range(idx - 1, max(-1, idx - 6), -1):
            cand = lines[b].strip()
            low = cand.lower()
            if not cand or low in {"•", "editado", "edited", "seguir", "follow"}:
                continue
            if _is_timestamp_line(cand):
                continue
            if _is_profile_text(cand):
                continue
            user = cand
            break

        segment = lines[idx + 1:next_idx]
        segment = _clean_segment_lines(segment)
        text = " ".join(segment).strip()
        if text:
            entries.append({"user": user, "text": text})

    if not entries:
        return "N/A", []

    caption = entries[0]["text"]
    comments = entries[1:1 + num_comments_to_scrape]
    return caption, comments

def _extract_relative_datetimes(container):
    """
    Extract datetime values from relative time labels (e.g. '157 sem', '3 h').
    Order is preserved as rendered in the page.
    """
    datetimes = []
    try:
        time_nodes = container.locator("time[datetime]")
        for i in range(time_nodes.count()):
            node = time_nodes.nth(i)
            label = (node.inner_text() or "").strip()
            dt = node.get_attribute("datetime")
            if dt and _is_timestamp_line(label):
                datetimes.append(dt)
    except Exception:
        pass
    return datetimes

def extract_post_payload(page, num_comments_to_scrape):
    """
    Extract a post's image/caption/comments from the post article.
    Avoids grabbing profile-avatar text as caption.
    """
    image_url = "N/A"
    caption_text = "N/A"
    comments_list = []
    post_timestamp = None

    container = None
    try:
        page.wait_for_selector("main", timeout=8000)
        container = page.locator("main").first
    except Exception:
        pass

    # Prefer non-avatar post image/caption from current layout.
    try:
        imgs = page.locator("main img")
        if imgs.count() == 0:
            imgs = page.locator("img")
        img_count = imgs.count()
        fallback_src = "N/A"
        fallback_alt = "N/A"
        for i in range(min(img_count, 12)):
            img = imgs.nth(i)
            src = img.get_attribute("src")
            alt = img.get_attribute("alt")
            if src and fallback_src == "N/A":
                fallback_src = src
                fallback_alt = alt if alt else "N/A"
            if not src:
                continue
            if alt and "photo by" not in alt.lower() and _is_profile_text(alt):
                continue
            if alt and _is_profile_text(alt):
                continue
            image_url = src
            caption_text = alt if alt else "N/A"
            break

        if image_url == "N/A":
            image_url = fallback_src
            caption_text = fallback_alt
    except Exception:
        pass

    try:
        if container is not None and container.count() > 0:
            main_text = container.inner_text()
            parsed_caption, parsed_comments = _parse_main_text(main_text, num_comments_to_scrape)
            if parsed_caption and parsed_caption != "N/A" and not _is_profile_text(parsed_caption):
                caption_text = parsed_caption
            comments_list = parsed_comments

            # Map rendered relative-time timestamps:
            # first timestamp is usually caption/post, next ones are comments.
            dt_values = _extract_relative_datetimes(container)
            if dt_values:
                post_timestamp = dt_values[0]
                for idx, comment in enumerate(comments_list):
                    if idx + 1 < len(dt_values):
                        comment["timestamp"] = dt_values[idx + 1]
    except Exception:
        pass

    # Final safety for caption.
    if _is_profile_text(caption_text):
        caption_text = "N/A"

    return image_url, caption_text, comments_list, post_timestamp

def run(search_query=None, num_posts=None, num_comments=None):
    import time
    start_total_time = time.time()
    
    # Argumentos compatibles con master_scraper.py
    parser = argparse.ArgumentParser(description="Instagram Scraper - Extracción de Posts y Comentarios")
    parser.add_argument("--query", type=str, default="python", help="Término de búsqueda")
    parser.add_argument("--posts", type=int, default=5, help="Número de posts a extraer")
    parser.add_argument("--comments", type=int, default=5, help="Número de comentarios por post")
    parser.add_argument("--year", type=int, default=None, help="Año para el filtro (proxy estático en IG)")
    parser.add_argument("--month", type=int, default=None, help="Mes para el filtro (proxy estático en IG)")
    
    args = parser.parse_args()
    
    search_query = args.query
    num_posts_to_scrape = args.posts
    num_comments_to_scrape = args.comments
    
    print(f"Search topic: {search_query}")
    if args.year and args.month:
        print(f"Date applied (Proxy for DB normalization): {args.year}-{args.month:02d}")
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
        # Custom Search Strategy based on Exact Dates (Google Dorks)
        unique_links = set()
        
        if args.year and args.month:
            print(f"Applying strict Date Filter via Google Dorks ({args.year}-{args.month:02d})...")
            # Google Search Dork for Instagram
            dork_query = f"site:instagram.com/p/ \"{search_query}\""
            import urllib.parse
            import calendar
            
            # Get last day of month
            _, last_day = calendar.monthrange(args.year, args.month)
            
            # Format: mm/dd/yyyy
            min_date = f"{args.month}/1/{args.year}"
            max_date = f"{args.month}/{last_day}/{args.year}"
            
            # tbs=cdr:1,cd_min:3/1/2023,cd_max:3/31/2023
            tbs_param = f"cdr:1,cd_min:{min_date},cd_max:{max_date}"
            
            google_url = f"https://www.google.com/search?q={urllib.parse.quote(dork_query)}&tbs={urllib.parse.quote(tbs_param)}"
            print(f"Executing Dork: {google_url}")
            
            page.goto(google_url)
            smart_sleep(2, 4, probability=1.0)
            
            print("\n⚠️  [INTERVENCIÓN REQUERIDA] \nEs muy probable que Google haya lanzado un CAPTCHA.")
            print("1. Revisa la ventana del navegador (Microsoft Edge).")
            print("2. Resuelve el Captcha si existe.")
            input("3. Presiona [ENTER] aquí en la consola CUANDO HAYAS TERMINADO y la página de resultados sea visible...")
            
            # Extract links from Google Search results
            page_idx = 0
            while len(unique_links) < num_posts_to_scrape and page_idx < 5: # Max 5 pages
                # Wait for Google results to render
                try:
                    page.wait_for_selector("div#search a", timeout=5000)
                except:
                    print("Could not find standard Google search results. Check CAPTCHA or blocking.")
                    break
                    
                links = page.locator("div#search a[href*='instagram.com/p/']")
                for i in range(links.count()):
                    href = links.nth(i).get_attribute('href')
                    if href and 'instagram.com/p/' in href and not 'google.com' in href.lower() and href.startswith('http'):
                        # Clean tracking parameters
                        clean_url = href.split('?')[0]
                        unique_links.add(clean_url)
                        if len(unique_links) >= num_posts_to_scrape:
                            break
                
                if len(unique_links) < num_posts_to_scrape:
                    # Try to go to next page
                    try:
                        next_btn = page.locator("a#pnnext")
                        if next_btn.count() > 0:
                            next_btn.click()
                            smart_sleep(2, 4, probability=1.0)
                            page_idx += 1
                        else:
                            break
                    except:
                        break
            
            print(f"Google Dorking found {len(unique_links)} strict dated links.")
            
        else:
            # Traditional Search functionality without exact dates
            print(f"Searching for '{search_query}' (No exact date specified)...")
            formatted_query = format_hashtag(search_query)
            print(f"Formatted hashtag: #{formatted_query}")
            
            tag_url = f"https://www.instagram.com/explore/tags/{formatted_query}/"
            print(f"Direct navigation to: {tag_url}")
            page.goto(tag_url)
            smart_sleep(2, 4, probability=1.0)  
            
            if "login" in page.url:
                print("Redirected to login page. Session might be invalid or expired.")
                return

        # Extract data
        posts_data = []
        count = 0
        processed_indices = set()
        
        # FIX: Define scroll variables universally so Branch 1 doesn't crash Branch 2 logic later
        max_scroll_attempts = 30
        scroll_attempt = 0
        no_new_posts_count = 0
        
        print(f"Target: {num_posts_to_scrape} posts")
        
        # Branch 1: We already have precise links (From Google)
        if args.year and args.month:
            for url in list(unique_links)[:num_posts_to_scrape]:
                try:
                    print(f"Processing dated post {count + 1}/{len(unique_links)}: {url}")
                    page.goto(url)
                    smart_sleep(2, 3, probability=1.0)
                    print("  Extracting comments via article selectors...")
                    image_url, caption_alt, comments_list, post_timestamp = extract_post_payload(page, num_comments_to_scrape)
                        
                    posts_data.append({
                        "post_url": url,
                        "caption_snippet": caption_alt[:100] + "..." if caption_alt and len(caption_alt) > 100 else caption_alt,
                        "image_url": image_url,
                        "post_timestamp": post_timestamp,
                        "comments": comments_list
                    })
                    count += 1
                    
                except Exception as e:
                    print(f"  Error processing isolated post: {e}")
                    continue
                    
        # Branch 2: We must dynamically scroll inside Instagram standard search modal
        else:
            max_scroll_attempts = 30  # Prevent infinite scrolling
            
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
                        print("  Extracting comments via article selectors...")
                        image_url, caption_alt, comments_list, post_timestamp = extract_post_payload(page, num_comments_to_scrape)
                        
                        posts_data.append({
                            "post_url": full_url,
                            "caption_snippet": caption_alt[:100] + "..." if caption_alt and len(caption_alt) > 100 else caption_alt,
                            "image_url": image_url,
                            "post_timestamp": post_timestamp,
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
        
        # Save raw extraction to file in Resultados folder
        filename = os.path.join(output_dir, f"results_{search_query}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        browser.close()
        end_scraping_time = time.time()
        
        # --- UNIVERSAL NLP PIPELINE (Phases 2-4) ---
        try:
            print("\n--- Starting Phase 2 ETL Processing ---")
            import uuid
            import pandas as pd
            import datetime
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            from shared.data_cleaner import ETLProcessor
            from x_scrapper.sentiment_prep import prepare_sentiment_data_with_processed
            
            # Flatten data for ETL
            flattened_data = []
            for p in posts_data:
                post_url = p.get('post_url', '')
                post_id = post_url.split('/')[-1] if post_url and post_url != "N/A" else str(uuid.uuid4())[:8]
                
                # Use proxy month/year for Instagram dates
                ig_year = args.year if args.year else datetime.datetime.now().year
                ig_month = args.month if args.month else datetime.datetime.now().month
                ig_ts = f"{ig_year}-{ig_month:02d}-15T12:00:00.000Z"
                post_ts = p.get('post_timestamp') or ig_ts
                
                # Post
                flattened_data.append({
                    "type": "post",
                    "author": "IG User",
                    "text": p.get('caption_snippet', ''),
                    "parent_url": post_url,
                    "timestamp": post_ts,
                    "item_id": post_id
                })
                
                # Comments
                for c in p.get('comments', []):
                    comment_id = str(uuid.uuid4())[:10]
                    flattened_data.append({
                        "type": "comment",
                        "author": c.get('user', 'IG User'),
                        "text": c.get('text', ''),
                        "parent_url": post_url,
                        "timestamp": c.get('timestamp', post_ts),
                        "item_id": comment_id
                    })
                    
            df_raw = pd.DataFrame(flattened_data)
            
            etl = ETLProcessor()
            topic_kws = [search_query] if search_query else []
            df_processed = etl.run_etl_pipeline(df_raw, platform='instagram', run_id=f"run_ig_{int(time.time())}", topic_keywords=topic_kws)
            
            # Filter noise
            if 'is_noise' in df_processed.columns:
                initial_count = len(df_processed)
                df_processed = df_processed[~df_processed['is_noise']].copy()
                removed = initial_count - len(df_processed)
                if removed > 0:
                    print(f"🧹 Noise Filter: Removed {removed} noisy comments")
                    
            if df_processed.empty:
                print("⚠️ No valid data left after noise filtering. Aborting sentiment analysis.")
                return
                    
            # Save Parquet Phase 2
            staged_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'staged', 'instagram')
            os.makedirs(staged_dir, exist_ok=True)
            try:
                yr = args.year if args.year else df_processed['year'].mode().iloc[0] if 'year' in df_processed.columns and not df_processed['year'].isna().all() else datetime.datetime.now().year
                mo = args.month if args.month else df_processed['month'].mode().iloc[0] if 'month' in df_processed.columns and not df_processed['month'].isna().all() else datetime.datetime.now().month
                staged_parquet = os.path.join(staged_dir, f"{int(yr)}-{int(mo):02d}.parquet")
                df_processed.to_parquet(staged_parquet, index=False)
                print(f"✅ Staged Parquet saved to {staged_parquet}")
            except Exception as e:
                pass

            df_sentiment = prepare_sentiment_data_with_processed(df_processed)
            df_sentiment.to_csv(os.path.join(output_dir, "sentiment_input.csv"), index=False, encoding='utf-8')
            end_processing_time = time.time()
            
            # --- DeepSeek Sentiment Analysis (Phases 3 & 4) ---
            start_sentiment_time = time.time()
            sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0, "mixed": 0}
            total_items_analyzed = 0
            
            print("\n" + "="*60)
            print("Starting Automatic Sentiment Analysis with DeepSeek (Phases 3 & 4)...")
            print("="*60)
            
            from shared.sentiment_analyzer import DeepSeekSentimentAnalyzer
            analyzer = DeepSeekSentimentAnalyzer()
            
            # Harmonize (Phase 3)
            df_harmonized = analyzer.harmonize_dataset(df_sentiment, platform="instagram", target_per_month=1000)
            
            # Robust Process (Phase 4)
            df_results = analyzer.process_dataset_robustly(
                df_harmonized,
                platform="instagram",
                text_col='post_text',
                comments_col='comments_json'
            )
            
            results_csv_path = os.path.join(output_dir, "sentiment_results.csv")
            df_results.to_csv(results_csv_path, index=False, encoding='utf-8')
            
            total_items_analyzed = len(df_results)
            if 'sentiment' in df_results.columns:
                counts = df_results['sentiment'].value_counts().to_dict()
                for k, v in counts.items():
                    key = str(k).lower()
                    if key in sentiment_distribution:
                        sentiment_distribution[key] = int(v)
            
            # Formato Investigación final
            from shared.unified_csv_exporter import convert_instagram_to_unified
            unified_csv_path = os.path.join(output_dir, "formato_investigacion.csv")
            convert_instagram_to_unified(results_csv_path, unified_csv_path)
            
            end_sentiment_time = time.time()
            end_total_time = time.time()
            
            # --- PERFORMANCE METRICS REPORT ---
            scraping_duration = end_scraping_time - start_total_time
            text_processing_duration = end_processing_time - end_scraping_time
            sentiment_duration = end_sentiment_time - start_sentiment_time
            total_duration = end_total_time - start_total_time
            
            total_comments = sum(len(post.get('comments', [])) for post in posts_data)
            
            print("\n" + "="*50)
            print(f"       PERFORMANCE REPORT: {search_query.upper()}")
            print("="*50)
            print(f"Total Posts Extracted:  {len(posts_data)}")
            print(f"Total Comments:         {total_comments}")
            print(f"Items Analyzed:         {total_items_analyzed}")
            print("-" * 50)
            print(f"1. Scraping Phase:      {scraping_duration:.2f} seconds")
            print(f"2. Phase 2 ETL:         {text_processing_duration:.2f} seconds")
            print(f"3. DeepSeek ML (P3-4):  {sentiment_duration:.2f} seconds")
            print("-" * 50)
            print(f"TOTAL EXECUTION TIME:   {total_duration:.2f} seconds")
            print("="*50)
            
            metrics = {
                "social_network": "Instagram",
                "llm_used": "DeepSeek (Unified)",
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
                    "items_analyzed": total_items_analyzed,
                },
                "sentiment_distribution": sentiment_distribution,
                "performance_metrics": {
                    "posts_per_second": round(len(posts_data) / scraping_duration if scraping_duration > 0 else 0, 2),
                    "comments_per_second": round(total_items_analyzed / sentiment_duration if sentiment_duration > 0 else 0, 2),
                    "avg_time_per_post": round(scraping_duration / len(posts_data) if len(posts_data) > 0 else 0, 2)
                }
            }
            
            metrics_filename = os.path.join(output_dir, "metrics.json")
            with open(metrics_filename, "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=4, ensure_ascii=False)
                
            print("\n### METRICS_JSON_START ###")
            print(json.dumps(metrics, ensure_ascii=False))
            print("### METRICS_JSON_END ###")
        except Exception as e:
            print(f"Error during execution pipeline: {e}")
            import traceback
            traceback.print_exc()

    return

if __name__ == "__main__":
    run()
