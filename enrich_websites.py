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
    """Search DuckDuckGo for a startup's website."""
    headers = {"User-Agent": "Mozilla/5.0"}
    query = f"{company_name} startup official website"
    url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}"

    try:
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.find_all("a", class_="result__a")

        for result in results[:5]:
            href = result.get("href", "")
            # Extract actual URL from DuckDuckGo redirect
            if "uddg=" in href:
                from urllib.parse import unquote, parse_qs, urlparse
                parsed = urlparse(href)
                params = parse_qs(parsed.query)
                if "uddg" in params:
                    href = unquote(params["uddg"][0])

            # Skip noise sites
            skip_domains = [
                "linkedin.com", "twitter.com", "x.com", "facebook.com",
                "crunchbase.com", "pitchbook.com", "tracxn.com",
                "wikipedia.org", "youtube.com", "github.com",
                "medium.com", "techcrunch.com", "bloomberg.com",
                "reuters.com", "forbes.com", "substack.com",
                "google.com", "bing.com", "duckduckgo.com",
                "angellist.com", "wellfound.com",
            ]

            if href.startswith("http") and not any(d in href.lower() for d in skip_domains):
                # Clean URL to just the domain
                from urllib.parse import urlparse as up
                parsed = up(href)
                clean = f"{parsed.scheme}://{parsed.netloc}"
                return clean

    except Exception as e:
        print(f"    Error searching: {e}")

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
