import pandas as pd
import sqlite3
import os

DB_NAME = "startups.db"
TABLE_NAME = "startups"

files_to_ingest = [
    {"path": "../Venture_Daily_Digest_Fundraises_March_2026.xlsx", "year": "2026", "month": "Mar"},
    {"path": "../Venture_Daily_Digest_Fundraises_April_2026.xlsx", "year": "2026", "month": "Apr"}
]

def clean_and_ingest():
    conn = sqlite3.connect(DB_NAME)
    
    all_data = []
    
    for file_info in files_to_ingest:
        if os.path.exists(file_info["path"]):
            print(f"Reading {file_info['path']}...")
            df = pd.read_excel(file_info["path"])
            
            # Add Source
            df['Source'] = "Daily Digest"
            
            # Clean Date (e.g. "Apr 1" -> "2026-04-01")
            # We append the year and parse it.
            # Handle potential NaN in Date
            df['Date'] = df['Date'].astype(str) + f" {file_info['year']}"
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce').dt.strftime('%Y-%m-%d')
            
            # Standardize Column Names to snake_case for DB
            df.columns = [c.lower().replace(' / ', '_').replace(' ', '_') for c in df.columns]
            
            # Standardize "amount" if possible (optional, keeping as string for now to preserve "$2M" format)
            
            all_data.append(df)
        else:
            print(f"File not found: {file_info['path']}")
            
    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # Drop duplicates based on company name and date
        final_df = final_df.drop_duplicates(subset=['company', 'date'])
        
        print(f"Total rows to ingest: {len(final_df)}")
        
        # Save to SQLite
        final_df.to_sql(TABLE_NAME, conn, if_exists='append', index=False)
        print("Data successfully ingested into SQLite database.")
        
    conn.close()

if __name__ == "__main__":
    clean_and_ingest()
