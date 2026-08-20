"""
Triage Gate & Data Quality Module for Startup Intelligence Database.
Validates whether an extracted record is a legitimate startup/funding event,
filters out news headlines, regulatory updates, feature launches, and corporate news,
and cleans entity names.
"""

import re
from typing import Tuple, Optional

# Verbs & phrases in headlines that indicate non-funding news / non-company items
NON_STARTUP_VERBS = [
    r'\bbanned\b', r'\blaunching\b', r'\blaunches feature\b', r'\bmarks down\b',
    r'\bfiles lawsuit\b', r'\bposts revenue\b', r'\bposts profit\b', r'\bposts loss\b',
    r'\bwarns\b', r'\babandons\b', r'\bbuys\b', r'\bpartnered with\b', r'\bfaces\b',
    r'\bmulls\b', r'\breceives\b', r'\bacquires\b', r'\bshuts\b', r'\bsecures approval\b',
    r'\bcloses deal\b', r'\blands in\b', r'\beyes\b', r'\bgets approval\b', r'\bplans to\b',
    r'\bfiles for\b', r'\bsays\b', r'\breports\b', r'\bipo\b', r'\bpicks up\b',
    r'\bto raise\b', r'\breduces\b', r'\blayoffs\b', r'\bfires\b', r'\bhires\b',
    r'\bappoints\b', r'\bexpands to\b', r'\benters\b', r'\btests\b', r'\bdrops\b',
    r'\brallies\b', r'\bbrings\b', r'\bsues\b', r'\bcourt\b', r'\bgovernment\b',
    r'\bpolicy\b', r'\bregulator\b', r'\bfined\b', r'\btax\b', r'\bshares\b', r'\bstock\b'
]

NON_STARTUP_REGEX = re.compile('|'.join(NON_STARTUP_VERBS), re.IGNORECASE)

# Words/Phrases that indicate descriptive fragments rather than company names
BAD_COMPANY_PREFIXES = [
    'for ', 'with ', 'in ', 'on ', 'at ', 'and ', 'is ',
    'exclusive:', '[updated]', 'deals in brief:', 'data vantage:', 'deals digest:'
]

BAD_COMPANY_SUFFIXES = [
    ' for', ' with', ' in', ' on', ' at', ' and', ' is', ' a', ' an', "'s"
]

def is_valid_company_name(name: str) -> Tuple[bool, str]:
    """
    Validates and cleans a proposed company name.
    Returns (is_valid, cleaned_name).
    """
    if not name or not isinstance(name, str):
        return False, ""

    cleaned = name.strip()
    
    # Strip common prefixes like "Exclusive: D2C Perfume Brand Fraganote"
    for prefix in ['Exclusive:', '[Updated]', 'Deals in brief:', 'DATA VANTAGE:', 'Deals Digest:', 'India:', 'Japan:', 'Korea:', 'Vietnam:', 'China:', 'Now,', 'SG ']:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()

    if cleaned.endswith("’s") or cleaned.endswith("'s"):
        cleaned = cleaned[:-2].strip()

    # Reject if too short or too long
    if len(cleaned) < 2 or len(cleaned) > 55:
        return False, ""

    # Reject if name contains headline verbs (e.g. "Ola banned in Chandigarh")
    if NON_STARTUP_REGEX.search(cleaned):
        return False, ""

    # Reject if it looks like a full sentence or descriptive clause
    words = cleaned.split()
    if len(words) > 5:
        return False, ""

    # Reject if starts/ends with bad fragment connectors
    lowered = cleaned.lower()
    for bad_pre in BAD_COMPANY_PREFIXES:
        if lowered.startswith(bad_pre) and not bad_pre in ['exclusive:', '[updated]', 'deals in brief:', 'data vantage:', 'deals digest:']:
            return False, ""
            
    for bad_suf in BAD_COMPANY_SUFFIXES:
        if lowered.endswith(bad_suf):
            return False, ""

    # Must contain at least one alphanumeric character
    if not re.search(r'[a-zA-Z0-9]', cleaned):
        return False, ""

    return True, cleaned


def triage_record(company: str, description: str = "", source: str = "") -> Tuple[bool, str, str]:
    """
    Triages a startup candidate record.
    Returns (is_approved, cleaned_company, reason).
    """
    # Check company name validity
    valid_company, cleaned_company = is_valid_company_name(company)
    if not valid_company:
        return False, company, f"Invalid company name entity: '{company}'"

    # Check description for obvious non-funding / non-startup indicators
    if description:
        # If description is a headline about bans/lawsuits/market drops without funding mentions
        has_funding = bool(re.search(r'(\$|₹|funding|raised|seed|series|invest|valuation)', description, re.IGNORECASE))
        has_negative_news = bool(re.search(r'\b(banned|lawsuit|sues|fine|penalty|markdown|layoff|banning)\b', description, re.IGNORECASE))
        
        if has_negative_news and not has_funding:
            return False, cleaned_company, f"Description indicates non-funding news event: '{description}'"

    return True, cleaned_company, "Approved"
