import pandas as pd
from typing import Optional

from .data_operations import load_csv, save_dataframe

def create_prompt(row: pd.Series) -> str:
    """
    Creates a prompt for each row based on the data.
    Customize this function according to your specific requirements.
    """
    prompt = f"Given the following information:\n"
    
    # Add each column and its value to the prompt
    for col, value in row.items():
        if col != 'prompt':  # Skip the prompt column itself
            prompt += f"- {col}: {value}\n"
    
    prompt += "\nPlease analyze this data and provide insights."
    
    return prompt

def generate_prompts(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    """
    Add a 'prompt' column to the DataFrame by creating a prompt for each row.
    
    This function:
    1. Makes a copy of the input DataFrame
    2. Creates a prompt for each row using the create_prompt function
    3. Returns the DataFrame with the new 'prompt' column
    4. Returns None if there's an error
    
    Args:
        df: The input DataFrame containing our data
        
    Returns:
        A new DataFrame with an added 'prompt' column, or None if there's an error
    """
    try:
        # Step 1: Make a copy of the original DataFrame to avoid changing it
        print(f"Making a copy of the DataFrame with {len(df)} rows")
        df_copy = df.copy()
        
        # Step 2: Add a new column called 'prompt' to our copy
        print("Creating prompts for each row...")
        df_copy['prompt'] = df_copy.apply(create_prompt, axis=1)
        
        # Step 3: Return the DataFrame with the new column
        print(f"Successfully created {len(df_copy)} prompts!")
        return df_copy
        
    except Exception as e:
        # Step 4: If anything goes wrong, tell us what happened
        print(f"Oops! Something went wrong while creating prompts: {e}")
        return None

def process_data(input_path: str, output_path: str) -> bool:
    """Process the data from input to output."""
    df = load_csv(input_path)
    if df is None:
        return False
        
    df_with_prompts = generate_prompts(df)
    if df_with_prompts is None:
        return False
        
    print(df_with_prompts.head(10))
    return save_dataframe(df_with_prompts, output_path) 