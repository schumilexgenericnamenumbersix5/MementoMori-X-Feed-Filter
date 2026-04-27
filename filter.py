import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

def clean_text(text):
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    return text.strip()

def strip_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def run_filter():
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # Negative filters: If any of these are found, skip the post
    IGNORE_KEYWORDS = [
        "アップデート", "Update",
        "メンテ", "Maintenance",
    ]

    if not webhook_url:
        print("Error: Missing DISCORD_WEBHOOK.")
        return

    try:
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')

        if not items:
            return

        now = datetime.now(timezone.utc)
        # 125-minute window
        time_threshold = now - (datetime.now(timezone.utc) - datetime.now(timezone.utc)) # Placeholder logic fix below
        import datetime as dt
        time_threshold = now - dt.timedelta(minutes=125)

        for item in reversed(items):
            pub_date_str = item.find('pubDate').text if item.find('pubDate') else None
            if not pub_date_str: continue
            
            pub_date = parsedate_to_datetime(pub_date_str)
            if pub_date < time_threshold: continue

            title = clean_text(item.find('title').text if item.find('title') else "")
            raw_description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else ""

            clean_description = strip_html(raw_description)
            full_content = (title + " " + clean_description).lower()
            
            # Exclusion Logic: Skip if IGNORE_KEYWORDS are present
            if any(word.lower() in full_content for word in IGNORE_KEYWORDS):
                continue

            # Convert to vxtwitter for better embedding
            clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
            
            # Send only the link
            payload = {
                "username": "MementoMori Official",
                "content": clean_link
            }
            requests.post(webhook_url, json=payload)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
