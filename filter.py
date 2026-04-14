import os
import requests
from bs4 import BeautifulSoup
import re

def get_last_id(gist_id, token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        # Retrieves the saved Tweet ID from your Gist memory
        return res.json()['files']['last_id.txt']['content'].strip()
    return "0"

def update_last_id(gist_id, token, new_id):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    data = {"files": {"last_id.txt": {"content": str(new_id)}}}
    requests.patch(url, headers=headers, json=data)

def run_filter():
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    gist_id = os.getenv("GIST_ID")
    gist_token = os.getenv("GIST_TOKEN")
    
    # Refined keywords for MementoMori content
    WANT_KEYWORDS = [
        "新キャラ", "登場", "実装", "ラメント", "lament", "cv", "song by", 
        "予告", "メンテ", "アップデート", "開催", "復刻", "運命ガチャ", "ピックアップ"
    ] 
    IGNORE_KEYWORDS = [
        "キャンペーン", "プレゼント", "抽選", "リツイート", "フォロー", "amazonギフト", "記念"
    ]

    if not all([webhook_url, gist_id, gist_token]):
        print("Error: Missing environment variables. Check GIST_ID and GIST_TOKEN in YAML.")
        return

    try:
        last_sent_id = get_last_id(gist_id, gist_token)
        print(f"Checking for tweets newer than ID: {last_sent_id}")

        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')

        if not items:
            print("No items found in feed.")
            return

        newest_processed_id = last_sent_id
        
        # Process items from oldest to newest (reversed) to maintain chronological order
        for item in reversed(items[:15]):
            title = item.find('title').text if item.find('title') else ""
            link = item.find('link').text if item.find('link') else ""
            
            # Extract the numerical Tweet ID from the URL
            match = re.search(r'status/(\d+)', link)
            current_id = match.group(1) if match else "0"

            # 1. Skip if already processed
            if current_id <= last_sent_id:
                continue

            # 2. Skip marketing/giveaway spam
            full_text = title.lower()
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            # 3. Match high-value content
            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                # vxtwitter forces Discord to show the large image card
                clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
                
                payload = {
                    "username": "MementoMori Official",
                    "avatar_url": "https://mementomori.jp/favicon.ico",
                    "content": f"**{title}**\n{clean_link}"
                }
                
                res = requests.post(webhook_url, json=payload)
                if res.status_code in [200, 204]:
                    newest_processed_id = current_id
                    print(f"Successfully posted Tweet ID: {current_id}")

        # Update Gist memory so we don't dupe on the next run
        if newest_processed_id != last_sent_id:
            update_last_id(gist_id, gist_token, newest_processed_id)
            print(f"Memory updated to: {newest_processed_id}")

    except Exception as e:
        print(f"Error occurred: {e}")

if __name__ == "__main__":
    run_filter()
