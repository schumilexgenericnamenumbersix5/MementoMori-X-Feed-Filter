import os
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from deep_translator import GoogleTranslator

def clean_text(text):
    text = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', text, flags=re.DOTALL)
    return text.strip()

def strip_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    for script in soup(["script", "style"]):
        script.decompose()
        
    text = soup.get_text(separator=" ")
    # Removes the Twitter signature/footer (— Name @handle Date)
    text = re.sub(r'—.*?\(@.*?\).*$', '', text, flags=re.MULTILINE)
    return " ".join(text.split())

def run_filter():
    rss_url = "https://rss.app/feeds/gNSWbxS89cf9JqaP.xml"
    webhook_url = os.getenv("DISCORD_WEBHOOK")
    
    WANT_KEYWORDS = [
        "新キャラ", "New Character", "登場", "Appears", "実装", "Released",
        "ラメント", "Lament", "cv", "song by", "予告", "Preview",
        "開催", "Held", "復刻", "Rerun", "Returning", "運命ガチャ", "Chance of Fate",
        "ピックアップ", "Pick-up", "キャンペーン", "Campaign", "記念", "Anniversary"
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
        # Set to exactly 125 minutes as requested
        time_threshold = now - timedelta(minutes=125)

        for item in reversed(items):
            pub_date_str = item.find('pubDate').text if item.find('pubDate') else None
            if not pub_date_str: continue
            
            pub_date = parsedate_to_datetime(pub_date_str)
            if pub_date < time_threshold: continue

            title = clean_text(item.find('title').text if item.find('title') else "")
            raw_description = item.find('description').text if item.find('description') else ""
            link = item.find('link').text if item.find('link') else ""

            # Check logic
            clean_description = strip_html(raw_description)
            full_content = (title + " " + clean_description).lower()
            
            if any(word.lower() in full_content for word in WANT_KEYWORDS):
                try:
                    translated_text = GoogleTranslator(source='auto', target='en').translate(clean_description)
                except Exception:
                    translated_text = clean_description

                # Remove hashtags
                translated_text = re.sub(r'#\w+', '', translated_text)
                # Remove extra whitespace
                translated_text = re.sub(r'\s+', ' ', translated_text).strip()

                # Replace standard Twitter links with vxtwitter for better Discord embeds
                clean_link = link.replace("x.com", "vxtwitter.com").replace("twitter.com", "vxtwitter.com")
                
                payload = {
                    "username": "MementoMori Official",
                    "content": f"{translated_text}\n\n{clean_link}"
                }
                requests.post(webhook_url, json=payload)

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    run_filter()
