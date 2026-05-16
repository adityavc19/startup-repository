import json
import os
from openai import OpenAI

# You can set the LLM_BASE_URL and LLM_API_KEY as environment variables
# For a local server like Ollama, the base URL is typically http://localhost:11434/v1
# For vLLM or other OpenAI-compatible servers, it might be http://localhost:8000/v1
BASE_URL = os.environ.get("LLM_BASE_URL", "http://localhost:11434/v1")
API_KEY = os.environ.get("LLM_API_KEY", "dummy-key-for-local")
MODEL_NAME = os.environ.get("LLM_MODEL", "llama3") # Change to your preferred local model

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

def extract_startup_info(headline):
    """
    Passes a news headline to the LLM to extract the company name, funding amount, and location.
    Returns a dictionary with keys: company, amount, location
    """
    prompt = f"""
You are a data extraction assistant. Extract the startup/company name, funding amount, and location from the following news headline.
If any value is missing or unclear, return "Unknown" for that field.

Headline: "{headline}"

Respond ONLY with a valid JSON object in the following format:
{{
    "company": "Company Name",
    "amount": "Amount Raised",
    "location": "Location"
}}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise data extraction API. Always output raw JSON, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        
        return {
            "company": data.get("company", "Unknown"),
            "amount": data.get("amount", "Unknown"),
            "location": data.get("location", "Unknown")
        }
    except Exception as e:
        print(f"LLM Extraction failed for '{headline}': {e}")
        # Fallback dictionary
        return {"company": "Unknown", "amount": "Unknown", "location": "Unknown"}

def standardize_sector(description):
    """
    Passes the startup description to the LLM to map it to a standard taxonomy.
    """
    valid_sectors = [
        "Fintech", "Healthtech & Bio", "Consumer & Social", "Enterprise SaaS",
        "AI/ML", "E-Commerce & Retail", "Media & Gaming", "EdTech",
        "Agtech / Foodtech", "Logistics & Mobility", "Proptech", "Web3 / Crypto",
        "Hardware / Robotics", "Other / Technology"
    ]
    
    prompt = f"""
Categorize the following startup description into EXACTLY ONE of the allowed sectors.

Allowed Sectors:
{json.dumps(valid_sectors)}

Description: "{description}"

Respond ONLY with a valid JSON object in the following format:
{{
    "sector": "Sector Name"
}}
"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a precise data extraction API. Always output raw JSON, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        data = json.loads(content)
        sector = data.get("sector", "Other / Technology")
        
        if sector not in valid_sectors:
            sector = "Other / Technology"
            
        return sector
    except Exception as e:
        print(f"LLM Sector Categorization failed: {e}")
        return "Unknown"
