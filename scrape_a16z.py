import requests
import re
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"
URL = "https://a16z.com/investment-list/"

def scrape_a16z():
    print("Fetching a16z investment list...")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
    }
    res = requests.get(URL, headers=headers)
    
    if res.status_code != 200:
        print(f"Failed to fetch a16z page: {res.status_code}")
        return

    # Use regex to find list items in the HTML
    # Typically, the list is in a <ul> or <ol> with <li> elements
    # Since the page is simple, let's look for <div class="entry-content"> or similar and extract <li>
    # Actually, a safer regex for this specific page structure:
    matches = re.findall(r'<li>(.*?)</li>', res.text, re.IGNORECASE)
    
    # Clean up the matches to get text
    companies = []
    for match in matches:
        # Remove any inner HTML tags (like <a> tags)
        clean_text = re.sub(r'<[^>]+>', '', match).strip()
        # Filter out anything that's clearly not a company name from the list
        if clean_text and len(clean_text) < 50 and not clean_text.startswith("http"):
            companies.append(clean_text)
            
    # The first few matches might be navigation links, but a16z usually puts the main list in a specific block.
    # We will just insert them all as they look like mostly companies in the list.
    # To be safe, remove known navigation items if they exist
    exclude = ['Portfolio', 'Team', 'AI', 'American Dynamism', 'Bio + Health', 'Consumer', 'Crypto', 
               'Cultural Leadership Fund', 'Enterprise', 'Fintech', 'Growth', 'Infrastructure', 
               'Perennial', 'Speedrun', 'News & Content', 'Terms of Use', 'Privacy Policy', 
               'Disclosures', 'Sitemap', '0x']
    
    final_companies = [c for c in set(companies) if c not in exclude and len(c) > 1]
    
    print(f"Extracted {len(final_companies)} a16z companies.")
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    for company in final_companies:
        record = {
            'date': today, # We don't have the exact date they were funded
            'company': company,
            'sector': 'Unknown',
            'description': 'a16z Portfolio Company',
            'location': 'Unknown',
            'stage': 'Unknown',
            'amount': 'N/A',
            'lead_notable_investors': 'Andreessen Horowitz',
            'source': 'a16z'
        }
        records.append(record)
        
    df = pd.DataFrame(records)
    
    conn = sqlite3.connect(DB_NAME)
    df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
    conn.close()
    
    print(f"Successfully inserted {len(df)} a16z startups into the database.")

if __name__ == "__main__":
    scrape_a16z()
