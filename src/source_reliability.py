from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import tldextract
import re
from dataclasses import dataclass

@dataclass
class SourceReliability:
    """Class for storing source reliability metrics."""
    domain: str
    is_verified_publisher: bool
    has_https: bool
    domain_age_score: float
    content_quality_score: float
    reliability_score: float

class SourceReliability(BaseModel):
    """Model for evaluating the reliability of a news source."""
    domain: str = Field(description="The domain name of the news source")
    is_verified_publisher: bool = Field(description="Whether the source is a verified news publisher")
    has_https: bool = Field(description="Whether the source uses HTTPS")
    domain_age_score: float = Field(description="Score based on domain age and reputation")
    content_quality_score: float = Field(description="Score based on content quality indicators")
    
    @property
    def reliability_score(self) -> float:
        """Calculate overall reliability score."""
        score = 1.0
        
        # Base reliability from domain reputation
        score *= self.domain_age_score
        
        # Verified publisher bonus
        if self.is_verified_publisher:
            score *= 1.2
            
        # HTTPS security bonus
        if self.has_https:
            score *= 1.1
            
        # Content quality impact
        score *= self.content_quality_score
        
        return min(1.0, score)

    @classmethod
    def evaluate_source(cls, url: str, content: str) -> 'SourceReliability':
        """Evaluate a news source based on URL and content."""
        # Extract domain
        ext = tldextract.extract(url)
        domain = f"{ext.domain}.{ext.suffix}"
        
        # Check HTTPS
        has_https = url.startswith('https://')
        
        # Evaluate domain reputation (simplified)
        reputable_domains = {
            'techcrunch.com': 0.9,
            'reuters.com': 1.0,
            'bloomberg.com': 1.0,
            'wsj.com': 1.0,
            'ft.com': 1.0,
            'cnbc.com': 0.9,
            'venturebeat.com': 0.8,
            'crunchbase.com': 0.85
        }
        domain_score = reputable_domains.get(domain, 0.6)
        
        # Content quality checks
        quality_indicators = [
            len(content) > 200,  # Minimum length
            bool(re.search(r'\$\d+(?:\.\d+)?[MBmb]', content)),  # Contains funding amount
            bool(re.search(r'(?:Series|Seed|Round)', content)),  # Contains round information
            bool(re.search(r'\b(?:announced|secured|raised|closed)\b', content)),  # Contains funding verbs
            not bool(re.search(r'(?:click here|buy now|advertisement)', content))  # No spam indicators
        ]
        content_score = sum(1 for x in quality_indicators if x) / len(quality_indicators)
        
        return cls(
            domain=domain,
            is_verified_publisher=domain in reputable_domains,
            has_https=has_https,
            domain_age_score=domain_score,
            content_quality_score=content_score
        ) 