import sqlite3
import pandas as pd
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# A proper taxonomy hierarchy and their associated keywords
TAXONOMY_MAP = {
    "Artificial Intelligence": ["AI", "ML", "Artificial Intelligence", "Machine Learning", "LLM", "Generative", "Data"],
    "Fintech & Finance": ["Fintech", "Finance", "Bank", "Payments", "Wealth", "Insurtech", "Insurance", "Credit"],
    "Healthcare & Biotech": ["Health", "Bio", "Medtech", "Pharma", "Care", "Therapeutics", "Diagnostics", "Medical", "Wellness"],
    "Crypto & Web3": ["Crypto", "Web3", "Blockchain", "DeFi", "NFT", "Bitcoin", "Ethereum", "Token"],
    "Security & Defense": ["Security", "Cyber", "Defense", "Military", "Privacy", "Compliance"],
    "Climate & Energy": ["Climate", "Energy", "Clean", "Sustainability", "Carbon", "Solar", "Green"],
    "DeepTech & Hardware": ["Deep Tech", "Hardware", "Robotics", "Semiconductor", "Space", "Aerospace", "Quantum", "Material"],
    "Developer Tools": ["DevTools", "Developer", "Infrastructure", "API", "Cloud", "Database", "Open Source", "Platform"],
    "Media & Gaming": ["Media", "Gaming", "Games", "Creator", "Entertainment", "Video", "Audio", "Music"],
    "E-commerce & Retail": ["E-commerce", "Retail", "Marketplace", "D2C", "Consumer Goods", "Shopping"],
    "Education": ["Education", "Edtech", "Learning", "Student", "School"],
    "Logistics & PropTech": ["Logistics", "Supply", "PropTech", "Real Estate", "Mobility", "Transport", "Travel"],
    "Enterprise Software & B2B": ["Enterprise", "B2B", "SaaS", "Software", "Workforce", "HR", "Productivity", "Sales", "Marketing"],
    "Consumer & Social": ["Consumer", "Social", "Community", "Network", "Dating", "App"]
}

def map_taxonomy(sector_str, description_str):
    text_to_search = str(sector_str).lower() + " " + str(description_str).lower()
    
    # Check if sector is completely unknown
    if sector_str == 'Unknown' and description_str == 'Unknown':
        return 'Other'
        
    for category, keywords in TAXONOMY_MAP.items():
        for kw in keywords:
            # Word boundary regex to ensure we match whole words (e.g. "AI" not "AIR")
            # except for some keywords where partial is fine
            if kw == "AI" or kw == "ML" or kw == "HR":
                pattern = r'\b' + kw.lower() + r'\b'
                if re.search(pattern, text_to_search):
                    return category
            else:
                if kw.lower() in text_to_search:
                    return category
                    
    # If it falls through, but the original sector wasn't "Unknown", we try to keep the first word of the original sector as a fallback
    # or just group it into "Other"
    
    if sector_str and sector_str != 'Unknown':
        # If it's a comma separated list, take the first item
        first_tag = str(sector_str).split(',')[0].strip()
        if len(first_tag) > 3 and len(first_tag) < 20:
            # Capitalize properly
            return first_tag.title()
            
    return "Other / Technology"

def apply_taxonomy():
    print("Applying proper taxonomy to sectors...")
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql(f"SELECT * FROM {TABLE_NAME}", conn)
    
    # We will keep the original sector data in 'tags' column, and replace 'sector'
    # Check if 'tags' column exists
    if 'tags' not in df.columns:
        df['tags'] = df['sector']
        
    # Apply mapping
    df['sector'] = df.apply(lambda row: map_taxonomy(row['tags'], row['description']), axis=1)
    
    # Save back to DB
    df.to_sql(TABLE_NAME, conn, if_exists='replace', index=False)
    conn.close()
    
    unique_sectors = df['sector'].nunique()
    print(f"Taxonomy applied successfully. Reduced to {unique_sectors} clean categories.")

if __name__ == "__main__":
    apply_taxonomy()
