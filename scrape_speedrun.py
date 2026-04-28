import requests
from bs4 import BeautifulSoup
import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "startups.db"
TABLE_NAME = "startups"
URL = "https://speedrun.a16z.com/companies"

def scrape_speedrun():
    print("Fetching a16z Speedrun companies...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(URL, headers=headers)
    
    if res.status_code != 200:
        print("Failed to fetch")
        return
        
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # The companies are listed in cards (usually <a> tags with specific classes, or just looking for 'COHORT')
    # Let's find all elements that contain 'COHORT'
    links = soup.find_all('a', href=lambda x: x and '/companies/' in x)
    
    records = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    # We will use a set to avoid duplicates since a card might have multiple links
    seen = set()
    
    for link in links:
        text = link.get_text(separator='|', strip=True)
        if not text or text in seen:
            continue
            
        parts = text.split('|')
        
        # Example format: COHORT|006|Acceler8|15 Employees|Located in|San Francisco, California|AI|B2B|AI for Workforce Intelligence & Planning...
        
        if len(parts) > 5 and 'COHORT' in parts[0]:
            seen.add(text)
            
            # The structure varies slightly depending on tags, but generally:
            # 0: COHORT
            # 1: 006
            # 2: Company Name
            company = parts[2]
            
            # Location is usually after "Located in"
            location = "Unknown"
            if "Located in" in parts:
                loc_idx = parts.index("Located in")
                if loc_idx + 1 < len(parts):
                    location = parts[loc_idx + 1]
                    
            # Description is usually the last part
            description = parts[-1]
            
            # Tags/Sector are between location and description
            sector = "Technology"
            if "Located in" in parts:
                loc_idx = parts.index("Located in")
                tags = parts[loc_idx + 2 : -1]
                if tags:
                    sector = ", ".join(tags)
                    
            record = {
                'date': today,
                'company': company,
                'sector': sector,
                'description': description,
                'location': location,
                'stage': 'Pre-Seed/Seed',
                'amount': 'N/A',
                'lead_notable_investors': 'a16z Speedrun',
                'source': 'a16z Speedrun'
            }
            records.append(record)
            
    print(f"Extracted {len(records)} Speedrun companies.")
    
    if records:
        df = pd.DataFrame(records)
        conn = sqlite3.connect(DB_NAME)
        
        # Remove these companies from the general 'a16z' source if they already exist so we don't have duplicates
        company_names = df['company'].tolist()
        placeholders = ','.join(['?'] * len(company_names))
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {TABLE_NAME} WHERE company IN ({placeholders}) AND source='a16z'", company_names)
        deleted = cursor.rowcount
        print(f"Removed {deleted} duplicate entries from the general a16z list.")
        
        df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        conn.close()
        print("Successfully inserted Speedrun startups into the database.")

if __name__ == "__main__":
    scrape_speedrun()
