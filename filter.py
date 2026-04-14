import os
import requests
from bs4 import BeautifulSoup

def run_filter():
    # --- CONFIGURATION ---
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # --- REFINED KEYWORDS ---
    WANT_KEYWORDS = [
        "新キャラ", "登場", "実装", "ラメント", "lament", "cv", "song by",
        "予告", "メンテ", "アップデート", "開催", "復刻", "update", "maintenance",
        "運命ガチャ", "ピックアップ", "布告", "告知"
    ] 

    IGNORE_KEYWORDS = [
        "キャンペーン", "プレゼント", "抽選", "リツイート", "フォロー", 
        "giveaway", "retweet", "campaign", "thank you", "記念", "amazonギフト"
    ]

    if not webhook_url:
        print("CRITICAL ERROR: DISCORD_WEBHOOK is not set.")
        return

    try:
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')

        if not items:
            print("No items found.")
            return

        print(f"Checking {len(items)} items for matches...")

        # We check the 5 most recent tweets
        for item in items[:5]:
            title = item.find('title').text if item.find('title') else ""
            link = item.find('link').text if item.find('link') else ""
            
            # 1. Force the link to be a clean X/Twitter link for fxtwitter to work
            # This strips RSS.app tracking and forces the preview
            if "rss.app" in link:
                # Often the real link is in the guid or can be cleaned
                # If RSS.app is masking it, we try to keep it as is but fix the domain
                clean_link = link.replace("x.com", "fxtwitter.com").replace("twitter.com", "fxtwitter.com")
            else:
                clean_link = link.replace("x.com", "fxtwitter.com").replace("twitter.com", "fxtwitter.com")
            
            full_text = title.lower()

            # 2. Skip marketing spam
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            # 3. Match and Send
            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                # We send the title and the clean link separately to force Discord to embed it
                message = f"**{title}**\n{clean_link}"
                
                payload = {
                    "username": "MementoMori Official",
                    "avatar_url": "https://mementomori.jp/favicon.ico",
                    "content": message
                }
                
                res = requests.post(webhook_url, json=payload)
                if res.status_code in [200, 204]:
                    print(f"Sent match: {title[:30]}")
                else:
                    print(f"Discord error: {res.status_code}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
