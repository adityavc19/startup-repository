import sqlite3
import pandas as pd
from datetime import datetime
import feedparser
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# We use Google News RSS to safely aggregate from these specific APAC domains
RSS_URL = "https://news.google.com/rss/search?q=funding+raises+OR+secures+site:thebridge.jp+OR+site:technode.com+OR+site:koreatechdesk.com+OR+site:techinasia.com+OR+site:kr-asia.com+OR+site:e27.co+OR+site:dealstreetasia.com&hl=en-US&gl=US&ceid=US:en"

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
    # Remove publisher suffix (e.g. " - DealStreetAsia")
    if " - " in title:
        title = title.rsplit(" - ", 1)[0]
        
    company = "Unknown"
    amount = "N/A"
    country = "Unknown"
    
    # Simple country heuristic based on mentions in the title
    title_lower = title.lower()
    if "japan" in title_lower or "tokyo" in title_lower or "yen" in title_lower or "¥" in title_lower:
        country = "Japan"
    elif "korea" in title_lower or "seoul" in title_lower or "won" in title_lower or "₩" in title_lower:
        country = "South Korea"
    elif "china" in title_lower or "beijing" in title_lower or "shanghai" in title_lower or "rmb" in title_lower or "yuan" in title_lower:
        country = "China"
    elif "singapore" in title_lower:
        country = "Singapore"
    elif "indonesia" in title_lower or "jakarta" in title_lower:
        country = "Indonesia"
    elif "vietnam" in title_lower:
        country = "Vietnam"
    elif "india" in title_lower:
        country = "India"
    
    # Heuristic: Extract Amount (looks for $, ¥, ₩, RMB, etc.)
    amount_match = re.search(r'(\$|¥|₩|RMB|€|£)\s*[\d\.]+\s*(Cr|Crore|Mn|M|Million|Billion|K|Lakh|b)?', title, re.IGNORECASE)
    if amount_match:
        amount = amount_match.group(0)
        
    # Heuristic: Extract Company (looks for text before keywords like "Raises", "Secures")
    # Sometimes it says "Vietnam's XYZ raises" or "Singapore-based XYZ secures"
    # Clean up prefixes
    clean_title = re.sub(r'^(Japan\'s|Korea\'s|China\'s|Singapore\'s|Vietnam\'s|Indonesia\'s|India\'s)\s+', '', title, flags=re.IGNORECASE)
    clean_title = re.sub(r'^.*?-\s*based\s+', '', clean_title, flags=re.IGNORECASE)
    
    company_match = re.search(r'^(.*?)\s+(Raises|Secures|Bags|Gets|Closes|Picks up|Lands|To Raise)', clean_title, re.IGNORECASE)
    if company_match:
        company = company_match.group(1).strip()
        # Clean up long prefixes like "Platform X"
        prefixes = ['Startup', 'Platform', 'Marketplace', 'Firm', 'Maker']
        for p in prefixes:
            if p in company:
                company = company.split(p)[-1].strip()
    
    if company == "Unknown" or not company:
        # Fallback to first few words
        company = " ".join(clean_title.split()[:2])
        
    return company, amount, title, country

def scrape_apac_news():
    print("Fetching latest APAC startup funding news...")
    feed = feedparser.parse(RSS_URL)
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        
        # Determine source
        source = "APAC News"
        if "thebridge" in title.lower() or "thebridge.jp" in link:
            source = "The Bridge"
        elif "technode" in title.lower() or "technode.com" in link:
            source = "TechNode"
        elif "koreatechdesk" in title.lower() or "koreatechdesk.com" in link:
            source = "KoreaTechDesk"
        elif "techinasia" in title.lower() or "techinasia.com" in link:
            source = "Tech in Asia"
        elif "kr-asia" in title.lower() or "kr-asia.com" in link:
            source = "KrASIA"
        elif "e27" in title.lower() or "e27.co" in link:
            source = "e27"
        elif "dealstreetasia" in title.lower() or "dealstreetasia.com" in link:
            source = "DealStreetAsia"
            
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
        print("No APAC news found.")
        return
        
    print(f"Extracted {len(records)} latest funding updates.")
    
    df = pd.DataFrame(records)
    conn = sqlite3.connect(DB_NAME)
    
    # Avoid inserting duplicates by checking descriptions
    existing = pd.read_sql(f"SELECT description FROM {TABLE_NAME}", conn)['description'].tolist()
    df = df[~df['description'].isin(existing)]
    
    if len(df) > 0:
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print(f"Successfully inserted {len(df)} new APAC startups into the database.")
    else:
        print("No new updates to insert (all were already in the database).")
        
    conn.close()

if __name__ == "__main__":
    scrape_apac_news()
