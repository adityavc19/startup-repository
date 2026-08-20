"""
Scrape startup funding data from Venture Daily Digest newsletters in Gmail.

First-time setup:
1. Go to https://console.cloud.google.com/
2. Create a project (or select existing)
3. Enable the Gmail API: APIs & Services > Enable APIs > search "Gmail API" > Enable
4. Create OAuth credentials: APIs & Services > Credentials > Create Credentials > OAuth Client ID
   - Application type: Desktop app
   - Download the JSON file and save it as 'credentials.json' in this directory
5. Run this script — it will open a browser window for you to authorize access
"""

import os
import sys
import re
import json
import base64
import sqlite3
import pandas as pd
from datetime import datetime
from email.utils import parsedate_to_datetime

# Gmail API imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

DB_NAME = "startups.db"
TABLE_NAME = "startups"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_FILE = "token.json"
CREDS_FILE = "credentials.json"


def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None

    # Load existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or create new credentials
    if not creds or not creds.valid:
        refreshed = False
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                refreshed = True
            except Exception as e:
                print(f"Warning: Could not refresh token ({e}). Re-authenticating...")
        if not refreshed and (not creds or not creds.valid):
            if not os.path.exists(CREDS_FILE):
                print(f"ERROR: '{CREDS_FILE}' not found!")
                print("Please follow the setup instructions at the top of this file.")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future runs
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def search_emails(service, query, max_results=50):
    """Search Gmail for messages matching the query."""
    results = service.users().messages().list(
        userId="me", q=query, maxResults=max_results
    ).execute()
    return results.get("messages", [])


def get_email_content(service, msg_id):
    """Get the full content of an email by its ID."""
    message = service.users().messages().get(
        userId="me", id=msg_id, format="full"
    ).execute()

    # Extract headers
    headers = message.get("payload", {}).get("headers", [])
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    date_str = next((h["value"] for h in headers if h["name"].lower() == "date"), "")
    from_addr = next((h["value"] for h in headers if h["name"].lower() == "from"), "")

    # Parse date
    try:
        date = parsedate_to_datetime(date_str).strftime("%Y-%m-%d")
    except Exception:
        date = ""

    # Extract body text
    body = extract_body(message.get("payload", {}))

    return {
        "id": msg_id,
        "subject": subject,
        "date": date,
        "from": from_addr,
        "body": body,
    }


def extract_body(payload):
    """Recursively extract text body from email payload."""
    body_text = ""

    if payload.get("body", {}).get("data"):
        body_text += base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")

    for part in payload.get("parts", []):
        mime = part.get("mimeType", "")
        if mime == "text/plain" and part.get("body", {}).get("data"):
            body_text += base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
        elif mime == "text/html" and part.get("body", {}).get("data") and not body_text:
            html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            body_text += re.sub(r"<[^>]+>", " ", html)
        elif "parts" in part:
            body_text += extract_body(part)

    return body_text.strip()


def parse_vdd_fundraises(body, email_date):
    """
    Parse the Venture Daily Digest newsletter format.
    
    Typical format:
    "CompanyName, a Location-based description, raised $XM in Stage funding. 
     The round was led by LeadInvestor, with participation from OtherInvestors."
    """
    records = []

    # Main pattern: "Company, a Location-based description, raised $X in Stage funding"
    pattern = re.compile(
        r"([A-Z][A-Za-z0-9\s\.\-&']+?),\s+"           # Company name
        r"(?:a[n]?\s+)?"                                 # optional "a" or "an"
        r"([A-Z][A-Za-z\s,\.\-]+?)-based\s+"            # Location-based
        r"([A-Za-z\s,/\-&]+?),\s+"                      # Description (what they do)
        r"(?:raised|secured|closed)\s+"                  # Action verb
        r"([\$€£]?[\d,.]+\s*[MBKmb]?(?:illion|n|m)?)\s+" # Amount
        r"(?:in\s+)?"                                    # optional "in"
        r"([A-Za-z\s\d]+?)\s+funding",                  # Stage (Seed, Series A, etc.)
        re.IGNORECASE
    )

    # Also match "raised funding at a $XB valuation" pattern
    pattern_valuation = re.compile(
        r"([A-Z][A-Za-z0-9\s\.\-&']+?),\s+"
        r"(?:a[n]?\s+)?"
        r"([A-Z][A-Za-z\s,\.\-]+?)-based\s+"
        r"([A-Za-z\s,/\-&]+?),\s+"
        r"(?:raised|secured|closed)\s+"
        r"(?:funding\s+at\s+a\s+)?"
        r"([\$€£]?[\d,.]+\s*[MBKmb]?(?:illion|n|m)?)\s+"
        r"(?:valuation\s+in\s+|in\s+)?"
        r"([A-Za-z\s\d]+?)(?:\s+funding|\.\s)",
        re.IGNORECASE
    )

    # Lead investor pattern
    lead_pattern = re.compile(
        r"(?:led by|backed by)\s+([^,\.]+?)(?:,\s+with|\.)",
        re.IGNORECASE
    )

    # Split into individual lines (VDD uses \r\n between entries)
    paragraphs = re.split(r'\r?\n', body)

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        # Skip non-fundraise sections
        if any(skip in para.lower() for skip in [
            "apply here", "newsletter is read", "pitch deck",
            "get in touch", "unsubscribe", "when you're ready",
            "hiring alert", "vc interview", "how i can help",
            "fluidDocs", "fluiddocs"
        ]):
            continue

        # Try main pattern
        match = pattern.search(para)
        if not match:
            match = pattern_valuation.search(para)

        if match:
            company = match.group(1).strip()
            location = match.group(2).strip()
            description = match.group(3).strip()
            amount = match.group(4).strip()
            stage = match.group(5).strip()

            # Clean up amount
            if not amount.startswith(("$", "€", "£")):
                amount = "$" + amount

            # Extract lead investor
            lead_investor = "Unknown"
            lead_match = lead_pattern.search(para)
            if lead_match:
                lead_investor = lead_match.group(1).strip()

            # Extract country from location
            country = extract_country(location)

            # Clean up company name
            company = company.strip().rstrip(",")

            # Skip if company name looks like noise
            if len(company) < 2 or len(company) > 60:
                continue
            if company.lower() in ("the", "a", "an", "this", "that", "our"):
                continue

            records.append({
                "company": company,
                "sector": categorize_sector(description),
                "description": f"{description} ({location}-based)",
                "amount": amount,
                "location": location,
                "stage": stage,
                "lead_investor": lead_investor,
                "date": email_date,
                "source": "Daily Digest",
                "country": country,
                "tags": description,
            })

    # Fallback: simpler pattern for lines we missed
    # "CompanyName raised $XM in Series X"
    simple_pattern = re.compile(
        r"\b([A-Z][A-Za-z0-9\s\.\-&']{1,40}?)(?:\s+has)?\s+"
        r"(?:raised|secured|closed)\s+"
        r"([\$€£][\d,.]+\s*[MBKmb]?(?:illion|n|m)?)\s+"
        r"(?:in\s+)?"
        r"([A-Za-z\s\d]+?)\s+(?:funding|round)",
        re.IGNORECASE
    )

    existing_companies = {r["company"].lower() for r in records}

    for para in paragraphs:
        para = para.strip()
        if not para or len(para) < 20:
            continue
        if any(skip in para.lower() for skip in [
            "apply here", "newsletter", "pitch deck", "unsubscribe",
            "fluiddocs", "how i can help"
        ]):
            continue

        for match in simple_pattern.finditer(para):
            company = match.group(1).strip().rstrip(",")
            amount = match.group(2).strip()
            stage = match.group(3).strip()

            if company.lower() in existing_companies:
                continue
            if len(company) < 2 or len(company) > 60:
                continue
            if company.lower() in ("the", "a", "an", "this", "that", "our", "openai", "meta", "apple", "google", "amazon", "microsoft"):
                continue

            # Extract lead investor
            lead_investor = "Unknown"
            lead_match = lead_pattern.search(para)
            if lead_match:
                lead_investor = lead_match.group(1).strip()

            records.append({
                "company": company,
                "sector": "Unknown",
                "description": "Unknown",
                "amount": amount,
                "location": "Unknown",
                "stage": stage,
                "lead_investor": lead_investor,
                "date": email_date,
                "source": "Daily Digest",
                "country": "Unknown",
                "tags": "",
            })
            existing_companies.add(company.lower())

    return records


def extract_country(location):
    """Extract country from a location string."""
    location = location.strip()
    us_states = [
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "Florida", "Georgia", "Hawaii", "Idaho",
        "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky", "Louisiana",
        "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota",
        "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming", "NYC", "NY", "CA", "TX",
        "MA", "WA", "IL", "PA", "VA", "GA", "FL", "CO", "OH", "MI",
        "NC", "NJ", "MD", "AZ", "MN", "OR", "CT", "UT", "WI", "TN",
    ]
    if any(state in location for state in us_states):
        return "USA"
    
    country_map = {
        "London": "UK", "UK": "UK", "England": "UK", "Edinburgh": "UK",
        "Berlin": "Germany", "Munich": "Germany", "Frankfurt": "Germany", "Stuttgart": "Germany",
        "Paris": "France", "Lyon": "France",
        "Tel Aviv": "Israel", "Israel": "Israel", "Jerusalem": "Israel",
        "Toronto": "Canada", "Vancouver": "Canada", "Montreal": "Canada", "Canada": "Canada",
        "Singapore": "Singapore",
        "Tokyo": "Japan", "Japan": "Japan",
        "Seoul": "South Korea", "Korea": "South Korea",
        "Sydney": "Australia", "Melbourne": "Australia", "Australia": "Australia",
        "Bangalore": "India", "Mumbai": "India", "Delhi": "India", "India": "India",
        "Beijing": "China", "Shanghai": "China", "Shenzhen": "China", "China": "China",
    }
    for key, country in country_map.items():
        if key in location:
            return country
    return "Unknown"


def categorize_sector(description):
    """Categorize a startup description into a sector."""
    desc = description.lower()
    
    sector_map = {
        "Artificial Intelligence": ["ai ", "artificial intelligence", "machine learning", "ml ", "deep learning", "generative ai", "llm", "language model"],
        "Fintech & Finance": ["fintech", "financial", "banking", "payments", "lending", "insurance", "insurtech", "credit"],
        "Healthcare & Biotech": ["health", "medical", "biotech", "pharma", "drug", "therapeutic", "clinical", "genomic", "diagnostic", "oncology", "dermatology"],
        "Enterprise & SaaS": ["saas", "enterprise", "b2b", "workflow", "platform", "compliance", "analytics", "data platform", "crm"],
        "Robotics & Hardware": ["robot", "hardware", "device", "sensor", "chip", "semiconductor"],
        "Cybersecurity": ["security", "cyber", "threat", "intelligence", "risk intelligence"],
        "Climate & Energy": ["climate", "energy", "solar", "clean", "carbon", "sustainability", "green"],
        "Education": ["education", "edtech", "learning", "training"],
        "E-Commerce & Retail": ["commerce", "retail", "shopping", "marketplace"],
        "Developer Tools": ["developer", "devops", "api ", "infrastructure", "cloud"],
        "Real Estate & PropTech": ["real estate", "property", "proptech", "housing"],
        "Gaming": ["game", "gaming", "esport"],
    }
    
    for sector, keywords in sector_map.items():
        if any(kw in desc for kw in keywords):
            return sector
    return "Other"


def save_to_db(records):
    """Insert new startup records into the database."""
    if not records:
        print("No records to insert.")
        return 0

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Check table columns
    cursor.execute(f"PRAGMA table_info({TABLE_NAME})")
    columns = [col[1] for col in cursor.fetchall()]

    # Get existing companies to avoid duplicates
    existing = set(
        row[0].lower()
        for row in cursor.execute(f"SELECT company FROM {TABLE_NAME}").fetchall()
    )

    inserted = 0
    for rec in records:
        company = rec.get("company", "").strip()
        if not company or company.lower() in existing:
            continue

        # Build insert dynamically based on available columns
        insert_cols = []
        insert_vals = []
        
        col_mapping = {
            "company": rec.get("company", "Unknown"),
            "sector": rec.get("sector", "Unknown"),
            "description": rec.get("description", "Unknown"),
            "amount": rec.get("amount", "Unknown"),
            "location": rec.get("location", "Unknown"),
            "stage": rec.get("stage", "Unknown"),
            "date": rec.get("date", ""),
            "source": rec.get("source", "Daily Digest"),
            "country": rec.get("country", "Unknown"),
            "tags": rec.get("tags", ""),
        }
        
        # Only add lead_investor if column exists
        if "lead_investor" in columns:
            col_mapping["lead_investor"] = rec.get("lead_investor", "Unknown")

        for col, val in col_mapping.items():
            if col in columns:
                insert_cols.append(col)
                insert_vals.append(val)

        placeholders = ", ".join(["?" for _ in insert_cols])
        col_names = ", ".join(insert_cols)

        cursor.execute(
            f"INSERT INTO {TABLE_NAME} ({col_names}) VALUES ({placeholders})",
            insert_vals
        )
        existing.add(company.lower())
        inserted += 1

    conn.commit()
    conn.close()
    print(f"\nInserted {inserted} new startups into the database.")
    return inserted


def main():
    print("=" * 60)
    print("Gmail Venture Daily Digest Scraper")
    print("=" * 60)

    # Authenticate
    print("\nAuthenticating with Gmail...")
    service = get_gmail_service()
    print("Authenticated successfully!")

    # Search for Venture Daily Digest emails from Substack
    query = "from:venturedailydigest@substack.com after:2026/04/28"
    print(f"\nSearching: {query}")
    messages = search_emails(service, query, max_results=50)
    print(f"Found {len(messages)} newsletter emails")

    if not messages:
        print("No newsletter emails found!")
        return

    # Process each email
    all_records = []
    for msg in messages:
        email = get_email_content(service, msg["id"])
        print(f"\n{'─' * 50}")
        print(f"📧 {email['date']} | {email['subject'][:70]}")

        records = parse_vdd_fundraises(email["body"], email["date"])
        if records:
            print(f"   ✅ Extracted {len(records)} startups:")
            for rec in records:
                print(f"      • {rec['company']} — {rec['amount']} ({rec['stage']}) [{rec['location']}]")
            all_records.extend(records)
        else:
            print(f"   ⚠️  No fundraise data found in this email")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Total startups extracted: {len(all_records)}")

    if all_records:
        # Save to database
        inserted = save_to_db(all_records)
        print(f"Done! {inserted} new startups added to {DB_NAME}")
    else:
        print("No startup data extracted from the newsletters.")


if __name__ == "__main__":
    main()
