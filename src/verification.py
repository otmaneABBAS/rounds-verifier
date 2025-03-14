import pandas as pd
from typing import Dict, Optional
from .data_operations import load_csv

def analyze_funding_data(file_path: str) -> Optional[pd.DataFrame]:
    """
    Step 1: Data Collection and Initial Analysis
    - Load and analyze the funding round data
    - Categorize entries based on available verification sources
    """
    df = load_csv(file_path)
    if df is None:
        return None
    
    # Categorize entries
    df['verification_category'] = 'needs_verification'
    df.loc[~df['News link'].isna(), 'verification_category'] = 'has_news_link'
    
    # Print summary
    print("\n=== Verification Categories ===")
    print(df['verification_category'].value_counts())
    
    # Basic validation checks
    print("\n=== Data Validation ===")
    print(f"Total entries: {len(df)}")
    print(f"Entries with news links: {(~df['News link'].isna()).sum()}")
    print(f"Entries needing web search: {df['News link'].isna().sum()}")
    
    return df

def prepare_verification_batch(df: pd.DataFrame, batch_size: int = 10) -> pd.DataFrame:
    """
    Prepare a batch of entries for verification
    Priority: entries with news links first
    """
    # First priority: entries with news links
    has_links = df[df['verification_category'] == 'has_news_link'].head(batch_size)
    return has_links

if __name__ == "__main__":
    input_path = "data/sample.csv"
    df = analyze_funding_data(input_path)
    if df is not None:
        print("\n=== Preparing Verification Batch ===")
        batch = prepare_verification_batch(df)
        print(f"\nFirst batch to verify ({len(batch)} entries):")
        print(batch[['Name', 'Round', 'Amount (USD M)', 'Year', 'News link']].head()) 