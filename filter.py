import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

def clean_text(text):
    if not text: return ""
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    return text.strip()

def strip_html(html_content):
    if not html_content: return ""
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def run_filter():
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # Negative filters
    IGNORE_KEYWORDS = [
        "アップデート", "Update",
        "メンテ", "Maintenance",
    ]

    if not webhook_url:
        print("Error: Missing DISCORD_WEBHOOK.")
        return

    try:
        print(f"Fetching RSS: {rss_url}")
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')

        if not items:
            print("No items found in feed.")
            return

        now = datetime.now(timezone.utc)
        # Increased window to 24 hours for testing; change back to 125 if needed
        time_threshold = now - timedelta(minutes=625)
        
        print(f"Filtering for posts after: {time_threshold}")

        for item in reversed(items):
            pub_date_str = item.find('pubDate').text if item.find('pubDate') else None
            if not pub_date_str: continue
            
            pub_date = parsedate_to_datetime(pub_date_str)
            
            # 1. TIME CHECK
            if pub_date < time_threshold:
                continue

            title = clean_text(item.find('title').text if item.find('title') else "")
            raw_description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else ""

            clean_description = strip_html(raw_description)
            # Combine everything for searching
            full_content = f"{title} {clean_description}"
            
            # 2. KEYWORD CHECK
            # We check lowercase for English but keep original for Japanese
            content_lower = full_content.lower()
            skip = False
            for word in IGNORE_KEYWORDS:
                if word.lower() in content_lower:
                    print(f"SKIPPED (Keyword '{word}'): {title[:30]}...")
                    skip = True
                    break
            
            if skip: continue

            # 3. SEND TO DISCORD
            clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
            
            payload = {
                "username": "MementoMori Official",
                "content": clean_link
            }
            
            resp = requests.post(webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                print(f"SUCCESSFULLY POSTED: {clean_link}")
            else:
                print(f"POST FAILED ({resp.status_code}): {resp.text}")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    run_filter()
