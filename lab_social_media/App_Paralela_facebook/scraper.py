import os
import json
import time
import random
import re
from playwright.sync_api import sync_playwright
from ollama_sentiment import classify_comments_sentiment
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def slugify(text):
    """Convert text to slug format for directory names"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')

def sleep_largo():
    time.sleep(1.4)

def sleep_corto():
    time.sleep(0.5)

def clean_comment_text(raw_text):
    if not raw_text: return ""
    lines = raw_text.split('\n')
    cleaned_lines = []
    
    # Regex for timestamps (e.g., "16 h", "2 d", "1 min", "3 sem")
    # And UI junk
    skip_patterns = [
        r"^\d+\s?[hmds]$",       # 1 h, 2d, 5m
        r"^\d+\s?sem$",          # 3 sem
        r"^\d+\s?min$", 
        r"^(Me gusta|Responder|Compartir|Like|Reply|Share|Follow|Seguir)$",
        r"^(Ver más|See more|Ver traducción|See translation)$",
        r"^(Editado|Edited|Autor|Author|Fans destacados|Top fan)$"
    ]
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        # Check against patterns
        is_junk = False
        for pat in skip_patterns:
            if re.search(pat, line, re.IGNORECASE):
                is_junk = True
                break
        
        if not is_junk:
            cleaned_lines.append(line)
            
    return " ".join(cleaned_lines)

def load_env_file(env_path):
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())

def run():
    import time
    import argparse
    start_total_time = time.time()
    
    # ARGUMENT PARSING
    parser = argparse.ArgumentParser(description="Facebook Scraper")
    parser.add_argument("--query", type=str, default=None, help="Search topic")
    parser.add_argument("--posts", type=int, default=None, help="Number of posts to scrape")
    parser.add_argument("--comments", type=int, default=None, help="Number of comments per post")
    
    args = parser.parse_args()
    
    # Use command-line arguments with default values
    search_query = args.query if args.query else "Inteligencia Artificial"
    num_posts_to_scrape = args.posts if args.posts is not None else 5
    num_comments_to_scrape = args.comments if args.comments is not None else 5
    
    print(f"Search topic: {search_query}")
    print(f"Number of posts: {num_posts_to_scrape}")
    print(f"Comments per post: {num_comments_to_scrape}")

    # User system configuration
    user_id = os.getenv("USER_ID", "default")
    query_slug = slugify(search_query)
    
    # Create output directory with user system structure
    output_dir = os.path.join("..", "users", user_id, "facebook", query_slug)
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nUser ID: {user_id}")
    print(f"Output directory: {output_dir}")
    
    load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
    gemini_api_key = None
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False, slow_mo=100, channel="msedge")
        
        # Load session
        try:
            context = browser.new_context(storage_state="auth_fb.json")

        except FileNotFoundError:
            print("Session file 'auth_fb.json' not found. Starting automatic login...")
            try:
                # Run login script as a separate process to avoid Playwright Sync loop conflicts
                import subprocess
                import sys
                print("Lanzando script de login automático...")
                subprocess.check_call([sys.executable, "login_auto.py"])
                
                # Check if it worked
                if os.path.exists("auth_fb.json"):
                     context = browser.new_context(storage_state="auth_fb.json")
                else:
                     print("Login abortado o falló. Intentando continuar sin sesión guardada...")
                     context = browser.new_context()
            except Exception as e:
                print(f"Auto-login failed: {e}")
                browser.close()
                return

        page = context.new_page()
        
        print("Navigating to Facebook...")
        try:
            page.goto("https://www.facebook.com/")
        except Exception as e:
            print(f"Navigation error: {e}")
            print("Retrying navigation...")
            sleep_largo()
            page.goto("https://www.facebook.com/")

        sleep_largo()

        # Search
        print(f"Searching for '{search_query}'...")
        # Direct navigation to search results for posts
        # URL format: https://www.facebook.com/search/posts/?q=query
        search_url = f"https://www.facebook.com/search/posts/?q={search_query}"
        page.goto(search_url)
        sleep_largo()
        
        # Check login
        if "login" in page.url and "search" not in page.url:
             print("Redirected to login. Session might be invalid.")
             return

        # Scroll to load posts
        # We fetch extra posts (1.5x) because some might not have comments or be duplicates
        target_buffer = int(num_posts_to_scrape * 1.5)
        print(f"Scrolling to load posts (Target candidate pool: {target_buffer} for {num_posts_to_scrape} valid posts)...")
        # Robust multi-selector for counting posts
        post_selectors = 'div[role="article"], .x1yztbdb, [data-pagelet^="FeedUnit"], [data-ad-comet-preview="message"]'
        
        # Increased scroll attempts and "wiggle" logic for stuck feeds
        max_scroll_attempts = 30 + int(num_posts_to_scrape / 2)
        stagnant_count = 0
        last_count = 0
        
        for s in range(max_scroll_attempts):
            current_found = page.locator(post_selectors).count()
            
            print(f"  Scroll {s+1}/{max_scroll_attempts}: Approx. {current_found} posts found...")
            if current_found >= target_buffer:
                break
            
            # Smart Scroll: Wiggle if stuck
            if current_found == last_count:
                stagnant_count += 1
                if stagnant_count >= 2:
                    print("    Feed stuck, trying to wiggle (Up/Down)...")
                    page.mouse.wheel(0, -500) # Up a bit
                    sleep_corto()
                    page.mouse.wheel(0, 4000) # Down hard
                    sleep_largo()
                else:
                    page.mouse.wheel(0, 3000)
                    sleep_largo()
            else:
                stagnant_count = 0
                page.mouse.wheel(0, 3000)
                sleep_largo()
            
            # Give up only after significant stagnation
            if stagnant_count > 6:
                print("  Stopping: Feed seems genuinely finished or blocked.")
                break
                
            last_count = current_found



        # Extract Posts
        print("Extracting posts...")
        start_scraping_time = time.time()
        posts_data = []
        
        # Selectors for Facebook posts on the search page
        articles = page.locator(post_selectors).all()
        
        if len(articles) == 0:
             print("\nError: 0 posts found. Your session might be invalid or expired.")
             print("Try deleting 'auth_fb.json' to force a new login.\n")
             # Print debug
             body_text = page.inner_text("body")[:200].replace("\n", " ")
             print(f"  Page preview: {body_text}")
             
        print(f"Processing up to {num_posts_to_scrape} items from {len(articles)} found elements...")

        
        count = 0
        seen_captions = set()
        for i, article in enumerate(articles):
            if count >= num_posts_to_scrape:
                break
                
            try:
                # Scroll article into view
                article.scroll_into_view_if_needed()
                sleep_largo()
                
                # Check for duplicates (Robust Version)
                try:
                    # We check looking for meaningful text
                    preview_text = article.inner_text().strip()
                    
                    # Remove common noise BEFORE checking duplicates
                    # This prevents "Facebook Facebook" headers from looking like duplicates
                    noise_marker = "Facebook"
                    if noise_marker in preview_text:
                        preview_text = preview_text.replace(noise_marker, "").strip()

                    if len(preview_text) > 20: 
                         # Normalize whitespace
                         preview_snippet = " ".join(preview_text.split())[:100]
                         if preview_snippet in seen_captions:
                             print(f"    Skipping duplicate post snippet: {preview_snippet[:30]}...")
                             continue
                         seen_captions.add(preview_snippet)
                except:
                    pass

                # Expand "See more" text if present - TRY HARDER
                try:
                    # Selectors specific to the "See more" text button often used in feeds
                    see_more = article.locator('div[role="button"]:has-text("Ver más"), div[role="button"]:has-text("See more")').first
                    if see_more.is_visible():
                        # Force click via JS to avoid overlay issues
                        see_more.dispatch_event("click") 
                        sleep_corto()
                except:
                    pass

                # Text content extraction
                # Try to find the specific content div first for cleaner text
                content_loc = article.locator('[data-ad-comet-preview="message"], [data-ad-preview="message"], div[dir="auto"]')
                if content_loc.count() > 0:
                     # Take the one with the most text
                     all_texts = [loc.inner_text() for loc in content_loc.all() if len(loc.inner_text()) > 5]
                     text_content = max(all_texts, key=len) if all_texts else article.inner_text()
                else:
                     text_content = article.inner_text()
                
                # URL extraction
                all_links = article.locator('a').all()
                full_url = "N/A"
                is_video_post = False
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and ("/posts/" in href or "/permalink.php" in href or "/groups/" in href or "story_fbid" in href):
                        if href.startswith("/"):
                             href = "https://www.facebook.com" + href
                        # Avoid main group URLs, look for post-specific ones
                        if "/posts/" in href or "fbid=" in href or "permalink" in href:
                             full_url = href.split("?")[0] if "?" in href and "fbid" not in href else href
                             break
                    if href and ("/watch/" in href or "/videos/" in href or "video.php" in href or "reel" in href):
                        is_video_post = True

                if article.locator("video").count() > 0:
                    is_video_post = True
                
                # Image extraction
                images = article.locator('img').all() 
                img_url = "N/A"
                for img in images:
                    src = img.get_attribute("src")
                    # Ignore small icons/emojis
                    width = img.get_attribute("width")
                    if width and int(width) < 50:
                         continue
                    if src and ("scontent" in src or "fbcdn" in src) and "/emoji.php" not in src:
                        img_url = src
                        break
                        
                # Extract Comments
                print(f"  [{i+1}] Attempting to open comments (Target: {num_comments_to_scrape})...")
                comments_list = []
                try:
                    if is_video_post:
                        print("    Video/reel post detected. Trying to extract comments anyway.")

                    # Look for comment button by common labels or roles
                    # Facebook often uses aria-label="Comment" or "Escribe un comentario"
                    comment_btn = None
                    button_selectors = [
                        'div[aria-label="Comentar"]',
                        'div[aria-label="Comment"]',
                        'div[role="button"]:has-text("Comentar")',
                        'div[role="button"]:has-text("Comment")',
                        'div[role="button"]:has-text("Comentarios")',
                        'div[role="button"]:has-text("Comments")',
                        'div[aria-label*="Leave a comment"]',
                        'div[aria-label*="Escribe un comentario"]',
                        # Video/Reel specific
                        'div[data-icon="comment"]',
                        'i[data-visualcompletion="css-img"]'
                    ]
                    
                    found_btn = False
                    for sel in button_selectors:
                        # try to find within the article first
                        btns = article.locator(sel).all()
                        for btn in btns:
                            if btn.is_visible():
                                href = btn.get_attribute("href")
                                if href and ("/watch/" in href or "/videos/" in href or "video.php" in href or "reel" in href):
                                    continue
                                comment_btn = btn
                                found_btn = True
                                break
                        if found_btn: break

                    if not found_btn:
                        # Fallback: broader search for comment controls inside the post
                        fallback_btns = article.locator('div[role="button"]').filter(
                            has_text=re.compile(r"(comentarios|comments)", re.IGNORECASE)
                        ).all()
                        for btn in fallback_btns:
                            if btn.is_visible():
                                href = btn.get_attribute("href")
                                if href and ("/watch/" in href or "/videos/" in href or "video.php" in href or "reel" in href):
                                    continue
                                comment_btn = btn
                                found_btn = True
                                break
                    
                    if comment_btn:
                        # Javascript click is sometimes more reliable for these react buttons that might be covered
                        # comment_btn.click() 
                        comment_btn.dispatch_event("click")
                        sleep_largo() 
                        
                        # Detect if a dialog opened (common for Facebook photo/video posts)
                        dialog = page.locator('div[role="dialog"]').last
                        
                        comment_scope = article # Default to measuring inside the article
                        if dialog.is_visible():
                            print("    Comments opened in a dialog/modal.")
                            comment_scope = dialog
                        else:
                            print("    Comments likely expanded inline.")

                        # --- TRY TO SWITCH TO ALL COMMENTS ---
                        try:
                            # Look for the dropdown trigger
                            sort_menu = comment_scope.locator('div[role="button"]:has-text("Más relevantes"), div[role="button"]:has-text("Most relevant")').first
                            if sort_menu.is_visible():
                                sort_menu.click()
                                sleep_corto()
                                # Click "All comments"
                                all_comments_opt = page.locator('div[role="menuitem"]:has-text("Todos los comentarios"), div[role="menuitem"]:has-text("All comments")').first
                                if all_comments_opt.is_visible():
                                    all_comments_opt.dispatch_event("click")
                                    print("    Switched to 'All comments' filter.")
                                    sleep_largo()
                        except:
                            pass

                        # Loop to load more comments if needed
                        for _ in range(5): # Reduce loops to speed up
                            current_comments_count = comment_scope.locator('div[role="article"]').count()
                            if current_comments_count >= num_comments_to_scrape:
                                break
                                
                            # Scroll logic: standard PageDown is often best for lazy loaders
                            try:
                                if dialog.is_visible():
                                    dialog.click() # Focus
                                    page.keyboard.press("End") # Go to bottom
                                    sleep_corto()
                                    page.keyboard.press("PageUp") # Wiggle a bit
                                else:
                                    page.keyboard.press("PageDown")
                            except:
                                pass
                                
                            # Try clicking "View more comments" - Broad text matching
                            try:
                                # Match "View previous comments", "View more comments", "Ver más comentarios", "Ver 50 comentarios más"
                                more_btns = comment_scope.locator('span').filter(has_text=re.compile(r"(ver|view).+(comentarios|comments)", re.IGNORECASE)).all()
                                clicked_any = False
                                for b in more_btns:
                                    if b.is_visible():
                                        # Only click if it looks like a button/link (pointer)
                                        # casting the net wide
                                        b.scroll_into_view_if_needed()
                                        b.dispatch_event("click")
                                        clicked_any = True
                                        sleep_largo() # Weight for load
                                        break # Click one at a time to avoid errors
                                
                                if not clicked_any:
                                     # Sometimes it's a div role=button
                                     more_divs = comment_scope.locator('div[role="button"]').filter(has_text=re.compile(r"(ver|view).+(comentarios|comments)", re.IGNORECASE)).all()
                                     for b in more_divs:
                                         if b.is_visible():
                                             b.scroll_into_view_if_needed()
                                             b.dispatch_event("click")
                                             sleep_largo()
                                             break
                                             
                                # Expand individual long comments ("See more" / "Ver más" inline)
                                inline_see_more = comment_scope.locator('div[role="button"]:has-text("Ver más"), div[role="button"]:has-text("See more")').all()
                                for btn in inline_see_more:
                                    if btn.is_visible():
                                         btn.dispatch_event("click")
                                         sleep_corto()

                            except:
                                pass
                            
                            sleep_corto()


                        # Comment text container detection
                        # We look for the main comment body. 
                        # Strategy: Find all 'article' roles (which usually represent a comment) 
                        # OR find generic divs with dir="auto" that are long enough.
                        
                        extracted_c = 0
                        
                        # Method 1: Semantic Roles (Best for reliability)
                        # Comments are often rol="article"
                        possible_comments = comment_scope.locator('div[role="article"]').all()
                        
                        # Filter out the main post if it was accidentally caught (unlikely in dialog, possible in inline)
                        
                        if len(possible_comments) > 0:
                            for c in possible_comments:
                                if extracted_c >= num_comments_to_scrape: break
                                # The text is usually in a div[dir="auto"] inside the article
                                text_div = c.locator('div[dir="auto"]').first
                                if text_div.count() > 0:
                                    c_text = text_div.inner_text().strip()
                                else:
                                    c_text = c.inner_text().strip()
                                    
                                    
                                # Clean up common button text that gets grabbed
                                c_text = clean_comment_text(c_text)
                                
                                if len(c_text) > 2:
                                     comments_list.append({"user": "FB User", "text": c_text})
                                     extracted_c += 1
                        
                        # Method 2: Fallback if Method 1 gave nothing (e.g. they aren't marked as articles)
                        if extracted_c == 0:
                             print("    Fallback semantic search for comments...")
                             # This selector targets the comment bubble text style often used
                             fallback_els = comment_scope.locator('div[dir="auto"]').all()
                             for el in fallback_els:
                                 if extracted_c >= num_comments_to_scrape: break
                                 c_text = el.inner_text().strip()
                                 c_text = clean_comment_text(c_text)
                                 # specific filtering for fallback
                                 if len(c_text) > 3 and c_text != post_text:
                                     comments_list.append({"user": "FB User", "text": c_text})
                                     extracted_c += 1

                        # Close dialog if it was open
                        if dialog.is_visible():
                            # multiple ways to close: escape, or click close button
                            page.keyboard.press("Escape")
                            sleep_corto()
                            
                    else:
                        print("    No comment button found (or comments disabled).")

                except Exception as ce:
                    print(f"    Notice: Comment section skip ({ce})")

                # Final caption cleanup
                lines = text_content.split('\n')
                # Explicitly exclude platform noise
                noise = ["Facebook", "Like", "Comment", "Share", "Me gusta", "Comentar", "Compartir", "Ver más", "See more", "Suggested for you"]
                clean_lines = [l.strip() for l in lines if len(l.strip()) > 5 and not any(n.lower() == l.strip().lower() for n in noise)]
                
                post_text = " ".join(clean_lines[:3]) 
                
                if not comments_list:
                    continue

                if comments_list:
                    # Sentiment decoupled - will be processed after browser close
                    pass

                posts_data.append({
                    "post_url": full_url,
                    "caption_snippet": post_text[:200] if post_text else "No text found",
                    "image_url": img_url,
                    "comments": comments_list,
                })
                count += 1
                
            except Exception as e:
                print(f"  Skipping post due to error: {e}")
                continue

        print(f"Extracted {len(posts_data)} posts.")
        end_scraping_time = time.time()
        
        # Save JSON to Resultados folder
        filename = os.path.join(output_dir, f"results_facebook_{search_query}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        
        browser.close()
        
        # --- Post-Processing Sentiment Analysis ---
        print("\n--- Starting Post-Processing Sentiment Analysis (Decoupled) ---")
        start_sentiment_time = time.time()
        
        # First, analyze post captions
        if posts_data:
            print(f"\nAnalyzing sentiments for {len(posts_data)} post captions...")
            post_captions = [post.get("caption_snippet", "") for post in posts_data]
            try:
                post_sentiment_results = classify_comments_sentiment(post_captions, None, batch_size=15)
                for i, post in enumerate(posts_data):
                    if i < len(post_sentiment_results):
                        result = post_sentiment_results[i]
                        if isinstance(result, dict):
                            post["sentiment"] = result.get("sentiment", "NEUTRAL")
                            post["sentiment_reasoning"] = result.get("reasoning", "Sin explicación")
                        else:
                            post["sentiment"] = result
                            post["sentiment_reasoning"] = "Sin explicación disponible"
                    else:
                        post["sentiment"] = "NEUTRAL"
                        post["sentiment_reasoning"] = "No analizado"
                print("✅ Post sentiment analysis complete.")
            except Exception as e:
                print(f"Error during post sentiment analysis: {e}")
                # If analysis fails, set defaults
                for post in posts_data:
                    post["sentiment"] = "NEUTRAL"
                    post["sentiment_reasoning"] = "Error en análisis"
        
        # Then analyze comments
        all_comments_texts = []
        for post in posts_data:
            for comment in post.get("comments", []):
                all_comments_texts.append(comment.get("text", ""))
        
        if all_comments_texts:
            print(f"Classifying {len(all_comments_texts)} comments with Ollama (with explainability)...")
            try:
                # classify_comments_sentiment ahora retorna lista de dicts con 'sentiment' y 'reasoning'
                sentiment_results = classify_comments_sentiment(all_comments_texts, None, batch_size=15)
                global_idx = 0
                for post in posts_data:
                    for comment in post.get("comments", []):
                        if global_idx < len(sentiment_results):
                            result = sentiment_results[global_idx]
                            
                            # Manejar tanto formato nuevo (dict) como antiguo (string)
                            if isinstance(result, dict):
                                comment["sentiment"] = result.get("sentiment", "NEUTRAL")
                                comment["sentiment_reasoning"] = result.get("reasoning", "Sin explicación")
                            else:
                                # Fallback para compatibilidad con formato antiguo
                                comment["sentiment"] = result
                                comment["sentiment_reasoning"] = "Sin explicación disponible"
                        else:
                            comment["sentiment"] = "NEUTRAL"
                            comment["sentiment_reasoning"] = "No analizado"
                        global_idx += 1
                print("✅ Comment sentiment analysis complete.")
            except Exception as e:
                print(f"Error during comment sentiment analysis: {e}")
        
        # Update JSON
        with open(filename, "w", encoding="utf-8") as f:
             json.dump(posts_data, f, indent=4, ensure_ascii=False)
        print(f"Updated JSON with sentiments and reasoning: {filename}")
        end_sentiment_time = time.time()
        
        # --- CSV Generation ---
        import csv
        print("Saving separated sentiment CSVs...")
        sentiments_lists = { "positivos": [], "negativos": [], "neutros": [] }
        
        for post in posts_data:
            p_url = post.get("post_url", "N/A")
            for comment in post.get("comments", []):
                s = comment.get("sentiment", "NEUTRAL").upper()
                c_text = comment.get("text", "")
                
                if s == "POSITIVO":
                    sentiments_lists["positivos"].append([c_text, p_url])
                elif s == "NEGATIVO":
                    sentiments_lists["negativos"].append([c_text, p_url])
                else:
                    sentiments_lists["neutros"].append([c_text, p_url])
                    
        for s_type, rows in sentiments_lists.items():
            csv_name = os.path.join(output_dir, f"comentarios_{s_type}_{search_query}.csv")
            try:
                with open(csv_name, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Comentario", "URL Post Original"])
                    writer.writerows(rows)
                print(f"  Saved {len(rows)} {s_type} comments to: {csv_name}")
            except Exception as e:
                print(f"  Error saving {s_type} CSV: {e}")
        
        # --- Generate Posts CSV with Sentiment (for import) ---
        print("\n--- Generating Posts CSV with Sentiment ---")
        posts_csv_name = os.path.join(output_dir, f"datos_extraidos_deepseek.csv")
        try:
            with open(posts_csv_name, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["source", "title", "content", "comments", "sentiment_deepseek", "explanation_deepseek"])
                
                for post in posts_data:
                    source = "facebook"
                    title = post.get("post_url", "N/A")
                    content = post.get("caption_snippet", "")
                    comments_json = json.dumps(post.get("comments", []), ensure_ascii=False)
                    sentiment = post.get("sentiment", "NEUTRAL")
                    explanation = post.get("sentiment_reasoning", "Sin explicación")
                    
                    writer.writerow([source, title, content, comments_json, sentiment, explanation])
            
            print(f"✅ Saved {len(posts_data)} posts with sentiment to: {posts_csv_name}")
            
            # ✅ NUEVO: Generar CSV unificado en formato de investigación
            try:
                import sys
                sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from shared.unified_csv_exporter import convert_facebook_to_unified
                
                unified_csv_path = os.path.join(output_dir, "formato_investigacion.csv")
                convert_facebook_to_unified(posts_csv_name, unified_csv_path)
                print(f"📋 CSV Unificado (Formato Investigación): {unified_csv_path}")
            except Exception as e:
                print(f"⚠️  Error generando CSV unificado: {e}")
                
        except Exception as e:
            print(f"❌ Error saving posts CSV: {e}")
        
        # --- Automatic Processing ---
        try:
            print("\n--- Starting Automatic Text Processing ---")
            import procesamiento_texto
            
            datos_nuevos = procesamiento_texto.cargar_datos_json(filename)
            tokens_limpios, tokens_stemmed = procesamiento_texto.procesar_texto(datos_nuevos)
            
            print(f"Processed {len(datos_nuevos)} new posts.")
            
            # Save JSON processed to Resultados folder
            processed_filename = os.path.join(output_dir, f"processed_facebook_{search_query}.json")
            processed_data = {
                "search_query": search_query,
                "total_posts": len(datos_nuevos),
                "tokens_limpios": tokens_limpios,
                "tokens_stemmed": tokens_stemmed
            }
            with open(processed_filename, "w", encoding="utf-8") as f:
                json.dump(processed_data, f, indent=4, ensure_ascii=False)
            print(f"Processed text saved to: {processed_filename}")
            
            # Save CSV processed to Resultados folder
            import csv
            csv_filename = os.path.join(output_dir, f"processed_facebook_{search_query}.csv")
            with open(csv_filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["Type", "Token"])
                for token in tokens_limpios:
                    writer.writerow(["Limpio", token])
                for token in tokens_stemmed:
                    writer.writerow(["Stemmed", token])
            print(f"Processed text saved to: {csv_filename}")
            
            # Visualize to Resultados folder
            output_img = os.path.join(output_dir, f"frecuencia_facebook_{search_query}.png")
            procesamiento_texto.visualizar_nube_palabras(tokens_limpios, output_img)
            print(f"Analysis complete. Image saved to: {output_img}")
            
            end_total_time = time.time()
            
            # --- FINAL PERFORMANCE REPORT ---
            scraping_duration = end_scraping_time - start_scraping_time
            sentiment_duration = end_sentiment_time - start_sentiment_time
            text_processing_duration = end_total_time - end_sentiment_time
            total_duration = end_total_time - start_total_time
            
            # Calculate sentiment distribution
            sentiment_distribution = {"positive": 0, "negative": 0, "neutral": 0}
            for post in posts_data:
                for comment in post.get("comments", []):
                    s = comment.get("sentiment", "NEUTRAL").upper()
                    if s == "POSITIVO" or s == "POSITIVE":
                        sentiment_distribution["positive"] += 1
                    elif s == "NEGATIVO" or s == "NEGATIVE":
                        sentiment_distribution["negative"] += 1
                    else:
                        sentiment_distribution["neutral"] += 1
            
            print("\n" + "="*50)
            print(f"       PERFORMANCE REPORT: {search_query.upper()}")
            print("="*50)
            print(f"Total Valid Posts:      {len(datos_nuevos)}")
            print(f"Total Comments Analyzed:{len(all_comments_texts)}")
            print("-" * 50)
            print(f"1. Scraping Phase:      {scraping_duration:.2f} seconds")
            print(f"   (Avg per post:       {scraping_duration/len(datos_nuevos) if len(datos_nuevos) else 0:.2f}s)")
            print(f"2. Sentiment Analysis:  {sentiment_duration:.2f} seconds (DeepSeek)")
            print(f"   (Avg per comment:    {sentiment_duration/len(all_comments_texts) if all_comments_texts else 0:.2f}s)")
            print(f"3. Text Processing:     {text_processing_duration:.2f} seconds")
            print("-" * 50)
            print(f"TOTAL EXECUTION TIME:   {total_duration:.2f} seconds")
            print("="*50)
            
            # Generate metrics JSON for master scraper
            metrics = {
                "social_network": "Facebook",
                "llm_used": "DeepSeek",
                "query": search_query,
                "execution_times": {
                    "scraping": round(scraping_duration, 2),
                    "sentiment_analysis": round(sentiment_duration, 2),
                    "text_processing": round(text_processing_duration, 2),
                    "total": round(total_duration, 2)
                },
                "data_metrics": {
                    "posts_extracted": len(datos_nuevos),
                    "comments_extracted": len(all_comments_texts),
                    "comments_analyzed": len(all_comments_texts),
                    "total_text_items": len(datos_nuevos) + len(all_comments_texts)
                },
                "sentiment_distribution": sentiment_distribution,
                "performance_metrics": {
                    "posts_per_second": round(len(datos_nuevos) / scraping_duration if scraping_duration > 0 else 0, 2),
                    "comments_per_second": round(len(all_comments_texts) / sentiment_duration if sentiment_duration > 0 else 0, 2),
                    "avg_time_per_post": round(scraping_duration / len(datos_nuevos) if len(datos_nuevos) > 0 else 0, 2)
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
