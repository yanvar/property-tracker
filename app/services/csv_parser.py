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


def extract_state_from_url(url: str) -> str | None:
    """Extract state from Redfin URL like https://www.redfin.com/OH/Cleveland/..."""
    if not url:
        return None
    match = re.search(r'redfin\.com/([A-Z]{2})/', url)
    if match:
        return match.group(1)
    return None


def extract_zip_from_url(url: str) -> str | None:
    """Extract zip code from Redfin URL like .../6749-Rockridge-Ct-44130/..."""
    if not url:
        return None
    # Look for 5-digit zip code pattern in the URL path
    match = re.search(r'-(\d{5})(?:/|$)', url)
    if match:
        return match.group(1)
    return None


def get_column_value(row, column_name: str) -> str:
    """Safely get a column value by name, returning empty string if not found or NaN."""
    if column_name in row.index and pd.notna(row[column_name]):
        return str(row[column_name]).strip()
    return ""


def parse_redfin_csv(csv_content: str) -> List[Dict[str, Any]]:
    """
    Parse Redfin CSV content and return list of property dictionaries.

    Uses column names for robust parsing across different Redfin CSV formats.
    Column name mapping:
    - "address" -> address
    - "address href" -> redfin_url (extract city and zip from URL)
    - "location" -> neighborhood
    - "column" -> price
    - "column 2" -> beds
    - "column 3" -> baths
    - "column 4" -> sqft
    - "column 5" -> price_per_sqft
    - "column 6" -> days_on_market
    """
    df = pd.read_csv(StringIO(csv_content))

    properties = []
    for _, row in df.iterrows():
        address = get_column_value(row, "address")
        redfin_url = get_column_value(row, "address href")

        # Skip rows without valid addresses
        if not address or address.lower() in ['address', '']:
            continue

        neighborhood = get_column_value(row, "location")

        property_data = {
            "address": address,
            "redfin_url": redfin_url,
            "city": extract_city_from_url(redfin_url),
            "state": extract_state_from_url(redfin_url),
            "zip_code": extract_zip_from_url(redfin_url),
            "neighborhood": neighborhood if neighborhood else None,
            "price": parse_price(get_column_value(row, "column")),
            "beds": parse_beds(get_column_value(row, "column 2")),
            "baths": parse_baths(get_column_value(row, "column 3")),
            "sqft": parse_sqft(get_column_value(row, "column 4")),
            "price_per_sqft": parse_price(get_column_value(row, "column 5")),
            "days_on_market": parse_days_on_market(get_column_value(row, "column 6")),
        }

        properties.append(property_data)

    return properties
