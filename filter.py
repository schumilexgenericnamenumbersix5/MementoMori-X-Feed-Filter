import os
import requests
import feedparser

# --- SETTINGS ---
# Using a fresh Nitter instance - if this is empty, we must use RSS.app
RSS_URL = "https://nitter.net/mementomori_boi/rss" 
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

WANT = ["maintenance", "メンテナンス", "メンテ", "character", "新登場", "ラメント", "復刻", "event", "イベント", "開催", "anniversary", "周年", "記念", "キャンペーン"]
IGNORE = ["live", "生放送", "YouTube", "grand battle", "グランドバトル", "グラバト", "guild battle", "ギルドバトル", "ギルバト", "version update", "アップデート", "Ver."]

# --- THE LOGIC ---
# This line proves the connection works. If you don't see this, the Webhook Secret is wrong.
requests.post(WEBHOOK_URL, json={"content": "📢 Filter Script checking for news..."})

feed = feedparser.parse(RSS_URL)

if not feed.entries:
    print("CRITICAL: The RSS feed is empty! Twitter is blocking this URL.")
    requests.post(WEBHOOK_URL, json={"content": "⚠️ RSS Feed is currently blocked by Twitter. Need new URL."})
else:
    print(f"Checking {len(feed.entries)} tweets...")
    for entry in feed.entries[:5]:
        text = entry.title.lower()
        # Filter Logic
        if any(x.lower() in text for x in IGNORE):
            continue
        if any(x.lower() in text for x in WANT):
            requests.post(WEBHOOK_URL, json={"content": f"**MementoMori News:**\n{entry.link}"})
