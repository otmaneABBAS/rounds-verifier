import os
import asyncio
import logging
from dotenv import load_dotenv
import pandas as pd
from tqdm import tqdm
from src.ai_verifier import AIFundingVerifier
from src.pydantic_models import FundingAnnouncement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('verification.log')
    ]
)

def load_announcements(csv_path: str) -> list[FundingAnnouncement]:
    """Load funding announcements from CSV file."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path, header=None, names=[
        'id', 'company_name', 'company_url', 'round_type', 'amount', 
        'year', 'month', 'investors', 'news_link'
    ])
    
    announcements = []
    for _, row in df.iterrows():
        try:
            # Convert empty strings to None for optional fields
            investors = row['investors'] if pd.notna(row['investors']) else None
            news_link = row['news_link'] if pd.notna(row['news_link']) else None
            month = int(row['month']) if pd.notna(row['month']) else None
            
            announcement = FundingAnnouncement(
                id=str(row['id']),
                company_name=row['company_name'],
                company_url=row['company_url'],
                round_type=row['round_type'],
                amount=float(row['amount']),
                year=int(row['year']),
                month=month,
                investors=investors,
                news_link=news_link
            )
            announcements.append(announcement)
        except Exception as e:
            logging.error(f"Error processing row {row}: {str(e)}")
            continue
    
    return announcements

async def main():
    """Main function to run the verification process."""
    load_dotenv()
    
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    csv_path = "data/sample.csv"
    announcements = load_announcements(csv_path)
    total_announcements = len(announcements)
    logging.info(f"Loaded {total_announcements} announcements from {csv_path}")
    
    # Create progress bar with more visible settings
    pbar = tqdm(
        total=total_announcements,
        desc="Verifying announcements",
        unit="announcement",
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]',
        ncols=100,
        colour='green',
        leave=True
    )
    
    # Override the update_progress method to update the progress bar
    async def update_progress():
        pbar.update(1)
        pbar.refresh()  # Force refresh the display
    
    try:
        async with AIFundingVerifier(openai_api_key) as verifier:
            # Set the callback in the verifier
            verifier.on_progress = update_progress
            
            # Process announcements in larger batches
            batch_size = 10
            for i in range(0, total_announcements, batch_size):
                batch = announcements[i:i + batch_size]
                await verifier.verify_batch(batch)
                
                # Reduced delay between batches
                await asyncio.sleep(0.5)
                
    except Exception as e:
        logging.error(f"Error during verification: {str(e)}")
        raise
    finally:
        pbar.close()
        logging.info("Verification process completed")

if __name__ == "__main__":
    asyncio.run(main())