import pandas as pd
import os
from typing import Optional

def load_csv(file_path: str) -> Optional[pd.DataFrame]:
    """Load a CSV file into a pandas DataFrame."""
    try:
        df = pd.read_csv(file_path)
        print(f"Successfully loaded CSV with {len(df)} rows")
        return df
    except Exception as e:
        print(f"Error loading CSV file: {e}")
        return None

def save_dataframe(df: pd.DataFrame, output_path: str) -> bool:
    """Save DataFrame to CSV file."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        print(f"Successfully saved to {output_path}")
        return True
    except Exception as e:
        print(f"Error saving DataFrame: {e}")
        return False 