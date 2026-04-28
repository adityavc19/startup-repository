import sqlite3
import time
import requests
from bs4 import BeautifulSoup

DB_NAME = "startups.db"
TABLE_NAME = "startups"

def enrich_unknowns(limit=50):
    print(f"Starting web search enrichment process for up to {limit} unknown companies...")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # We select companies where description starts with "a16z Portfolio" or is "Unknown"
    cursor.execute(f"SELECT rowid, company FROM {TABLE_NAME} WHERE description LIKE '%a16z Portfolio%' OR description = 'Unknown' LIMIT ?", (limit,))
    rows = cursor.fetchall()
    
    if not rows:
        print("No unknown companies found!")
        return
        
    print(f"Found {len(rows)} companies to enrich in this batch.")
    
    updated_count = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for rowid, company in rows:
        print(f"Searching the web for: {company}...")
        try:
            # We use DuckDuckGo's HTML version as a proxy for web search (since Google blocks automated scraping)
            query = f"{company} startup"
            res = requests.get(f'https://html.duckduckgo.com/html/?q={query}', headers=headers)
            
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                snippets = soup.find_all('a', class_='result__snippet')
                
                if snippets:
                    summary = snippets[0].text.strip()
                    cursor.execute(
                        f"UPDATE {TABLE_NAME} SET description = ? WHERE rowid = ?", 
                        (summary, rowid)
                    )
                    updated_count += 1
                    print(f"  -> Found: {summary[:80]}...")
                else:
                    print("  -> No snippets found.")
            else:
                print(f"  -> Web search returned status {res.status_code}")
                
        except Exception as e:
            print(f"  -> Error: {e}")
            
        # Sleep to avoid rate limiting from the search engine
        time.sleep(2.0)
            
    conn.commit()
    conn.close()
    
    print(f"Enrichment complete. Successfully enriched {updated_count} startups.")
    print("Run this script again to process the next batch!")

if __name__ == "__main__":
    enrich_unknowns()
