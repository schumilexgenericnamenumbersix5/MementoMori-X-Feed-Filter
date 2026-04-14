import os
import requests
import feedparser
import sys

# --- CONFIG ---
RSS_URL = "https://nitter.net/mementomori_boi/rss" 
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Check if the Webhook URL exists
if not WEBHOOK_URL:
    print("ERROR: DISCORD_WEBHOOK_URL is missing from GitHub Secrets.")
    sys.exit(1)

WANT = ["maintenance", "メンテナンス", "メンテ", "character", "新登場", "ラメント", "復刻", "event", "イベント", "開催", "anniversary", "周年", "記念", "キャンペーン"]
IGNORE = ["live", "生放送", "YouTube", "grand battle", "グランドバトル", "グラバト", "guild battle", "ギルドバトル", "ギルバト", "version update", "アップデート", "Ver."]

# --- THE LOGIC ---
try:
    print(f"Connecting to feed: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)

    if not feed.entries:
        print("The RSS feed is empty. Twitter might be blocking this instance.")
        # Sending a message to Discord so you know the script ran but failed to find tweets
        requests.post(WEBHOOK_URL, json={"content": "⚠️ Script ran, but the RSS feed was empty. Twitter is likely blocking the link."})
    else:
        for entry in feed.entries[:5]:
            text = entry.title.lower()
            if any(x.lower() in text for x in IGNORE):
                continue
            if any(x.lower() in text for x in WANT):
                requests.post(WEBHOOK_URL, json={"content": f"**MementoMori News Found:**\n{entry.link}"})
                
except Exception as e:
    print(f"An error occurred: {e}")
    sys.exit(1)
