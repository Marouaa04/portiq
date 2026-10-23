import json
import os
import time
import sys
sys.path.insert(0, "port_optimizer")

from scraper import scrape_all_news

SAVE_FILE = "headlines_raw.json"

# Load existing headlines
if os.path.exists(SAVE_FILE):
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        existing = json.load(f)
else:
    existing = []

# Build set of already-seen titles
seen_titles = set(h["title"] for h in existing)

# Scrape new ones
print(f"Scraping... (already have {len(existing)} headlines)")
new_headlines = scrape_all_news()

# Add only new ones
added = 0
for h in new_headlines:
    if h["title"] not in seen_titles:
        existing.append(h)
        seen_titles.add(h["title"])
        added += 1

# Save back
with open(SAVE_FILE, "w", encoding="utf-8") as f:
    json.dump(existing, f, ensure_ascii=False, indent=2)

print(f"Added {added} new headlines. Total now: {len(existing)}")