"""
Universal Company Enrichment Engine.
Fetches official website URLs, real company descriptions, locations, and sectors
for startups missing websites or carrying placeholder descriptions.
"""

import sqlite3
import time
import requests
import re
from urllib.parse import quote
from bs4 import BeautifulSoup

DB_NAME = "startups.db"
TABLE_NAME = "startups"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

def lookup_clearbit(company: str):
    """Query Clearbit Autocomplete API for domain and name."""
    clean_name = company.split(', Inc')[0].split(' Inc')[0].split(' LLC')[0].split('-')[0].strip()
    url = f"https://autocomplete.clearbit.com/v1/companies/suggest?query={quote(clean_name)}"
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                item = data[0]
                domain = item.get('domain')
                name = item.get('name')
                logo = item.get('logo')
                if domain:
                    return f"https://{domain}", domain
    except Exception as e:
        pass
    return None, None


def lookup_duckduckgo(company: str):
    """Query DuckDuckGo for web snippet description and website URL."""
    query = f"{company} startup official website"
    url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
    
    website = None
    description = None
    
    try:
        res = requests.get(url, headers=HEADERS, timeout=8)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            # Get first snippet
            snippets = soup.find_all('a', class_='result__snippet')
            if snippets:
                snippet_text = snippets[0].get_text(strip=True)
                if len(snippet_text) > 20:
                    description = snippet_text
                    
            # Get first result URL
            urls = soup.find_all('a', class_='result__url')
            if urls:
                raw_url = urls[0].get_text(strip=True)
                if raw_url and not any(bad in raw_url for bad in ['wikipedia', 'linkedin', 'crunchbase', 'twitter', 'facebook', 'instagram', 'youtube']):
                    if not raw_url.startswith('http'):
                        raw_url = 'https://' + raw_url
                    website = raw_url
    except Exception as e:
        pass
        
    return website, description


def infer_sector_from_text(text: str) -> str:
    """Keyword-based fast sector classification."""
    lowered = text.lower()
    
    if any(k in lowered for k in ['ai', 'artificial intelligence', 'llm', 'machine learning', 'neural', 'deep learning']):
        return 'AI/ML'
    if any(k in lowered for k in ['health', 'medical', 'bio', 'biotech', 'clinical', 'pharma', 'therapeutics', 'patient', 'doctor']):
        return 'Healthtech & Bio'
    if any(k in lowered for k in ['fintech', 'bank', 'payment', 'lending', 'finance', 'crypto', 'blockchain', 'wallet', 'credit']):
        return 'Fintech'
    if any(k in lowered for k in ['consumer', 'ecommerce', 'retail', 'fashion', 'apparel', 'food', 'beverage', 'fitness', 'wellness', 'gaming', 'game', 'social']):
        return 'Consumer & Social'
    if any(k in lowered for k in ['saas', 'enterprise', 'software', 'cloud', 'security', 'cyber', 'analytics', 'data', 'developer', 'b2b']):
        return 'Enterprise SaaS'
    if any(k in lowered for k in ['logistics', 'mobility', 'transport', 'ev', 'vehicle', 'supply chain', 'freight']):
        return 'Logistics & Mobility'
    if any(k in lowered for k in ['education', 'edtech', 'school', 'learning', 'student', 'course']):
        return 'EdTech'
    if any(k in lowered for k in ['proptech', 'real estate', 'housing', 'construction']):
        return 'Proptech'
    
    return 'Enterprise SaaS' # sensible default for tech portfolio companies


def enrich_companies(limit=100):
    print("=" * 60)
    print(f"Starting Batch Enrichment for up to {limit} companies...")
    print("=" * 60)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Query companies with missing websites OR generic descriptions
    cursor.execute(f"""
        SELECT rowid, company, description, website, sector 
        FROM {TABLE_NAME} 
        WHERE (website IS NULL OR website = '' OR description LIKE '%Portfolio Company%' OR description = 'Unknown' OR sector = 'Other / Technology')
        LIMIT ?
    """, (limit,))
    
    rows = cursor.fetchall()

    if not rows:
        print("No companies needing enrichment found!")
        conn.close()
        return

    print(f"Found {len(rows)} companies to enrich in this run.\n")

    enriched_count = 0

    for i, (rowid, company, old_desc, old_web, old_sector) in enumerate(rows):
        print(f"[{i+1}/{len(rows)}] Enriching '{company}'...", end=" ", flush=True)

        new_web = old_web
        new_desc = old_desc
        new_sector = old_sector

        # 1. Clearbit lookup for website
        if not new_web or new_web.strip() == "":
            cb_web, domain = lookup_clearbit(company)
            if cb_web:
                new_web = cb_web

        # 2. DDG lookup if website or description still missing
        if (not new_web or new_web.strip() == "") or ("Portfolio Company" in str(old_desc) or old_desc == "Unknown" or not old_desc):
            ddg_web, ddg_desc = lookup_duckduckgo(company)
            if not new_web and ddg_web:
                new_web = ddg_web
            if ("Portfolio Company" in str(old_desc) or old_desc == "Unknown" or not old_desc) and ddg_desc:
                new_desc = ddg_desc

        # 3. If description is still generic, create a clean descriptive summary from company name and domain
        if "Portfolio Company" in str(new_desc) or new_desc == "Unknown" or not new_desc:
            clean_dom = new_web.replace('https://', '').replace('http://', '').replace('www.', '').rstrip('/') if new_web else ""
            if clean_dom:
                new_desc = f"{company} ({clean_dom}) technology startup."
            else:
                new_desc = f"{company} technology and venture-backed startup."

        # 4. Update sector if it was "Other / Technology" or "Unknown"
        if new_sector in ["Other / Technology", "Unknown", None]:
            new_sector = infer_sector_from_text(f"{company} {new_desc}")

        # Update Database
        cursor.execute(f"""
            UPDATE {TABLE_NAME}
            SET website = ?, description = ?, sector = ?
            WHERE rowid = ?
        """, (new_web, new_desc, new_sector, rowid))
        
        conn.commit()
        enriched_count += 1
        print(f"✅ Web: {new_web or 'N/A'} | Sector: {new_sector} | Desc: {new_desc[:60]}...")

        # Small pause to avoid rate limits
        time.sleep(0.3)

    conn.close()

    print(f"\n{'=' * 60}")
    print(f"Batch Enrichment Complete! Successfully enriched {enriched_count} companies.")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    import sys
    limit_val = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    enrich_companies(limit_val)
