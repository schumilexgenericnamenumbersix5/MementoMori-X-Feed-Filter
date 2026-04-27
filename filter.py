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
    # Remove script/style but also remove hidden links that might contain "Update" or "Live"
    for tag in soup(["script", "style", "a"]):
        tag.decompose()
    text = soup.get_text(separator=" ")
    return " ".join(text.split())

def run_filter():
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    # Negative filters
    IGNORE_KEYWORDS = ["アップデート", "Update", "メンテ", "Maintenance"]

    if not webhook_url:
        print("Error: Missing DISCORD_WEBHOOK.")
        return

    try:
        print(f"--- Starting Fetch ---")
        response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        response.raise_for_status()
        
        # Use 'xml' parser specifically
        soup = BeautifulSoup(response.content, 'xml')
        items = soup.find_all('item')

        if not items:
            print("No <item> tags found. Check if the RSS URL is still valid.")
            return

        now = datetime.now(timezone.utc)
        time_threshold = now - timedelta(minutes=625)
        print(f"Threshold: {time_threshold} | Now: {now}")

        found_in_window = 0

        for item in reversed(items):
            # Try to get the date
            pub_date_tag = item.find('pubDate')
            if not pub_date_tag:
                continue
            
            pub_date = parsedate_to_datetime(pub_date_tag.text)
            
            # Skip if older than threshold
            if pub_date < time_threshold:
                continue
            
            found_in_window += 1
            
            # Get content
            title = clean_text(item.find('title').text if item.find('title') else "")
            # Some RSS feeds use <content:encoded> instead of description
            desc_tag = item.find('description') or item.find('encoded')
            description = strip_html(desc_tag.text if desc_tag else "")
            link = item.find('link').text if item.find('link') else ""

            full_content = f"{title} {description}"
            content_lower = full_content.lower()

            print(f"Checking Item: {title[:50]}...") # Debug log

            # Keyword Check
            skip = False
            for word in IGNORE_KEYWORDS:
                if word.lower() in content_lower:
                    print(f"   >> SKIPPED: Found keyword '{word}'")
                    skip = True
                    break
            
            if skip: continue

            # Format Link
            clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
            
            # Post to Discord
            payload = {
                "username": "MementoMori Official",
                "content": clean_link
            }
            
            resp = requests.post(webhook_url, json=payload)
            if resp.status_code in [200, 204]:
                print(f"   >> SUCCESS: {clean_link}")
            else:
                print(f"   >> WEBHOOK ERROR ({resp.status_code}): {resp.text}")

        if found_in_window == 0:
            print("No items found within the 625-minute window.")

    except Exception as e:
        print(f"Critical Error: {e}")

if __name__ == "__main__":
    run_filter()
