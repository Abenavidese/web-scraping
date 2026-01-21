import asyncio
import random
from playwright.async_api import async_playwright

class XScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Starts the browser session."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        
        # Load state if exists
        try:
            self.context = await self.browser.new_context(
                storage_state="state.json",
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            print("Loaded previous session state.")
        except Exception:
            print("No previous session state found. Starting fresh.")
            self.context = await self.browser.new_context(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
        self.page = await self.context.new_page()

    async def _human_sleep(self, min_seconds=2, max_seconds=5):
        """Sleeps for a random amount of time to simulate human behavior."""
        sleep_time = random.uniform(min_seconds, max_seconds)
        print(f"Sleeping for {sleep_time:.2f} seconds...")
        await asyncio.sleep(sleep_time)

    async def login(self, username, password):
        """Logs into X.com."""
        print("Checking if already logged in...")
        await self.page.goto("https://x.com/home")
        await self._human_sleep(3, 5)
        
        try:
            await self.page.wait_for_selector("a[data-testid='AppTabBar_Home_Link']", timeout=5000)
            print("Already logged in!")
            return
        except:
            print("Not logged in. Proceeding to login page...")
        
        await self.page.goto("https://x.com/i/flow/login")
        await self._human_sleep(4, 7)

        # Enter Username
        print("Entering username...")
        try:
            input_selector = "input[autocomplete='username']"
            await self.page.wait_for_selector(input_selector, timeout=10000)
            await self.page.fill(input_selector, username)
            await self._human_sleep(1, 3)
            await self.page.keyboard.press("Enter")
            await self._human_sleep(3, 5)
        except Exception as e:
            print(f"Username step skipped/failed: {e}")

        # Enter Password
        print("Entering password...")
        try:
            password_selector = "input[name='password']"
            await self.page.wait_for_selector(password_selector, timeout=10000)
            await self.page.fill(password_selector, password)
            await self._human_sleep(2, 4)
            await self.page.keyboard.press("Enter")
            await self._human_sleep(5, 8)
        except Exception as e:
            print(f"Password step skipped/failed: {e}")

        # Wait for home page or manual login completion
        print("Waiting for login to complete... IF AUTOMATION FAILED, PLEASE LOG IN MANUALLY NOW.")
        try:
            # Wait up to 5 minutes for user to fix login
            await self.page.wait_for_selector("a[data-testid='AppTabBar_Home_Link']", timeout=300000)
            print("Login detected successfully.")
            
            # Save state
            await self.context.storage_state(path="state.json")
            print("Session state saved to 'state.json'. Next run will be faster!")
            
        except:
             print("Could not detect home link after 5 minutes. Proceeding anyway (might fail)...")


    async def scrape_search(self, query, count=50):
        """Scrapes tweets for a given search query."""
        print(f"Searching for: {query}")
        # Use 'f=live' to get latest tweets or just standard search
        await self.page.goto(f"https://x.com/search?q={query}&src=typed_query&f=live")
        await self._human_sleep(5, 8)

        tweets_data = []
        last_height = await self.page.evaluate("document.body.scrollHeight")
        
        consecutive_scrolls_without_new_tweets = 0

        while len(tweets_data) < count:
            # Select tweet articles
            # X uses <article data-testid="tweet">
            articles = await self.page.query_selector_all("article[data-testid='tweet']")
            
            new_tweets_found = 0
            for article in articles:
                try:
                    # Extract Text
                    text_element = await article.query_selector("div[data-testid='tweetText']")
                    text = await text_element.inner_text() if text_element else ""
                    
                    # Extract Author
                    user_element = await article.query_selector("div[data-testid='User-Name']")
                    user_text = await user_element.inner_text() if user_element else "Unknown"
                    # User text usually contains name and handle, we can clean it later
                    
                    # Extract Time
                    time_element = await article.query_selector("time")
                    timestamp = await time_element.get_attribute("datetime") if time_element else ""
                    
                    # Extract Tweet URL
                    # Usually in the time element's parent or a link with '/status/'
                    tweet_url = ""
                    link_element = await article.query_selector("a[href*='/status/']")
                    if link_element:
                        href = await link_element.get_attribute("href")
                        if href:
                            tweet_url = f"https://x.com{href}" if not href.startswith("http") else href

                    tweet_obj = {
                        "author": user_text.replace('\n', ' '),
                        "text": text.replace('\n', ' '),
                        "timestamp": timestamp,
                        "url": tweet_url
                    }

                    # Simple check to avoid checking exact duplicates in this loop if feasible, 
                    # but sets/hashing is better done on the full list id. 
                    if tweet_obj["text"] and tweet_obj not in tweets_data:
                        tweets_data.append(tweet_obj)
                        new_tweets_found += 1
                        
                    if len(tweets_data) >= count:
                        break
                except Exception as e:
                    continue
            
            if len(tweets_data) >= count:
                break

            print(f"Collected {len(tweets_data)} tweets so far...")

            # Scroll down
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await self._human_sleep(3, 6)
            
            new_height = await self.page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                print("Reached bottom or content not loading.")
                consecutive_scrolls_without_new_tweets += 1
                if consecutive_scrolls_without_new_tweets > 3:
                     # Attempt small scroll up to trigger load
                    await self.page.evaluate("window.scrollBy(0, -300)")
                    await self._human_sleep(2, 4)
            else:
                consecutive_scrolls_without_new_tweets = 0
                
            last_height = new_height

        return tweets_data

    async def scrape_comments(self, tweet_url, max_comments=5):
        """Visits a tweet URL and extracts comments."""
        if not tweet_url:
            return []
            
        print(f"  Accessing tweet: {tweet_url}")
        try:
            # Increase timeout for specific tweet page loading
            await self.page.goto(tweet_url, timeout=60000, wait_until='domcontentloaded')
            await self._human_sleep(3, 5)
            
            comments = []
            
            last_height = await self.page.evaluate("document.body.scrollHeight")
            consecutive_scrolls = 0
            
            # X replies are also articles. Usually the first one is the main tweet (or conversation chain).
            # We will grab articles and check if they are replies.
            
            attempts = 0
            while len(comments) < max_comments and attempts < 5:
                # Select all tweets on page
                articles = await self.page.query_selector_all("article[data-testid='tweet']")
                
                # If we have multiple articles, subsequent ones are usually replies
                if len(articles) > 1:
                    # Skip the first one (main tweet)
                    for article in articles[1:]: 
                        try:
                            text_element = await article.query_selector("div[data-testid='tweetText']")
                            text = await text_element.inner_text() if text_element else ""
                            
                            user_element = await article.query_selector("div[data-testid='User-Name']")
                            user_text = await user_element.inner_text() if user_element else "Unknown"

                            comment_obj = {
                                "author": user_text.replace('\n', ' '),
                                "text": text.replace('\n', ' ')
                            }
                            
                            # Simple dedup
                            if text and comment_obj not in comments:
                                comments.append(comment_obj)
                            
                            if len(comments) >= max_comments:
                                break
                        except:
                            continue
                
                if len(comments) >= max_comments:
                    break
                    
                # Scroll a bit
                await self.page.evaluate("window.scrollBy(0, 500)")
                await self._human_sleep(1, 2)
                
                new_height = await self.page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    consecutive_scrolls += 1
                    if consecutive_scrolls > 2:
                        break # Stop if no new content
                else:
                    consecutive_scrolls = 0
                last_height = new_height
                attempts += 1
                
            print(f"  Extracted {len(comments)} comments.")
            return comments

        except Exception as e:
            print(f"  Error extracting comments: {e}")
            return []

    async def close(self):
        """Closes the browser."""
        await self.browser.close()
        await self.playwright.stop()
