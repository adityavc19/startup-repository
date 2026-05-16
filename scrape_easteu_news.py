import sqlite3
import pandas as pd
from datetime import datetime
import feedparser
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# We use Google News RSS to safely aggregate from these specific Eastern European domains
RSS_URL = "https://news.google.com/rss/search?q=funding+raises+OR+secures+site:ewdn.com+OR+site:ain.capital&hl=en-US&gl=US&ceid=US:en"

HEADLINE_VERBS = re.compile(
    r'\b(Mulls|Receives|Raises|Acquires|Shuts|Launches|Secures|Bags|Closes|'
    r'Lands|Eyes|Gets|Funds|Plans|Files|Says|Reports|IPO|Picks\s+Up|To\s+Raise)\b',
    re.IGNORECASE
)

def is_valid_company(name):
    """Return False if the name looks like a news headline rather than a company name."""
    if not name or len(name) < 2 or len(name) > 60:
        return False
    if HEADLINE_VERBS.search(name):
        return False
    # Reject truncated names (ending in common article words)
    if name.lower().endswith(("'s", " the", " a", " an")):
        return False
    return True

def extract_info(title):
    # Remove publisher suffix
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
        
    company = "Unknown"
    amount = "N/A"
    country = "Unknown"
    
    # Simple country heuristic based on mentions in the title
    title_lower = title.lower()
    if "russia" in title_lower or "moscow" in title_lower:
        country = "Russia"
    elif "ukraine" in title_lower or "kyiv" in title_lower:
        country = "Ukraine"
    elif "poland" in title_lower or "warsaw" in title_lower:
        country = "Poland"
    elif "estonia" in title_lower or "tallinn" in title_lower:
        country = "Estonia"
    elif "romania" in title_lower or "bucharest" in title_lower:
        country = "Romania"
    
    # Heuristic: Extract Amount
    amount_match = re.search(r'(\$|€|£)\s*[\d\.]+\s*(Cr|Crore|Mn|M|Million|Billion|K|Lakh|b)?', title, re.IGNORECASE)
    if amount_match:
        amount = amount_match.group(0)
        
    # Clean up prefixes
    clean_title = re.sub(r'^(Russia\'s|Ukraine\'s|Poland\'s|Estonia\'s|Romania\'s)\s+', '', title, flags=re.IGNORECASE)
    clean_title = re.sub(r'^.*?-\s*based\s+', '', clean_title, flags=re.IGNORECASE)
    clean_title = re.sub(r'^.*?-\s*founded\s+', '', clean_title, flags=re.IGNORECASE)
    
    company_match = re.search(r'^(.*?)\s+(Raises|Secures|Bags|Gets|Closes|Picks up|Lands|To Raise)', clean_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        # Clean up long prefixes like "Platform X"
        prefixes = ['Startup', 'Platform', 'Marketplace', 'Firm', 'Maker', 'Service']
        for p in prefixes:
            if p in company:
                company = company.split(p)[-1].strip()
    
    if company == "Unknown" or not company:
        # Fallback to first few words
        company = " ".join(clean_title.split()[:2])
        
    return company, amount, title, country

def scrape_easteu_news():
    print("Fetching latest Eastern European startup funding news...")
    feed = feedparser.parse(RSS_URL)
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        # Determine source
        source = "Eastern Europe News"
        if "ewdn" in title.lower() or "ewdn.com" in link:
            source = "EWDN"
        elif "ain" in title.lower() or "ain.capital" in link:
            source = "AIN.Capital"
            
        company, amount, description, country = extract_info(title)
        
        if is_valid_company(company):
            record = {
                'date': today,
                'company': company,
                'sector': 'Unknown',
                'description': description,
                'location': country,
                'stage': 'Unknown',
                'amount': amount,
                'country': country,
                'source': source
            }
            records.append(record)
        
    if not records:
        print("No Eastern European news found.")
        return
        
    print(f"Extracted {len(records)} latest funding updates.")
    
    df = pd.DataFrame(records)
    conn = sqlite3.connect(DB_NAME)
    
    # Avoid inserting duplicates by checking descriptions
    existing = pd.read_sql(f"SELECT description FROM {TABLE_NAME}", conn)['description'].tolist()
    df = df[~df['description'].isin(existing)]
    
    if len(df) > 0:
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print(f"Successfully inserted {len(df)} new Eastern European startups into the database.")
    else:
        print("No new updates to insert (all were already in the database).")
        
    conn.close()

if __name__ == "__main__":
    scrape_easteu_news()
