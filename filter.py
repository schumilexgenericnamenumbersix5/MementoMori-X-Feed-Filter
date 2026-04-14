import os
import requests
from bs4 import BeautifulSoup
import re

def get_last_id(gist_id, token):
    url = f"https://api.github.com/gists/{gist_id}"
    headers = {"Authorization": f"token {token}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        # Pulls the saved ID from your Gist
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
    
    # Updated patterns for MementoMori JP feed
    WANT_KEYWORDS = [
        "新キャラ", "登場", "実装", "ラメント", "lament", "cv", "song by", 
        "予告", "メンテ", "アップデート", "開催", "復刻", "運命ガチャ", "ピックアップ"
    ] 
    IGNORE_KEYWORDS = [
        "キャンペーン", "プレゼント", "抽選", "リツイート", "フォロー", "amazonギフト", "記念"
    ]

    if not all([webhook_url, gist_id, gist_token]):
        print("Error: Missing GIST_ID or GIST_TOKEN in GitHub Secrets.")
        return

    try:
        last_sent_id = get_last_id(gist_id, gist_token)
        print(f"Last processed ID: {last_sent_id}")

        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'html.parser')
        items = soup.find_all('item')

        if not items:
            return

        newest_id = last_sent_id
        
        # Process items oldest to newest
        for item in reversed(items[:15]):
            title = item.find('title').text if item.find('title') else ""
            link = item.find('link').text if item.find('link') else ""
            
            # Extract the actual Tweet ID from the URL
            match = re.search(r'status/(\d+)', link)
            current_id = match.group(1) if match else "0"

            # Skip if we already sent this one
            if current_id <= last_sent_id:
                continue

            # Filtering logic
            full_text = title.lower()
            if any(word.lower() in full_text for word in IGNORE_KEYWORDS):
                continue

            if any(word.lower() in full_text for word in WANT_KEYWORDS):
                # vxtwitter ensures the BIG Kepler-style image card shows up
                clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
                
                payload = {
                    "username": "MementoMori Official",
                    "avatar_url": "https://mementomori.jp/favicon.ico",
                    "content": f"**{title}**\n{clean_link}"
                }
                
                res = requests.post(webhook_url, json=payload)
                if res.status_code in [200, 204]:
                    newest_id = current_id
                    print(f"Successfully posted: {current_id}")

        # Save the new ID so we don't dupe next time
        if newest_id != last_sent_id:
            update_last_id(gist_id, gist_token, newest_id)
            print(f"Updated Gist memory to: {newest_id}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
