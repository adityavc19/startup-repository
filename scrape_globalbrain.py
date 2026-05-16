import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"
URL = "https://globalbrains.com/en/portfolio"

def scrape_globalbrain():
    print("Fetching Global Brain investment list...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=15)
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch Global Brain page: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    
    companies = []
    for item in soup.find_all('p', class_='name'):
        name = item.get_text(strip=True)
        if name and len(name) < 60 and name not in companies:
            companies.append(name)
            
    if not companies:
        print("No companies found on Global Brain portfolio page.")
        return
        
    print(f"Extracted {len(companies)} Global Brain portfolio companies.")
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    for company in companies:
        record = {
            'date': today, # We don't have the exact date they were funded
            'company': company,
            'sector': 'Unknown',
            'description': 'Global Brain Portfolio Company',
            'location': 'Japan / APAC',
            'stage': 'Unknown',
            'amount': 'N/A',
            'lead_notable_investors': 'Global Brain',
            'source': 'Global Brain',
            'country': 'Japan'
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    conn = sqlite3.connect(DB_NAME)
    
    # Avoid duplicates by company name and source
    existing = pd.read_sql(f"SELECT company FROM {TABLE_NAME} WHERE source='Global Brain'", conn)['company'].tolist()
    df = df[~df['company'].isin(existing)]
    
    if len(df) > 0:
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print(f"Successfully inserted {len(df)} new Global Brain startups into the database.")
    else:
        print("No new updates to insert (all were already in the database).")
        
    conn.close()

if __name__ == "__main__":
    scrape_globalbrain()
