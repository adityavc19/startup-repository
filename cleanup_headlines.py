"""
One-time cleanup: delete startup records with article-headline names (not real company names).
Also clears out incorrect websites from the consumer spotlight enrichment.
"""

import sqlite3
import re

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# Patterns that indicate the "company" field is actually a news headline
HEADLINE_PATTERNS = [
    r'\bMulls\b', r'\bReceives\b', r'\bRaises\b', r'\bAcquires\b',
    r'\bShuts\b', r'\bLaunches\b', r'\bSecures\b', r'\bBags\b',
    r'\bCloses\b', r'\bLands\b', r'\bPicks Up\b', r'\bEyes\b',
    r'\bGets\b', r'\bFunds\b', r'\bTo Raise\b', r'\bIPO\b',
    r'\bFiling\b', r'\bReport\b', r'\bSays\b', r'\bPlans\b',
    r'^Mobile Gaming$', r'^Online Gaming$', r'^New Gaming$',
    r'^Mobile Gaming', r'^Online Gaming', r'^New Gaming',
    r'Gaming\.\.\.$',  # truncated headlines like "Mobile Gaming..."
    r"Biswas'",  # "Kabeer Biswas' M..."
    r"Biswas's",
    r'^Zerodha\s+\w+',  # "Zerodha shuts..."
    r'^Flipkart\s+\w+',  # "Flipkart Mulls..."
    r'^Petpooja,\s',     # "Petpooja, Restaurants..."
    r'^MobiKwik\s+\w+',  # "MobiKwik Receives..."
]

# Trusted websites that are clearly NOT the startup's website
BAD_WEBSITES = [
    "ycombinator.com",
    "business-standard.com",
    "economictimes.indiatimes.com",
    "entrackr.com",
    "inc42.com",
    "yourstory.com",
    "techcrunch.com",
    "bloomberg.com",
    "reuters.com",
    "forbes.com",
    "hitwicket.com",  # assigned to wrong startup
    "topstartups.io",
    "laffaz.com",
    "scopely.com",
    "jestjs.io",      # Jest the JS testing library, not a startup
    "apache.org",
    "gnu.org",
    "flink.apache.org",
    "remix.ethereum.org",
    "docs.ray.io",
    "learn.microsoft.com",
    "startuphaven.com",
    "napkinmath.com",
    "kinectcapital.org",
    "arapartners.com",
    "dos.fl.gov",
    "lumapps.com",
    "pelagohealth.com",  # Pelago is a health company not a consumer app
]


def is_headline(company_name):
    for pattern in HEADLINE_PATTERNS:
        if re.search(pattern, company_name, re.IGNORECASE):
            return True
    return False


def main():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Find and delete headline-named records
    all_companies = cursor.execute(
        f"SELECT rowid, company, source FROM {TABLE_NAME}"
    ).fetchall()

    to_delete = []
    for rowid, company, source in all_companies:
        if is_headline(str(company or "")):
            to_delete.append((rowid, company, source))

    print(f"Found {len(to_delete)} headline-named records to delete:")
    for rowid, company, source in to_delete:
        print(f"  [{rowid}] '{company}' ({source})")

    if to_delete:
        cursor.executemany(
            f"DELETE FROM {TABLE_NAME} WHERE rowid = ?",
            [(r[0],) for r in to_delete]
        )
        print(f"\n✅ Deleted {len(to_delete)} bad records.")

    # 2. Clear incorrect websites
    all_websites = cursor.execute(
        f"SELECT rowid, company, website FROM {TABLE_NAME} WHERE website IS NOT NULL AND website != ''"
    ).fetchall()

    cleared = 0
    for rowid, company, website in all_websites:
        if any(bad in str(website) for bad in BAD_WEBSITES):
            cursor.execute(
                f"UPDATE {TABLE_NAME} SET website = '' WHERE rowid = ?",
                (rowid,)
            )
            print(f"  Cleared bad website for '{company}': {website}")
            cleared += 1

    print(f"\n✅ Cleared {cleared} incorrect website entries.")

    conn.commit()
    conn.close()
    print("\nDone! Database cleaned up.")


if __name__ == "__main__":
    main()
