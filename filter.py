import os
import requests
from bs4 import BeautifulSoup

def run_filter():
    # --- CONFIGURATION ---
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # --- JAPANESE & ENGLISH FILTER PATTERNS ---
    # These match new character releases, maintenance, and event news.
    WANT_KEYWORDS = [
        # English
        "new", "update", "character", "release", "maintenance", "event", "fixed", "collab",
        # Japanese
        "新キャラ", "登場", "予告", "実装", "メンテ", "アップデート", "開催", "不具合", "復刻"
    ] 

    # These hide generic marketing fluff and repeat automated posts.
    IGNORE_KEYWORDS = [
        # English
        "thank you", "follow", "share", "campaign", "giveaway", "repost",
        # Japanese
        "ありがとう", "フォロー", "キャンペーン", "プレゼント", "リツイート", "引用", "抽選"
    ]

    print(f"Fetching RSS feed from RSS.app...")

    if not webhook_url:
        print("CRITICAL ERROR: DISCORD_WEBHOOK is not set.")
        return

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, features="xml")
        items = soup.find_all('item')
        print(f"Total items in feed: {len(items)}")

        matches_found = 0
        for item in items:
            title = item.find('title').text if item.find('title') else ""
            description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else "No link"
            
            # Combine all text into one searchable string
            full_text = (title + " " + description).lower()

            # 1. Check for IGNORE words first (to skip junk)
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            # 2. Check for WANT words
            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                matches_found += 1
                print(f"Match Found: {title[:50]}...")
                
                payload = {
                    "username": "MementoMori Official Tracker",
                    "embeds": [{
                        "title": title[:256],
                        "description": description[:1000],
                        "url": link,
                        "color": 3447003 # MementoMori Blue
                    }]
                }
                
                requests.post(webhook_url, json=payload)
        
        print(f"Process complete. Sent {matches_found} new posts to Discord.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
