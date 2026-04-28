import sqlite3
import pandas as pd
from datetime import datetime
import feedparser
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# We use Google News RSS to safely aggregate from these specific domains without getting blocked by Cloudflare
RSS_URL = "https://news.google.com/rss/search?q=funding+raises+OR+secures+site:entrackr.com+OR+site:inc42.com+OR+site:yourstory.com&hl=en-IN&gl=IN&ceid=IN:en"

def extract_info(title):
    # Remove publisher suffix (e.g. " - Inc42")
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
        
    company = "Unknown"
    amount = "N/A"
    
    # Heuristic: Extract Amount (looks for $, ₹, Cr, Mn, etc.)
    amount_match = re.search(r'(\$|₹|INR|Rs\.?)\s*[\d\.]+\s*(Cr|Crore|Mn|M|Million|Billion|K|Lakh)?', title, re.IGNORECASE)
    if amount_match:
        amount = amount_match.group(0)
        
    # Heuristic: Extract Company (looks for text before keywords like "Raises", "Secures")
    company_match = re.search(r'^(.*?)\s+(Raises|Secures|Bags|Gets|Closes|Picks up|Lands|To Raise)', title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        # Clean up long prefixes like "Bengaluru-based SaaS Startup X"
        prefixes = ['Startup', 'Platform', 'Marketplace', 'Firm', 'Maker']
        for p in prefixes:
            if p in company:
                company = company.split(p)[-1].strip()
    
    if company == "Unknown" or not company:
        # Fallback to first few words
        company = " ".join(title.split()[:2])
        
    return company, amount, title

def scrape_indian_news():
    print("Fetching latest Indian startup funding news...")
    feed = feedparser.parse(RSS_URL)
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        # Determine source
        source = "Indian News"
        if "entrackr" in title.lower() or "entrackr.com" in link:
            source = "Entrackr"
        elif "inc42" in title.lower() or "inc42.com" in link:
            source = "Inc42"
        elif "yourstory" in title.lower() or "yourstory.com" in link:
            source = "YourStory"
            
        company, amount, description = extract_info(title)
        
        record = {
            'date': today,
            'company': company,
            'sector': 'Unknown',
            'description': description,
            'location': 'India',
            'stage': 'Unknown',
            'amount': amount,
            'country': 'India',
            'source': source
        }
        records.append(record)
        
    if not records:
        print("No news found.")
        return
        
    print(f"Extracted {len(records)} latest funding updates.")
    
    df = pd.DataFrame(records)
    conn = sqlite3.connect(DB_NAME)
    
    # Avoid inserting duplicates by checking descriptions
    existing = pd.read_sql(f"SELECT description FROM {TABLE_NAME}", conn)['description'].tolist()
    df = df[~df['description'].isin(existing)]
    
    if len(df) > 0:
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print(f"Successfully inserted {len(df)} new Indian startups into the database.")
    else:
        print("No new updates to insert (all were already in the database).")
        
    conn.close()

if __name__ == "__main__":
    scrape_indian_news()
