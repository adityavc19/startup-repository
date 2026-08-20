"""
Audit and Triage Database Script.
Scans all existing rows in startups.db, applies triage.py rules,
purges invalid headline / non-startup rows, and corrects inaccurate descriptions.
"""

import sqlite3
from triage import triage_record

DB_NAME = "startups.db"
TABLE_NAME = "startups"

# Specific manual overrides/corrections for verified companies
DESCRIPTION_OVERRIDES = {
    "Yoga Joint": "Infrared heated yoga and fitness studio chain offering hot yoga, core, and HIIT classes."
}

def audit_database():
    print("=" * 60)
    print("Starting Startup Database Triage Audit...")
    print("=" * 60)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    rows = cursor.execute(f"SELECT rowid, company, description, source FROM {TABLE_NAME}").fetchall()
    print(f"Total rows in database: {len(rows)}")

    to_delete = []
    to_update_company = []
    to_update_desc = []

    for rowid, company, description, source in rows:
        company_str = str(company or "")
        desc_str = str(description or "")
        source_str = str(source or "")

        # 1. Apply Triage Gate
        approved, cleaned_company, reason = triage_record(company_str, desc_str, source_str)

        if not approved:
            to_delete.append((rowid, company_str, source_str, reason))
        elif cleaned_company != company_str:
            to_update_company.append((cleaned_company, rowid))

        # 2. Apply Description Overrides
        if company_str in DESCRIPTION_OVERRIDES:
            new_desc = DESCRIPTION_OVERRIDES[company_str]
            if desc_str != new_desc:
                to_update_desc.append((new_desc, rowid))

    print(f"\nAudit complete!")
    print(f"  • Rows flagged for deletion (non-startups / bad headlines): {len(to_delete)}")
    print(f"  • Rows with cleaned company names: {len(to_update_company)}")
    print(f"  • Descriptions corrected: {len(to_update_desc)}")

    if to_delete:
        print("\nSample deleted rows:")
        for r in to_delete[:15]:
            print(f"  ❌ [{r[0]}] '{r[1]}' ({r[2]}) -> {r[3]}")

        cursor.executemany(f"DELETE FROM {TABLE_NAME} WHERE rowid = ?", [(r[0],) for r in to_delete])
        print(f"\n✅ Successfully deleted {len(to_delete)} invalid rows.")

    if to_update_company:
        cursor.executemany(f"UPDATE {TABLE_NAME} SET company = ? WHERE rowid = ?", to_update_company)
        print(f"✅ Updated {len(to_update_company)} company names.")

    if to_update_desc:
        cursor.executemany(f"UPDATE {TABLE_NAME} SET description = ? WHERE rowid = ?", to_update_desc)
        print(f"✅ Corrected {len(to_update_desc)} descriptions.")

    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print("Database Triage Audit Complete!")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    audit_database()
