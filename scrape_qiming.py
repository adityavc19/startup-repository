import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"
URL = "https://www.qimingvc.com/en/portfolio"

def scrape_qiming():
    print("Fetching Qiming Venture Partners investment list...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    
    try:
        res = requests.get(URL, headers=headers, timeout=30)
        res.raise_for_status()
    except Exception as e:
        print(f"Failed to fetch Qiming page: {e}")
        return

    soup = BeautifulSoup(res.text, 'html.parser')
    
    companies = []
    # Qiming puts company names in tags with class containing 'txt', 'name', or 'title'
    for tag in soup.find_all(['h3', 'h4', 'div', 'span', 'p']):
        class_str = ' '.join(tag.get('class', [])).lower()
        if 'name' in class_str or 'title' in class_str or 'txt' in class_str:
            name = tag.get_text(strip=True)
            if name and len(name) < 40 and name not in companies:
                # filter out obvious non-companies
                if name.lower() not in ['technology', 'healthcare', 'consumer', 'portfolio', 'about', 'news']:
                    companies.append(name)
            
    if not companies:
        print("No companies found on Qiming portfolio page.")
        return
        
    print(f"Extracted {len(companies)} Qiming portfolio companies.")
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    for company in companies:
        record = {
            'date': today,
            'company': company,
            'sector': 'Unknown',
            'description': 'Qiming Venture Partners Portfolio Company',
            'location': 'China / APAC',
            'stage': 'Unknown',
            'amount': 'N/A',
            'lead_notable_investors': 'Qiming Venture Partners',
            'source': 'Qiming',
            'country': 'China'
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    conn = sqlite3.connect(DB_NAME)
    
    # Avoid duplicates by company name and source
    existing = pd.read_sql(f"SELECT company FROM {TABLE_NAME} WHERE source='Qiming'", conn)['company'].tolist()
    df = df[~df['company'].isin(existing)]
    
    if len(df) > 0:
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print(f"Successfully inserted {len(df)} new Qiming startups into the database.")
    else:
        print("No new updates to insert (all were already in the database).")
        
    conn.close()

if __name__ == "__main__":
    scrape_qiming()
