import sqlite3
import pandas as pd

DB_NAME = "startups.db"
TABLE_NAME = "startups"

def cleanup():
    conn = sqlite3.connect(DB_NAME)
    
    # Read the data
    df = pd.read_sql(f"SELECT rowid, * FROM {TABLE_NAME}", conn)
    
    # Fix the sector and location for Speedrun companies
    for idx, row in df.iterrows():
        if row['source'] == 'a16z Speedrun':
            sector = str(row['sector'])
            location = str(row['location'])
            
            # If sector starts with a comma and a state (e.g. ", California, AI, B2B")
            if sector.startswith(", "):
                parts = sector.split(", ")
                # The first element is empty string (because of ", ")
                # The second element is the state e.g. "California"
                if len(parts) >= 2:
                    state = parts[1]
                    # Update location
                    new_location = f"{location}, {state}"
                    # Update sector
                    new_sector = ", ".join(parts[2:])
                    
                    df.at[idx, 'location'] = new_location
                    df.at[idx, 'sector'] = new_sector

    # Extract Country
    def get_country(loc):
        if not loc or pd.isna(loc) or loc == 'Unknown':
            return 'Unknown'
        loc_str = str(loc).strip()
        parts = [p.strip() for p in loc_str.split(',')]
        last_part = parts[-1].upper()
        
        usa_identifiers = ['USA', 'UNITED STATES', 'CA', 'CALIFORNIA', 'NY', 'NEW YORK', 
                           'TX', 'TEXAS', 'WA', 'WASHINGTON', 'MA', 'MASSACHUSETTS', 
                           'IL', 'ILLINOIS', 'CO', 'COLORADO', 'FL', 'FLORIDA', 'UT', 'UTAH']
        
        if last_part in usa_identifiers or 'USA' in loc_str.upper():
            return 'USA'
        
        # If it's something like "London, UK", return "UK"
        return parts[-1]

    df['country'] = df['location'].apply(get_country)

    # Sort so rows with non-empty descriptions and websites come first
    df['has_web'] = df['website'].apply(lambda x: 1 if x and str(x).strip() not in ['', 'None', 'nan'] else 0)
    df['has_desc'] = df['description'].apply(lambda x: 1 if x and 'Portfolio Company' not in str(x) and str(x) not in ['Unknown', ''] else 0)
    
    df = df.sort_values(by=['has_web', 'has_desc', 'date'], ascending=[False, False, False])
    
    # Deduplicate by company and source
    initial_len = len(df)
    df = df.drop_duplicates(subset=['company', 'source'], keep='first')
    df = df.drop(columns=['rowid', 'has_web', 'has_desc'], errors='ignore')
    
    print(f"Deduplicated database: reduced from {initial_len} to {len(df)} unique startup records.")

    # Re-save to DB
    df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
    
    conn.close()
    print("Database cleaned and 'country' column added.")

if __name__ == "__main__":
    cleanup()
