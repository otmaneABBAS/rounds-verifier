import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get OpenAI API key
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Verification settings
CONFIDENCE_THRESHOLD = 0.7
MAX_RETRIES = 3
REQUEST_TIMEOUT = 10

# Prompt template for extracting funding information
EXTRACTION_PROMPT = """
Please analyze this news article and extract the following funding information:
- Company name
- Funding amount (in millions)
- Round type (e.g., Seed, Series A, etc.)
- Date of funding

News content:
{content}

Please format your response as:
Company: [company name]
Amount: [amount in millions]
Round: [round type]
Date: [date]
""" 