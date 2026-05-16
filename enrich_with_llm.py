"""
One-time script to enrich the database using a local LLM server.
It will run through startups with 'Unknown' sectors and attempt to classify them,
and can also be used to re-extract company names from article descriptions if needed.
"""
import sqlite3
import time
from llm_parser import standardize_sector

DB_NAME = "startups.db"
TABLE_NAME = "startups"

def main():
    print("=" * 60)
    print("LLM Sector Standardization")
    print("=" * 60)
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Get startups that have 'Unknown' as their sector but have a description
    rows = cursor.execute(
        f"SELECT rowid, company, description FROM {TABLE_NAME} WHERE sector = 'Unknown' AND description != '' LIMIT 50"
    ).fetchall()
    
    if not rows:
        print("No startups found needing sector standardization.")
        return
        
    print(f"Found {len(rows)} startups to classify. Using local LLM...\n")
    
    updated = 0
    for i, (rowid, company, desc) in enumerate(rows):
        print(f"[{i+1}/{len(rows)}] Classifying '{company}'...", end=" ", flush=True)
        
        sector = standardize_sector(desc)
        
        if sector and sector != "Unknown":
            cursor.execute(
                f"UPDATE {TABLE_NAME} SET sector = ? WHERE rowid = ?",
                (sector, rowid)
            )
            conn.commit()
            updated += 1
            print(f"✅ {sector}")
        else:
            print("❌ Could not classify")
            
        time.sleep(0.5) # Slight pause
        
    conn.close()
    print(f"\n{'=' * 60}")
    print(f"Done! Standardized sectors for {updated} startups.")

if __name__ == "__main__":
    main()
