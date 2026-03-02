import pandas as pd
import re
from typing import List, Dict, Any
from io import StringIO


def parse_price(price_str: str) -> int | None:
    """Parse price string like '$204,900' to cents (20490000)."""
    if not price_str or price_str == "—":
        return None
    # Remove $ and commas, handle + suffix for plans
    cleaned = re.sub(r'[$,+]', '', price_str.strip())
    try:
        return int(float(cleaned) * 100)
    except (ValueError, TypeError):
        return None


def parse_sqft(sqft_str: str) -> int | None:
    """Parse sqft string like '1,152' to integer."""
    if not sqft_str or sqft_str == "—":
        return None
    cleaned = re.sub(r'[,]', '', sqft_str.strip())
    try:
        return int(cleaned)
    except (ValueError, TypeError):
        return None


def parse_days_on_market(dom_str: str) -> int | None:
    """Parse days on market like '8 days' to integer."""
    if not dom_str or dom_str == "—":
        return None
    # Extract first number
    match = re.search(r'(\d+)', dom_str)
    if match:
        return int(match.group(1))
    return None


def parse_beds(beds_str: str) -> int | None:
    """Parse beds to integer."""
    if not beds_str or beds_str == "—":
        return None
    try:
        return int(beds_str)
    except (ValueError, TypeError):
        return None


def parse_baths(baths_str: str) -> float | None:
    """Parse baths to float."""
    if not baths_str or baths_str == "—":
        return None
    try:
        return float(baths_str)
    except (ValueError, TypeError):
        return None


def extract_city_from_url(url: str) -> str | None:
    """Extract city from Redfin URL like https://www.redfin.com/OH/Cleveland/..."""
    if not url:
        return None
    match = re.search(r'redfin\.com/[A-Z]{2}/([^/]+)/', url)
    if match:
        # Convert URL-encoded city name
        city = match.group(1).replace('-', ' ')
        return city
    return None


def parse_redfin_csv(csv_content: str, zip_code: str) -> List[Dict[str, Any]]:
    """
    Parse Redfin CSV content and return list of property dictionaries.

    CSV columns:
    - Column 0: "address" -> address
    - Column 1: "address href" -> redfin_url (extract city from URL)
    - Column 2: "location" -> neighborhood
    - Column 3: "column" -> price
    - Column 4: "column 2" -> beds
    - Column 5: "column 3" -> baths
    - Column 6: "column 4" -> sqft
    - Column 7: "column 5" -> price_per_sqft
    - Column 8: "column 6" -> days_on_market
    """
    df = pd.read_csv(StringIO(csv_content))

    properties = []
    for _, row in df.iterrows():
        address = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        redfin_url = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""

        # Skip rows without valid addresses
        if not address or address.lower() in ['address', '']:
            continue

        property_data = {
            "address": address,
            "redfin_url": redfin_url,
            "city": extract_city_from_url(redfin_url),
            "zip_code": zip_code,
            "neighborhood": str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else None,
            "price": parse_price(str(row.iloc[3]) if pd.notna(row.iloc[3]) else ""),
            "beds": parse_beds(str(row.iloc[4]) if pd.notna(row.iloc[4]) else ""),
            "baths": parse_baths(str(row.iloc[5]) if pd.notna(row.iloc[5]) else ""),
            "sqft": parse_sqft(str(row.iloc[6]) if pd.notna(row.iloc[6]) else ""),
            "price_per_sqft": parse_price(str(row.iloc[7]) if pd.notna(row.iloc[7]) else ""),
            "days_on_market": parse_days_on_market(str(row.iloc[8]) if pd.notna(row.iloc[8]) else ""),
        }

        properties.append(property_data)

    return properties
