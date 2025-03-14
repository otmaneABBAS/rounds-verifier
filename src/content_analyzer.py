import logging
from typing import Optional, Dict, Any, List, Tuple
import json
from urllib.parse import urlparse
from openai import OpenAI
from .types import ExtractedDetails, SourceReliability

class ContentAnalyzer:
    def __init__(self, api_key: str):
        """Initialize the content analyzer."""
        self.client = OpenAI(api_key=api_key)
        
        # Configure verified domains and their base reliability scores
        self.verified_domains = {
            'techcrunch.com': 0.9,
            'reuters.com': 0.95,
            'bloomberg.com': 0.95,
            'wsj.com': 0.95,
            'venturebeat.com': 0.85,
            'crunchbase.com': 0.85,
            'forbes.com': 0.85,
            'businesswire.com': 0.8,
            'prnewswire.com': 0.8
        }
    
    def analyze_content(self, content: str, source_url: str) -> Tuple[ExtractedDetails, SourceReliability]:
        """Analyze content and extract funding details."""
        try:
            # Extract details using OpenAI
            extracted_details = self._extract_details(content)
            
            # Assess source reliability
            source_reliability = self._assess_source_reliability(source_url, content)
            
            return extracted_details, source_reliability
            
        except Exception as e:
            logging.error(f"Error analyzing content: {str(e)}")
            raise
    
    def _extract_details(self, content: str) -> ExtractedDetails:
        """Extract funding details from content using OpenAI."""
        try:
            # Prepare prompt for OpenAI
            prompt = f"""Extract funding announcement details from the following text.
            You must respond with ONLY a valid JSON object containing these fields:
            {{
                "company_name": "Company name (string)",
                "amount": "Funding amount in millions (float)",
                "round_type": "Type of funding round (string)",
                "date": "Announcement date (YYYY-MM-DD string)",
                "investors": ["List of investors if mentioned (array of strings)"],
                "description": "Brief description of the company/funding (string)"
            }}
            
            Text: {content}
            
            Respond with ONLY the JSON object, no other text."""
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a precise funding details extractor. You must respond with ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Parse response
            try:
                result = json.loads(response.choices[0].message.content)
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON response: {response.choices[0].message.content}")
                raise ValueError("OpenAI response was not valid JSON")
            
            # Validate required fields
            required_fields = ['company_name', 'amount', 'round_type', 'date']
            missing_fields = [field for field in required_fields if field not in result]
            if missing_fields:
                raise ValueError(f"Missing required fields in OpenAI response: {missing_fields}")
            
            # Create ExtractedDetails object
            return ExtractedDetails(
                company_name=str(result['company_name']),
                amount=float(result['amount']),
                round_type=str(result['round_type']),
                date=str(result['date']),
                investors=result.get('investors', []),
                description=result.get('description', '')
            )
            
        except Exception as e:
            logging.error(f"Error extracting details: {str(e)}")
            raise
    
    def _assess_source_reliability(self, source_url: str, content: str) -> SourceReliability:
        """Assess the reliability of the content source."""
        try:
            # Get domain from URL
            domain = urlparse(source_url).netloc.lower()
            
            # Check if domain is verified
            is_verified = domain in self.verified_domains
            base_reliability = self.verified_domains.get(domain, 0.5)
            
            # Assess content quality
            content_quality = self._assess_content_quality(content)
            
            # Calculate overall score
            overall_score = (base_reliability * 0.7) + (content_quality * 0.3)
            
            return SourceReliability(
                domain=domain,
                is_verified_publisher=is_verified,
                reliability_score=base_reliability,
                content_quality_score=content_quality,
                overall_score=overall_score
            )
            
        except Exception as e:
            logging.error(f"Error assessing source reliability: {str(e)}")
            raise
    
    def _assess_content_quality(self, content: str) -> float:
        """Assess the quality of the content using OpenAI."""
        try:
            prompt = f"""Assess the quality and professionalism of this funding announcement content.
            Consider:
            1. Clarity and completeness of information
            2. Professional writing style
            3. Presence of key details (amount, date, investors)
            4. Absence of promotional/marketing language
            
            Return ONLY a single number between 0 and 1, where:
            0.0-0.3: Poor quality, unprofessional, or missing key details
            0.4-0.6: Average quality, some issues or missing information
            0.7-0.8: Good quality, professional, most details present
            0.9-1.0: Excellent quality, highly professional, all details present
            
            Content: {content}
            
            Score (respond with ONLY the number):"""
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a content quality assessor. You must respond with ONLY a number between 0 and 1."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1
            )
            
            # Extract score from response
            score_text = response.choices[0].message.content.strip()
            try:
                score = float(score_text)
                return min(max(score, 0.0), 1.0)  # Ensure score is between 0 and 1
            except ValueError:
                logging.warning(f"Could not parse quality score: {score_text}")
                return 0.5
            
        except Exception as e:
            logging.error(f"Error assessing content quality: {str(e)}")
            return 0.5  # Default to medium quality on error

def normalize_date(date_str: str) -> Optional[str]:
    """Normalize date format to YYYY-MM-DD."""
    if pd.isna(date_str) or not date_str:
        return None
    try:
        if isinstance(date_str, str):
            date_obj = pd.to_datetime(date_str)
        else:
            date_obj = pd.to_datetime(date_str)
        return date_obj.strftime('%Y-%m-%d')
    except Exception as e:
        logging.warning(f"Error parsing date '{date_str}': {str(e)}")
        return None

def main():
    """Main function to run the content analyzer."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('verification.log'),
            logging.StreamHandler()
        ]
    )
    
    # Test data with various date formats
    test_data = [
        {
            "company": "TechCorp",
            "amount": 10.5,
            "round_type": "Series A",
            "date": "2024-03-01",
            "source_url": "https://techcrunch.com/2024/03/01/techcorp-funding",
            "content": "TechCorp announced today that it has raised $10.5 million in a Series A funding round on March 8, 2022."
        },
        {
            "company": "DataAI",
            "amount": 5.0,
            "round_type": "Seed",
            "date": "15/02/2024",  # DD/MM/YYYY format
            "source_url": "https://venturebeat.com/2024/02/15/dataai-seed-round",
            "content": "DataAI has secured $5M in seed funding to advance its AI platform development."
        },
        {
            "company": "CloudScale",
            "amount": 25.0,
            "round_type": "Series B",
            "date": "Mar 5, 2024",  # Month name format
            "source_url": "https://reuters.com/2024/03/05/cloudscale-funding",
            "content": "CloudScale's Series B round brings in $25M to expand cloud infrastructure services."
        }
    ]
    
    # Save test data
    test_df = pd.DataFrame(test_data)
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    test_df.to_csv(data_dir / "test_announcements.csv", index=False)
    
    # Run verifications
    try:
        run_verifications("data/test_announcements.csv")
    except Exception as e:
        logging.error(f"Error running verifications: {str(e)}")
        raise

if __name__ == "__main__":
    main() 