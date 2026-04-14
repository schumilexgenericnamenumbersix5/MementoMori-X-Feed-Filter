import os
import requests
from bs4 import BeautifulSoup

def run_filter():
    # --- CONFIGURATION ---
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # --- EN/JP KEYWORD PATTERNS ---
    # Targets: New Witches, Laments, Maintenance, and specialized Gacha banners
    WANT_KEYWORDS = [
        # Character & Music
        "新キャラ", "登場", "実装", "ラメント", "lament", "cv", "song by",
        # Updates & Events
        "予告", "メンテ", "アップデート", "開催", "復刻", "update", "maintenance",
        # Gacha/Specifics
        "運命ガチャ", "ピックアップ", "布告", "告知"
    ] 

    # Targets: Daily RT campaigns and generic marketing fluff
    IGNORE_KEYWORDS = [
        "キャンペーン", "プレゼント", "抽選", "リツイート", "フォロー", 
        "giveaway", "retweet", "campaign", "thank you", "記念"
    ]

    print("Fetching RSS feed from RSS.app...")

    if not webhook_url:
        print("CRITICAL ERROR: DISCORD_WEBHOOK is not set.")
        return

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        
        # Using 'html.parser' instead of 'xml' to avoid the missing library error
        # while still correctly pulling the XML tags from the RSS feed.
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')
        print(f"Total items found in feed: {len(items)}")

        matches_found = 0
        for item in items:
            # RSS tags are case-insensitive in html.parser
            title = item.find('title').text if item.find('title') else ""
            description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else ""
            
            full_text = (title + " " + description).lower()

            # 1. Skip ignored junk
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            # 2. Match wanted content
            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                matches_found += 1
                print(f"Match Found: {title[:50]}...")
                
                payload = {
                    "username": "MementoMori Official Tracker",
                    "embeds": [{
                        "title": title[:256],
                        "description": description[:1000],
                        "url": link,
                        "color": 3066993 # MementoMori themed color
                    }]
                }
                
                requests.post(webhook_url, json=payload)
        
        print(f"Process complete. Sent {matches_found} matches to Discord.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
