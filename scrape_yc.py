import requests
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# Algolia API details for Y Combinator
APP_ID = "45BWZJ1SGC"
API_KEY = "NzllNTY5MzJiZGM2OTY2ZTQwMDEzOTNhYWZiZGRjODlhYzVkNjBmOGRjNzJiMWM4ZTU0ZDlhYTZjOTJiMjlhMWFuYWx5dGljc1RhZ3M9eWNkYyZyZXN0cmljdEluZGljZXM9WUNDb21wYW55X3Byb2R1Y3Rpb24lMkNZQ0NvbXBhbnlfQnlfTGF1bmNoX0RhdGVfcHJvZHVjdGlvbiZ0YWdGaWx0ZXJzPSU1QiUyMnljZGNfcHVibGljJTIyJTVE"
URL = f"https://{APP_ID}-dsn.algolia.net/1/indexes/YCCompany_production/query"

HEADERS = {
    'X-Algolia-API-Key': API_KEY,
    'X-Algolia-Application-Id': APP_ID
}

def scrape_yc():
    print("Fetching companies from YC Algolia API...")
    all_hits = []
    
    # Fetch top 500 companies for demonstration to avoid long wait times
    for page in range(5):
        data = {'params': f'hitsPerPage=100&page={page}'}
        res = requests.post(URL, headers=HEADERS, json=data)
        
        if res.status_code == 200:
            hits = res.json().get('hits', [])
            if not hits:
                break
            all_hits.extend(hits)
        else:
            print(f"Error fetching page {page}: {res.status_code}")
            break
            
    print(f"Fetched {len(all_hits)} YC companies. Preparing data...")
    
    records = []
    CUTOFF = datetime(2025, 1, 1)
    for hit in all_hits:
        # Convert launched_at epoch to date string
        launched_date = None
        if hit.get('launched_at'):
            dt = datetime.fromtimestamp(hit['launched_at'])
            if dt < CUTOFF:
                continue  # Skip companies before 2025
            launched_date = dt.strftime('%Y-%m-%d')
            
        record = {
            'date': launched_date,
            'company': hit.get('name'),
            'sector': hit.get('industry', 'Technology'),
            'description': hit.get('one_liner', hit.get('long_description', '')[:200]),
            'location': hit.get('all_locations'),
            'stage': hit.get('stage', 'Seed'), # YC companies are typically seed/growth
            'amount': 'N/A', # YC funding not always public
            'lead_notable_investors': 'Y Combinator',
            'source': 'YC'
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    
    # Save to SQLite
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
    conn.close()
    
    print(f"Successfully inserted {len(df)} YC startups into the database.")

if __name__ == "__main__":
    scrape_yc()
