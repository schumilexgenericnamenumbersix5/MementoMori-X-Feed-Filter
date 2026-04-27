import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

def clean_text(text):
    if not text: return ""
    # Strip CDATA and extra whitespace
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    return text.strip()

def strip_html(html_content):
    if not html_content: return ""
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove script/style and links (which often contain "Update" or "Live")
    for tag in soup(["script", "style", "a"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def run_filter():
    # UPDATED TO NITTER RSS
    rss_url = "https://nitter.net/mementomori_boi/rss"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # Negative filters
    IGNORE_KEYWORDS = ["アップデート", "Update", "メンテ", "Maintenance"]

    if not webhook_url:
        print("Error: Missing DISCORD_WEBHOOK.")
        return

    try:
        print(f"--- Fetching from Nitter ---")
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')

        if not items:
            print("No items found. Nitter instance might be rate-limited. Try a different instance if this persists.")
            return

        now = datetime.now(timezone.utc)
        # Using your specified window
        time_threshold = now - timedelta(minutes=125)
        print(f"Checking for posts after: {time_threshold}")

        found_count = 0

        for item in reversed(items):
            pub_date_tag = item.find('pubDate')
            if not pub_date_tag: continue
            
            pub_date = parsedate_to_datetime(pub_date_tag.text)
            
            if pub_date < time_threshold:
                continue
            
            # Content parsing
            title = clean_text(item.find('title').text if item.find('title') else "")
            description = strip_html(item.find('description').text if item.find('description') else "")
            link = item.find('link').text if item.find('link') else ""

            # Nitter often puts the full tweet in the description
            full_content = f"{title} {description}"
            content_lower = full_content.lower()

            # Filter Check
            skip = False
            for word in IGNORE_KEYWORDS:
                if word.lower() in content_lower:
                    print(f"SKIPPED: Found '{word}' in tweet.")
                    skip = True
                    break
            
            if skip: continue

            # Convert to vxtwitter for Discord
            clean_link = link.replace("nitter.net", "vxtwitter.com")
            # Handle cases where nitter link is a bit different
            clean_link = re.sub(r'https?://[^/]+', 'https://vxtwitter.com', clean_link)
            
            payload = {
                "username": "MementoMori Official",
                "content": clean_link
            }
            
            resp = requests.post(webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                print(f"SUCCESS: {clean_link}")
                found_count += 1
            else:
                print(f"FAILED: {resp.status_code}")

        if found_count == 0:
            print("No new tweets matching criteria found.")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    run_filter()
