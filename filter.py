import os
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
TARGET_ACCOUNT = "mementomori_boi"
NITTER_INSTANCE = "https://nitter.net"

# Add your keywords here
WANT_KEYWORDS = ["Update", "Witch", "Maintenance", "New"]  # Only send if it has these
IGNORE_KEYWORDS = ["Ad", "Promo", "Spam"]               # Skip if it has these

def send_to_discord(tweet_url, tweet_text):
    """Sends the link to Discord using fxtwitter for rich previews/images."""
    if not WEBHOOK_URL:
        print("!! ERROR: DISCORD_WEBHOOK_URL not found in Secrets.")
        return

    # Convert to fxtwitter so Discord shows the image/embed
    pretty_url = tweet_url.replace("nitter.net", "fxtwitter.com").replace("x.com", "fxtwitter.com")
    
    payload = {
        "content": f"**MementoMori Update:**\n{pretty_url}"
    }
    
    requests.post(WEBHOOK_URL, json=payload)
    print(f"Sent: {pretty_url}")

def run_filter():
    print(f"Scraping @{TARGET_ACCOUNT}...")
    url = f"{NITTER_INSTANCE}/{TARGET_ACCOUNT}"
    headers = {"User-Agent": "Mozilla/5.0"}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        tweets = soup.find_all("div", class_="tweet-body")

        for tweet in tweets:
            # 1. Get the Link
            link_element = tweet.find("a", class_="tweet-link")
            if not link_element: continue
            tweet_link = f"{NITTER_INSTANCE}{link_element.get('href').split('#')[0]}"
            
            # 2. Get the Text for filtering
            content_element = tweet.find("div", class_="tweet-content")
            tweet_text = content_element.get_text() if content_element else ""

            # 3. Apply WANT/IGNORE logic
            should_send = False
            
            # Check if it has any 'WANT' words (or set to True if WANT list is empty)
            if not WANT_KEYWORDS or any(word.lower() in tweet_text.lower() for word in WANT_KEYWORDS):
                should_send = True
            
            # Check if it has any 'IGNORE' words
            if any(word.lower() in tweet_text.lower() for word in IGNORE_KEYWORDS):
                should_send = False

            # 4. If it passed the filter, send it!
            if should_send:
                send_to_discord(tweet_link, tweet_text)
            else:
                print(f"Skipping (Filtered): {tweet_link}")

    except Exception as e:
        print(f"Error during run: {e}")

if __name__ == "__main__":
    run_filter()
