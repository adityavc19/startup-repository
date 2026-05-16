"""
Enrich consumer startups with website URLs using DuckDuckGo search.
"""

import sqlite3
import time
import requests
from bs4 import BeautifulSoup
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# Consumer filter (same logic as app.py)
CONSUMER_SECTORS = [
    "Consumer & Social", "Media & Gaming", "E-Commerce & Retail",
    "E-commerce & Retail", "Education", "Agtech / Foodtech",
    "Food Tech", "Agtech",
]
CONSUMER_SECTOR_KW = [
    "SOCIAL", "GAMES", "GAMING", "FITNESS", "DATING", "CREATIVE",
    "EDTECH", "MEDIA", "ANIMATION",
]
CONSUMER_DESC_KW = [
    "consumer", "wellness", "gaming", "social", "mobile app",
    "beauty", "fashion", "food", "travel", "entertainment",
    "lifestyle", "fitness", "dating", "music", "sports", "beer",
    "diaper", "jewelry", "greeting card", "pet", "kids",
    "personal", "wearable",
]


def is_consumer(row):
    sector = str(row[0] or "")
    tags = str(row[1] or "").lower()
    desc = str(row[2] or "").lower()

    if sector in CONSUMER_SECTORS:
        return True
    if any(kw in sector.upper() for kw in CONSUMER_SECTOR_KW):
        return True
    if "consumer" in tags:
        return True
    if any(kw in desc for kw in CONSUMER_DESC_KW):
        return True
    return False


def search_website(company_name):
    """Search Clearbit API for a startup's official website."""
    # Clean up the company name for better search results
    search_term = company_name.split('-')[0].split('|')[0].strip()
    
    url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={requests.utils.quote(search_term)}"
    
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                domain = data[0].get('domain')
                if domain:
                    return f"https://{domain}"
                    
    except Exception as e:
        print(f"    Error searching Clearbit: {e}")

    return ""


def main():
    print("=" * 60)
    print("Consumer Startup Website Enrichment")
    print("=" * 60)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Get all startups that might be consumer
    rows = cursor.execute(
        f"SELECT rowid, company, sector, tags, description, website FROM {TABLE_NAME}"
    ).fetchall()

    consumer_rows = []
    for row in rows:
        rowid, company, sector, tags, desc, website = row
        if is_consumer((sector, tags, desc)):
            if not website or website.strip() == "":
                consumer_rows.append((rowid, company))

    print(f"\nFound {len(consumer_rows)} consumer startups without websites")
    print(f"Starting website lookup...\n")

    updated = 0
    for i, (rowid, company) in enumerate(consumer_rows):
        print(f"[{i+1}/{len(consumer_rows)}] {company}...", end=" ", flush=True)

        website = search_website(company)
        if website:
            cursor.execute(
                f"UPDATE {TABLE_NAME} SET website = ? WHERE rowid = ?",
                (website, rowid)
            )
            conn.commit()
            updated += 1
            print(f"✅ {website}")
        else:
            print("❌ not found")

        # Rate limit to avoid getting blocked
        time.sleep(1.5)

    conn.close()
    print(f"\n{'=' * 60}")
    print(f"Done! Updated {updated}/{len(consumer_rows)} consumer startups with websites.")


if __name__ == "__main__":
    main()
