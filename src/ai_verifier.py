import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import os
import pandas as pd
import aiohttp
from tqdm import tqdm
from openai import AsyncOpenAI
from .pydantic_models import (
    FundingAnnouncement,
    SourceReliability,
    VerificationResult,
    VerificationStatus,
    Discrepancy
)
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
import time
import json

class AIFundingVerifier:
    def __init__(self, openai_api_key: str):
        """Initialize the AI-powered funding verifier."""
        self.client = AsyncOpenAI(api_key=openai_api_key)
        self.confidence_threshold = 0.8
        self.session = None
        self.cache = {}  # Simple cache for URL contents
        self.on_progress = None  # Callback for progress updates
        self.semaphore = asyncio.Semaphore(8)  # Increased to 8 concurrent API calls
        self.checkpoint_file = "reports/checkpoint.json"
        self.processed_companies = set()
        
    def load_checkpoint(self) -> None:
        """Load the last checkpoint if it exists."""
        try:
            if os.path.exists(self.checkpoint_file):
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                    self.processed_companies = set(checkpoint.get('processed_companies', []))
                    logging.info(f"Loaded checkpoint with {len(self.processed_companies)} processed companies")
        except Exception as e:
            logging.error(f"Error loading checkpoint: {str(e)}")
            self.processed_companies = set()

    def save_checkpoint(self) -> None:
        """Save the current state to a checkpoint file."""
        try:
            checkpoint = {
                'processed_companies': list(self.processed_companies),
                'timestamp': datetime.now().isoformat()
            }
            os.makedirs(os.path.dirname(self.checkpoint_file), exist_ok=True)
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f)
            logging.info(f"Saved checkpoint with {len(self.processed_companies)} processed companies")
        except Exception as e:
            logging.error(f"Error saving checkpoint: {str(e)}")

    async def verify_batch(self, announcements: List[FundingAnnouncement], batch_size: int = 15) -> None:
        """Process announcements in batches with improved error handling and parallel processing."""
        # Load previous checkpoint
        self.load_checkpoint()
        
        total = len(announcements)
        processed = 0
        with_links = 0
        verified = 0
        errors = 0
        
        results = []
        
        # Filter out already processed companies
        announcements_to_process = [
            a for a in announcements 
            if a.company_name not in self.processed_companies
        ]
        
        logging.info(f"Resuming verification with {len(announcements_to_process)} remaining announcements")
        
        # Process announcements in larger batches
        for i in range(0, len(announcements_to_process), batch_size):
            batch = announcements_to_process[i:i + batch_size]
            tasks = []
            
            for announcement in batch:
                task = asyncio.create_task(self._process_single_announcement(announcement))
                tasks.append(task)
            
            # Wait for all tasks in the batch to complete
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    errors += 1
                    logging.error(f"Error processing announcement: {str(result)}")
                    continue
                
                if result:
                    verified += 1
                    results.append(result)
                    self.processed_companies.add(result.company_name)
                
                processed += 1
                if self.on_progress:
                    await self.on_progress()
                
                # Save checkpoint after each successful verification
                self.save_checkpoint()
                
                # Reduced delay between batches
                await asyncio.sleep(0.3)
            
            # Save batch results more frequently
            if results:
                await self._save_results(results)
                results = []  # Clear results after saving
        
        # Save final summary
        summary = {
            "total_processed": total,
            "with_links": with_links,
            "verified": verified,
            "errors": errors
        }
        await self._save_summary(summary)
        
        # Clean up checkpoint file after successful completion
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
            logging.info("Removed checkpoint file after successful completion")

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=20)  # Reduced timeout to 20 seconds
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        
    async def verify_announcement(self, reported: FundingAnnouncement) -> VerificationResult:
        """Verify a single funding announcement."""
        try:
            # Fetch and analyze content from source URL
            try:
                content = await self._fetch_content(reported.news_link)
            except Exception as e:
                logging.error(f"Error fetching content from {reported.news_link}: {str(e)}")
                # Return unverified result if content cannot be fetched
                return VerificationResult(
                    company_name=reported.company_name,
                    verification_status=VerificationStatus.UNVERIFIED,
                    overall_confidence=0.0,
                    source_url=reported.news_link,
                    discrepancies=[],
                    verification_notes=f"Could not verify - Failed to fetch content: {str(e)}"
                )
            
            # Analyze source reliability
            source_reliability = await self._analyze_source_reliability(reported.news_link, content)
            
            # Extract details from content
            extracted = await self._extract_announcement_details(content)
            
            # Verify the announcement
            result = await self._verify_details(reported, extracted, source_reliability)
            
            return result
            
        except Exception as e:
            logging.error(f"Error verifying announcement: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _analyze_source_reliability(self, url: str, content: str) -> SourceReliability:
        """Analyze the reliability of a news source."""
        prompt = f"""Perform a comprehensive analysis of this news source:

URL: {url}
Content Sample: {content[:1000]}...

Please evaluate:
1. Domain Reputation:
   - Is this a well-known financial/business news source?
   - Check for professional domain and established presence
   - Assess editorial standards and fact-checking practices

2. Content Quality:
   - Writing professionalism and clarity
   - Use of specific details and facts
   - Presence of quotes or direct sources
   - Balance and objectivity in reporting

3. Verification Status:
   - Is this a verified publisher?
   - Are there clear author attributions?
   - Is contact information available?
   - Are sources cited properly?

4. Technical Assessment:
   - Website security (HTTPS)
   - Professional formatting
   - Presence of ads/sponsored content
   - Mobile responsiveness

Return the analysis in this format:
Domain: [extracted domain name]
Score: [0-1 reliability score]
Verified: [yes/no]
Detailed Assessment:
[bullet points with key findings]"""

        try:
            response = await self._chat_completion(prompt)
            
            # Parse response
            lines = response.split('\n')
            domain = url.split('/')[2]
            score = 0.5  # Default score
            is_verified = False
            
            for line in lines:
                line = line.strip()
                if line.startswith('Score:'):
                    try:
                        score = float(line.split(':')[1].strip())
                    except ValueError:
                        pass
                elif line.startswith('Verified:'):
                    is_verified = 'yes' in line.lower()
                elif line.startswith('Domain:'):
                    domain = line.split(':')[1].strip() or domain
            
            return SourceReliability(
                domain=domain,
                score=score,
                verification_status=VerificationStatus.VERIFIED if is_verified else VerificationStatus.UNVERIFIED
            )
        except Exception as e:
            logging.warning(f"Error analyzing source reliability for {url}: {str(e)}")
            return SourceReliability(
                domain=url.split('/')[2],
                score=0.5,  # Default moderate score
                verification_status=VerificationStatus.UNVERIFIED
            )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _extract_announcement_details(self, content: str) -> FundingAnnouncement:
        """Extract funding announcement details from content."""
        prompt = f"""Extract detailed funding announcement information from this content:
{content}

Please analyze the text carefully and extract:

1. Company Information:
   - Full company name
   - Any alternative names or trading names mentioned
   - Brief description of company's business

2. Funding Details:
   - Exact funding amount in millions USD
   - Round type/series
   - Pre/post-money valuation if mentioned
   - Previous funding rounds if mentioned

3. Timing Information:
   - Announcement date
   - Closing date if different
   - Any relevant timeline details

4. Additional Context:
   - Key investors involved
   - Use of funds
   - Company growth metrics
   - Market context

Return the core announcement details in this exact format:
Company name: [full legal name]
Funding amount: [number in millions USD]
Round type: [seed/series A/B/etc]
Announcement date: [YYYY-MM-DD]
Source URL: [url]

Additional context:
[bullet points with other relevant details]"""

        response = await self._chat_completion(prompt)
        
        # Parse response and create FundingAnnouncement object
        lines = response.split('\n')
        details = {}
        
        # Extract core details
        for line in lines:
            if ':' in line and not line.startswith('Additional context'):
                key, value = line.split(':', 1)
                details[key.strip().lower().replace(' ', '_')] = value.strip()
        
        try:
            # Clean and convert amount
            amount_str = details.get('funding_amount', '0')
            amount_str = amount_str.replace('$', '').replace(',', '').replace('M', '').replace('USD', '').strip()
            amount = float(amount_str)
            
            # Clean and standardize round type
            round_type = details.get('round_type', '').strip().upper()
            if 'SERIES' not in round_type and round_type not in ['SEED', 'ANGEL', 'IPO']:
                if round_type:
                    round_type = f"SERIES {round_type}"
                else:
                    round_type = "UNSPECIFIED"
            
            # Parse and validate date
            date_str = details.get('announcement_date', '')
            try:
                announcement_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                announcement_date = datetime.now().date()
            
            return FundingAnnouncement(
                company_name=details.get('company_name', ''),
                amount=amount,
                round_type=round_type,
                date=announcement_date,
                source_url=details.get('source_url', '')
            )
            
        except (KeyError, ValueError) as e:
            logging.warning(f"Error parsing extracted details: {str(e)}")
            # Return a minimal announcement with default values
            return FundingAnnouncement(
                company_name=details.get('company_name', ''),
                amount=0.0,
                round_type="UNSPECIFIED",
                date=datetime.now().date(),
                source_url=details.get('source_url', '')
            )

    async def _verify_details(
        self,
        reported: FundingAnnouncement,
        extracted: FundingAnnouncement,
        source_reliability: SourceReliability
    ) -> VerificationResult:
        """Compare reported and extracted details to verify the announcement."""
        comparison_prompt = f"""Analyze and compare these funding announcement details:

REPORTED DETAILS:
Company: {reported.company_name}
Amount: ${reported.amount}M
Round Type: {reported.round_type}
Date: {reported.year}-{reported.month if reported.month else '01'}

EXTRACTED DETAILS:
Company: {extracted.company_name}
Amount: ${extracted.amount}M
Round Type: {extracted.round_type}
Date: {extracted.date}

Please analyze:
1. Are there any discrepancies between the reported and extracted information?
2. For each discrepancy, assess its severity and potential impact on verification
3. Consider the context and potential reasons for any differences
4. Determine if the differences are significant enough to affect verification

Return the analysis in this format:
Discrepancies: [list each discrepancy with field, values, and impact score 0-1]
Verification Status: [VERIFIED/UNVERIFIED]
Confidence Score: [0-1]
Notes: [detailed explanation]"""

        # Get AI analysis
        analysis = await self._chat_completion(comparison_prompt)
        
        # Parse AI response and create discrepancies
        discrepancies = []
        verification_notes = []
        
        # Extract discrepancies from AI response
        response_lines = analysis.split('\n')
        current_section = ""
        
        for line in response_lines:
            line = line.strip()
            if line.startswith('Discrepancies:'):
                current_section = "discrepancies"
            elif line.startswith('Verification Status:'):
                status_line = line.split(':')[1].strip()
                status = VerificationStatus.VERIFIED if "VERIFIED" in status_line else VerificationStatus.UNVERIFIED
            elif line.startswith('Confidence Score:'):
                try:
                    confidence = float(line.split(':')[1].strip())
                except ValueError:
                    confidence = 0.5
            elif line.startswith('Notes:'):
                current_section = "notes"
            elif line and current_section == "discrepancies" and ':' in line:
                # Parse discrepancy line
                field = line.split(':')[0].strip()
                values = line.split(':')[1].strip()
                if 'impact' in values.lower():
                    try:
                        impact = float(values.split('impact')[1].strip().split()[0])
                    except (ValueError, IndexError):
                        impact = 0.2
                    reported_val = values.split('vs')[0].strip()
                    extracted_val = values.split('vs')[1].split('impact')[0].strip()
                    
                    discrepancies.append(Discrepancy(
                        field=field,
                        reported_value=reported_val,
                        extracted_value=extracted_val,
                        impact=impact
                    ))
            elif line and current_section == "notes":
                verification_notes.append(line)
        
        # Create verification result
        result = VerificationResult(
            company_name=reported.company_name,
            verification_status=status,
            overall_confidence=confidence * source_reliability.score,  # Adjust confidence based on source reliability
            source_url=reported.news_link,
            discrepancies=discrepancies,
            verification_notes="\n".join(verification_notes) if verification_notes else "No detailed notes provided."
        )
        
        return result

    def _generate_verification_notes(self, discrepancies: List[Discrepancy]) -> str:
        """Generate verification notes based on discrepancies."""
        if not discrepancies:
            return "All details verified successfully. No discrepancies found."
        
        notes = ["Verification completed with the following discrepancies:"]
        for d in discrepancies:
            notes.append(f"- {str(d)}")
        
        return "\n".join(notes)
            
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def _fetch_content(self, url: str) -> str:
        """Fetch content from URL with retry logic."""
        if url in self.cache:
            return self.cache[url]

        if not self.session:
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

        try:
            async with self.session.get(url, ssl=False, allow_redirects=True) as response:
                if response.status == 403:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    async with self.session.get(url, headers=headers, ssl=False) as response:
                        if response.status != 200:
                            raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")
                        content = await response.text()
                elif response.status != 200:
                    raise aiohttp.ClientError(f"HTTP {response.status}: {response.reason}")
                else:
                    content = await response.text()

            self.cache[url] = content
            return content
        except Exception as e:
            logging.error(f"Error fetching content from {url}: {str(e)}")
            raise

    def _save_batch_results(self, results: List[Dict[str, Any]]) -> None:
        """Save batch verification results to CSV files."""
        try:
            # Convert results to DataFrame
            df = pd.DataFrame(results)
            
            # Save detailed results
            df.to_csv(
                'reports/verification_results.csv',
                mode='a',
                header=not os.path.exists('reports/verification_results.csv'),
                index=False
            )
            
            # Save summary
            summary = df.groupby('verification_status').agg({
                'company_name': 'count',
                'overall_confidence': 'mean'
            }).round(2)
            
            summary.to_csv(
                'reports/verification_summary.csv',
                mode='a',
                header=not os.path.exists('reports/verification_summary.csv'),
                index=True
            )
            
        except Exception as e:
            logging.error(f"Error saving batch results: {str(e)}")
            raise

    async def generate_detailed_report(self, result: VerificationResult, source_reliability: SourceReliability) -> str:
        """Generate a detailed verification report."""
        prompt = f"""Generate a comprehensive verification report for this funding announcement:

Company: {result.company_name}
Status: {result.verification_status}
Confidence: {result.overall_confidence:.2f}

Source Assessment:
- Domain: {source_reliability.domain}
- Reliability Score: {source_reliability.score:.2f}
- Verified Publisher: {"Yes" if source_reliability.verification_status == VerificationStatus.VERIFIED else "No"}

Discrepancies Found: {len(result.discrepancies)}
{self._format_discrepancies_for_prompt(result.discrepancies)}

Please provide:
1. Executive Summary
2. Detailed Analysis of Findings
3. Risk Assessment
4. Recommendations
5. Confidence Level Explanation

Format the report in a clear, professional style suitable for business stakeholders."""

        try:
            response = await self._chat_completion(prompt)
            return response
        except Exception as e:
            logging.error(f"Error generating detailed report: {str(e)}")
            return self._generate_fallback_report(result, source_reliability)

    def _format_discrepancies_for_prompt(self, discrepancies: List[Discrepancy]) -> str:
        """Format discrepancies for the report prompt."""
        if not discrepancies:
            return "No discrepancies found."
        
        formatted = ["Discrepancy Details:"]
        for d in discrepancies:
            formatted.append(f"- {d.field}:")
            formatted.append(f"  Reported: {d.reported_value}")
            formatted.append(f"  Extracted: {d.extracted_value}")
            formatted.append(f"  Impact Score: {d.impact:.2f}")
        return "\n".join(formatted)

    def _generate_fallback_report(self, result: VerificationResult, source_reliability: SourceReliability) -> str:
        """Generate a basic report when AI generation fails."""
        return f"""FUNDING ANNOUNCEMENT VERIFICATION REPORT

EXECUTIVE SUMMARY
----------------
Company: {result.company_name}
Verification Status: {result.verification_status}
Overall Confidence: {result.overall_confidence:.2f}

SOURCE ASSESSMENT
----------------
Domain: {source_reliability.domain}
Reliability Score: {source_reliability.score:.2f}
Verified Publisher: {"Yes" if source_reliability.verification_status == VerificationStatus.VERIFIED else "No"}

VERIFICATION FINDINGS
-------------------
Number of Discrepancies: {len(result.discrepancies)}

{self._format_discrepancies_for_prompt(result.discrepancies)}

VERIFICATION NOTES
----------------
{result.verification_notes}

Report generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}"""

    async def _find_news_link(self, company_name: str, funding_info: str) -> Optional[str]:
        """Search for news link if none is provided."""
        search_query = f"{company_name} funding {funding_info} announcement"
        
        try:
            # Use the API to find relevant articles
            response = await self._chat_completion(f"""Find the most relevant news article about this funding:
            Company: {company_name}
            Funding Info: {funding_info}
            
            Return only the URL of the most reliable source found, or "None" if no reliable source is found.
            """)
            
            url = response.strip()
            if url.lower() == "none" or not url.startswith("http"):
                return None
                
            # Check if the URL is accessible
            try:
                content = await self._fetch_content(url)
                if content:
                    return url
            except:
                return None
                
            return None
        except Exception as e:
            logging.error(f"Error finding news link for {company_name}: {str(e)}")
            return None

    async def _save_results(self, results: List[VerificationResult]) -> None:
        """Save verification results to CSV files."""
        try:
            # Convert results to DataFrame
            df = pd.DataFrame([result.__dict__ for result in results])
            
            # Save detailed results
            df.to_csv(
                'reports/verification_results.csv',
                mode='a',
                header=not os.path.exists('reports/verification_results.csv'),
                index=False
            )
            
            # Save summary
            summary = df.groupby('verification_status').agg({
                'company_name': 'count',
                'overall_confidence': 'mean'
            }).round(2)
            
            summary.to_csv(
                'reports/verification_summary.csv',
                mode='a',
                header=not os.path.exists('reports/verification_summary.csv'),
                index=True
            )
            
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")
            raise

    async def _save_summary(self, summary: Dict[str, int]) -> None:
        """Save verification summary to CSV file."""
        try:
            # Convert summary to DataFrame
            df = pd.DataFrame([summary])
            
            # Save summary
            df.to_csv(
                'reports/verification_summary.csv',
                mode='a',
                header=not os.path.exists('reports/verification_summary.csv'),
                index=False
            )
            
        except Exception as e:
            logging.error(f"Error saving summary: {str(e)}")
            raise

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=5))
    async def _chat_completion(self, prompt: str) -> str:
        """Make an API call with reduced retry attempts and wait times."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Reduced temperature for faster, more consistent responses
                max_tokens=500  # Reduced max tokens for faster responses
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error in chat completion: {str(e)}")
            raise 