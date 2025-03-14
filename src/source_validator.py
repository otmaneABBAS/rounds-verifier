import pandas as pd
from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
from .data_operations import load_csv

def validate_news_link(url: str) -> Dict:
    """
    Validate a news link and extract relevant information
    Returns a dictionary with validation results
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return {
                'status': 'valid',
                'title': soup.title.string if soup.title else None,
                'content': soup.get_text()[:500],  # First 500 characters
                'url': url
            }
        else:
            return {
                'status': 'invalid',
                'error': f'HTTP Status: {response.status_code}',
                'url': url
            }
    except Exception as e:
        return {
            'status': 'error',
            'error': str(e),
            'url': url
        }

def search_funding_news(company: str, year: int, amount: float) -> Optional[str]:
    """
    Search for funding news when no direct link is provided
    Returns the most relevant news URL if found
    """
    # This is a placeholder - we'll implement web search later
    # We'll use Google/Bing API or similar for actual implementation
    return None

def process_entry(row: pd.Series) -> Dict:
    """
    Process a single funding round entry
    Returns validation results
    """
    result = {
        'company': row['Name'],
        'year': row['Year'],
        'amount': row['Amount (USD M)'],
        'round_type': row['Round'],
        'reported_details': {
            'company': row['Name'],
            'year': row['Year'],
            'amount': row['Amount (USD M)'],
            'round_type': row['Round']
        }
    }

    if pd.notna(row['News link']):
        # Case 1: News link is provided
        validation = validate_news_link(row['News link'])
        result.update({
            'is_valid': validation['status'] == 'valid',
            'content': validation.get('content', ''),
            'url': row['News link']
        })
    else:
        # Case 2: Need to search for news
        found_url = search_funding_news(row['Name'], row['Year'], row['Amount (USD M)'])
        if found_url:
            validation = validate_news_link(found_url)
            result.update({
                'is_valid': validation['status'] == 'valid',
                'content': validation.get('content', ''),
                'url': found_url
            })
        else:
            result.update({
                'is_valid': False,
                'content': '',
                'url': None
            })
    
    return result

if __name__ == "__main__":
    # Test with a small batch
    input_path = "data/sample.csv"
    df = load_csv(input_path)
    if df is not None:
        # Test with first entry that has a news link
        test_row = df[~df['News link'].isna()].iloc[0]
        print("\n=== Testing Source Validation ===")
        print(f"Testing validation for: {test_row['Name']}")
        result = process_entry(test_row)
        print("\nValidation Result:")
        print(result) 