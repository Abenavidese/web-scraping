import os
import json
import time
import random
import re
import argparse
from playwright.sync_api import sync_playwright

def random_sleep(min_seconds=2, max_seconds=5):
    time.sleep(random.uniform(min_seconds, max_seconds))

def run():
    # Argumentos compatibles con master_scraper.py
    parser = argparse.ArgumentParser(description="Facebook Scraper - Extracción de Posts y Comentarios")
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
            random_sleep(2, 4)
            page.goto("https://www.facebook.com/")

        random_sleep(3, 5)

        # Search
        print(f"Searching for '{search_query}'...")
        # Direct navigation to search results for posts
        # URL format: https://www.facebook.com/search/posts/?q=query
        search_url = f"https://www.facebook.com/search/posts/?q={search_query}"
        page.goto(search_url)
        random_sleep(5, 8)
        
        # Check login
        if "login" in page.url and "search" not in page.url:
             print("Redirected to login. Session might be invalid.")
             return

        # Scroll to load posts
        print(f"Scrolling to load enough posts (Goal: {num_posts_to_scrape})...")
        last_count = 0
        
        # Robust multi-selector for counting posts
        post_selectors = 'div[role="article"], .x1yztbdb, [data-pagelet^="FeedUnit"], [data-ad-comet-preview="message"]'
        
        for s in range(15):
            current_found = page.locator(post_selectors).count()
            
            print(f"  Scroll {s+1}: Approx. {current_found} posts found...")
            if current_found >= num_posts_to_scrape:
                break
                
            page.mouse.wheel(0, 3000)
            random_sleep(3, 5)
            
            if current_found == last_count and s > 4:
                print("  Stopping: No more new posts loading.")
                break
            last_count = current_found



        # Extract Posts
        print("Extracting posts...")
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
                random_sleep(2, 3)
                
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
                        random_sleep(1, 2)
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
                for link in all_links:
                    href = link.get_attribute("href")
                    if href and ("/posts/" in href or "/permalink.php" in href or "/groups/" in href or "story_fbid" in href):
                        if href.startswith("/"):
                             href = "https://www.facebook.com" + href
                        # Avoid main group URLs, look for post-specific ones
                        if "/posts/" in href or "fbid=" in href or "permalink" in href:
                             full_url = href.split("?")[0] if "?" in href and "fbid" not in href else href
                             break
                
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
                print(f"  [{count+1}] Attempting to open comments (Target: {num_comments_to_scrape})...")
                comments_list = []
                try:
                    # Look for comment button by common labels or roles
                    # Facebook often uses aria-label="Comment" or "Escribe un comentario"
                    comment_btn = None
                    button_selectors = [
                        'div[aria-label="Comentar"]',
                        'div[aria-label="Comment"]',
                        'div[role="button"]:has-text("Comentar")',
                        'div[role="button"]:has-text("Comment")',
                        'span:has-text("Comentarios")',
                        'span:has-text("Comments")',
                        'div[aria-label*="Leave a comment"]', 
                        'div[aria-label*="Escribe un comentario"]'
                    ]
                    
                    found_btn = False
                    for sel in button_selectors:
                        # try to find within the article first
                        btns = article.locator(sel).all()
                        for btn in btns:
                            if btn.is_visible():
                                comment_btn = btn
                                found_btn = True
                                break
                        if found_btn: break
                    
                    if comment_btn:
                        # Javascript click is sometimes more reliable for these react buttons that might be covered
                        # comment_btn.click() 
                        comment_btn.dispatch_event("click")
                        random_sleep(3, 5) 
                        
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
                                random_sleep(1, 2)
                                # Click "All comments"
                                all_comments_opt = page.locator('div[role="menuitem"]:has-text("Todos los comentarios"), div[role="menuitem"]:has-text("All comments")').first
                                if all_comments_opt.is_visible():
                                    all_comments_opt.dispatch_event("click")
                                    print("    Switched to 'All comments' filter.")
                                    random_sleep(2, 4)
                        except:
                            pass

                        # Loop to load more comments if needed
                        for _ in range(8): # Check 8 times
                            current_comments_count = comment_scope.locator('div[role="article"]').count()
                            if current_comments_count >= num_comments_to_scrape:
                                break
                                
                            # Scroll logic: standard PageDown is often best for lazy loaders
                            try:
                                if dialog.is_visible():
                                    dialog.click() # Focus
                                    page.keyboard.press("End") # Go to bottom
                                    random_sleep(1, 2)
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
                                        random_sleep(2, 4) # Weight for load
                                        break # Click one at a time to avoid errors
                                
                                if not clicked_any:
                                     # Sometimes it's a div role=button
                                     more_divs = comment_scope.locator('div[role="button"]').filter(has_text=re.compile(r"(ver|view).+(comentarios|comments)", re.IGNORECASE)).all()
                                     for b in more_divs:
                                         if b.is_visible():
                                             b.scroll_into_view_if_needed()
                                             b.dispatch_event("click")
                                             random_sleep(2, 4)
                                             break
                                             
                                # Expand individual long comments ("See more" / "Ver más" inline)
                                inline_see_more = comment_scope.locator('div[role="button"]:has-text("Ver más"), div[role="button"]:has-text("See more")').all()
                                for btn in inline_see_more:
                                    if btn.is_visible():
                                         btn.dispatch_event("click")
                                         random_sleep(0.5, 1)

                            except:
                                pass
                            
                            random_sleep(1, 2)


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
                                if len(c_text) > 2 and c_text not in ["Me gusta", "Responder", "Like", "Reply", "Hide", "Ocultar"]:
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
                                 # specific filtering for fallback
                                 if len(c_text) > 3 and c_text != post_text and c_text not in ["Me gusta", "Responder", "Like", "Reply"]:
                                     comments_list.append({"user": "FB User", "text": c_text})
                                     extracted_c += 1

                        # Close dialog if it was open
                        if dialog.is_visible():
                            # multiple ways to close: escape, or click close button
                            page.keyboard.press("Escape")
                            random_sleep(1, 2)
                            
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
                
                if not post_text and not comments_list:
                    continue 

                # FILTER: Skip empty/ghost posts (no comments, no image, no URL)
                if not comments_list and image_url == "N/A" and full_url == "N/A":
                    continue

                posts_data.append({
                    "post_url": full_url,
                    "caption_snippet": post_text[:200] if post_text else "No text found",
                    "image_url": img_url,
                    "comments": comments_list
                })
                count += 1
                
            except Exception as e:
                continue

        print(f"Extracted {len(posts_data)} posts.")
        
        # Save JSON to Resultados folder
        filename = os.path.join(output_dir, f"results_facebook_{search_query}.json")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(posts_data, f, indent=4, ensure_ascii=False)
            
        print(f"Data saved to {filename}")
        
        browser.close()
        
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
            
        except Exception as e:
            print(f"Error during text processing: {e}")

if __name__ == "__main__":
    run()