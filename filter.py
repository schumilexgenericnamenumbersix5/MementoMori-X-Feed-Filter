import os
import requests
from bs4 import BeautifulSoup

def run_filter():
    # --- CONFIGURATION ---
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # --- REFINED EN/JP KEYWORD PATTERNS ---
    # Targets: New Witches, Laments, CV reveals, and Game Updates
    WANT_KEYWORDS = [
        "新キャラ", "登場", "実装", "ラメント", "lament", "cv", "song by",
        "予告", "メンテ", "アップデート", "開催", "復刻", "update", "maintenance",
        "運命ガチャ", "ピックアップ", "布告", "告知", "美少女"
    ] 

    # Strictly filters out the daily repetitive marketing spam
    IGNORE_KEYWORDS = [
        "キャンペーン", "プレゼント", "抽選", "リツイート", "フォロー", 
        "giveaway", "retweet", "campaign", "thank you", "記念", "amazonギフト"
    ]

    print("Fetching RSS feed from RSS.app...")

    if not webhook_url:
        print("CRITICAL ERROR: DISCORD_WEBHOOK is not set.")
        return

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(rss_url, headers=headers)
        response.raise_for_status()
        
        # Parse RSS items
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')
        print(f"Total items found in feed: {len(items)}")

        matches_found = 0
        for item in items:
            title = item.find('title').text if item.find('title') else ""
            description = item.find('description').text if item.find('description') else ""
            # RSS.app links usually point directly to the tweet
            link = item.find('link').text if item.find('link') else ""
            
            full_text = (title + " " + description).lower()

            # 1. Skip ignored marketing junk
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            # 2. Match high-value content
            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                matches_found += 1
                print(f"Match Found: {title[:50]}...")
                
                # --- THE IDEAL FORMAT FIX ---
                # To get the large image preview like the Kepler tweet:
                # We send the link OUTSIDE of an embed. Discord will then scrape the 
                # Twitter/X metadata and generate the large card automatically.
                message_content = f"🔔 **MementoMori Update Found!**\n\n{title}\n\n{link}"
                
                payload = {
                    "username": "MementoMori Official",
                    "avatar_url": "https://mementomori.jp/favicon.ico",
                    "content": message_content
                }
                
                requests.post(webhook_url, json=payload)
        
        print(f"Process complete. Sent {matches_found} matches to Discord.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
