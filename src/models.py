from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, date
import os
import json
from pydantic import BaseModel, Field, validator
from enum import Enum

@dataclass
class FundingDetails:
    company: Optional[str]
    amount: Optional[float]
    round_type: Optional[str]
    date: Optional[str]
    additional_details: Optional[str]

@dataclass
class SourceReliability:
    domain: str
    is_verified_publisher: bool
    has_https: bool
    domain_age_score: float
    content_quality_score: float
    reliability_score: float

@dataclass
class Discrepancy:
    field: str
    reported_value: str
    extracted_value: str
    severity: float
    impact: str

@dataclass
class VerificationReport:
    verification_id: str
    timestamp: str
    company_name: str
    source_url: str
    source_reliability: SourceReliability
    reported_details: FundingDetails
    extracted_details: FundingDetails
    discrepancies: List[Discrepancy]
    confidence_scores: Dict[str, float]
    overall_confidence: float
    verification_status: str
    
    def generate_summary(self) -> str:
        """Generate a human-readable summary of the verification results."""
        summary = [
            f"Verification Report for {self.company_name}",
            f"ID: {self.verification_id}",
            f"Status: {self.verification_status}",
            f"Overall Confidence: {self.overall_confidence:.2f}",
            "",
            "Source Assessment:",
            f"- URL: {self.source_url}",
            f"- Domain: {self.source_reliability.domain}",
            f"- Verified Publisher: {'Yes' if self.source_reliability.is_verified_publisher else 'No'}",
            f"- Reliability Score: {self.source_reliability.reliability_score:.2f}",
            "",
            "Reported Details:",
            f"- Amount: ${self.reported_details.amount}M",
            f"- Round: {self.reported_details.round_type}",
            f"- Date: {self.reported_details.date}",
            "",
            "Extracted Details:",
            f"- Amount: ${self.extracted_details.amount}M",
            f"- Round: {self.extracted_details.round_type}",
            f"- Date: {self.extracted_details.date}",
            "",
            f"Discrepancies Found: {len(self.discrepancies)}",
        ]
        
        if self.discrepancies:
            summary.append("Discrepancy Details:")
            for d in self.discrepancies:
                summary.append(f"- {d.field}: {d.reported_value} vs {d.extracted_value}")
                summary.append(f"  Severity: {d.severity:.2f}, Impact: {d.impact}")
        
        return "\n".join(summary)

    def generate_detailed_report(self) -> str:
        """Generate a detailed human-readable report."""
        return f"""
FUNDING ANNOUNCEMENT VERIFICATION REPORT
======================================
Verification ID: {self.verification_id}
Generated: {self.timestamp}

COMPANY INFORMATION
------------------
Company: {self.company_name}

SOURCE ASSESSMENT
----------------
Source: {self.source_url}
Reliability Score: {self.source_reliability.reliability_score:.2f}
Domain Reputation: {self.source_reliability.domain_age_score:.2f}
Content Quality: {self.source_reliability.content_quality_score:.2f}

FUNDING DETAILS COMPARISON
------------------------
Reported Details:
- Amount: ${self.reported_details.amount}M
- Round: {self.reported_details.round_type or 'Not specified'}
- Date: {self.reported_details.date or 'Not specified'}

Extracted Details:
- Amount: ${self.extracted_details.amount}M
- Round: {self.extracted_details.round_type or 'Not specified'}
- Date: {self.extracted_details.date or 'Not specified'}

DISCREPANCIES FOUND
------------------
{self._format_discrepancies()}

CONFIDENCE ASSESSMENT
-------------------
{self._format_confidence_scores()}

Overall Confidence: {self.overall_confidence:.2f}

VERIFICATION RESULT
-----------------
Status: {self.verification_status.upper()}

Additional Notes:
- Source is {'' if self.source_reliability.is_verified_publisher else 'not '}a verified publisher
- Content quality indicators: {self.source_reliability.content_quality_score:.2f}/1.0
"""

    def _format_discrepancies(self) -> str:
        if not self.discrepancies:
            return "No discrepancies found."
        
        return "\n".join(
            f"- {d.field}: {d.reported_value} (reported) vs {d.extracted_value} (extracted)\n  Severity: {d.severity:.2f}\n  Impact: {d.impact}"
            for d in self.discrepancies
        )

    def _format_confidence_scores(self) -> str:
        return "\n".join(
            f"- {key}: {value:.2f}"
            for key, value in self.confidence_scores.items()
        )

    def save_to_file(self, directory: str = "reports") -> str:
        """Save the report to a file and return the filename."""
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename
        filename = f"{directory}/{self.company_name}_{self.verification_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save detailed text report
        with open(f"{filename}_report.txt", "w") as f:
            f.write(self.generate_detailed_report())
            
        # Save JSON data
        with open(f"{filename}_data.json", "w") as f:
            json.dump({
                'verification_id': self.verification_id,
                'timestamp': self.timestamp,
                'company_name': self.company_name,
                'source_url': self.source_url,
                'source_reliability': asdict(self.source_reliability),
                'reported_details': asdict(self.reported_details),
                'extracted_details': asdict(self.extracted_details),
                'discrepancies': [asdict(d) for d in self.discrepancies],
                'confidence_scores': self.confidence_scores,
                'overall_confidence': self.overall_confidence,
                'verification_status': self.verification_status
            }, f, indent=2, default=str)
            
        return filename

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"

class SourceReliability(BaseModel):
    domain: str
    score: float = Field(ge=0.0, le=1.0)
    is_verified_publisher: bool = False

    @validator('score')
    def validate_score(cls, v):
        if not 0 <= v <= 1:
            raise ValueError('Score must be between 0 and 1')
        return v

class Discrepancy(BaseModel):
    field: str
    reported_value: str
    extracted_value: str
    impact: float = Field(ge=0.0, le=1.0)

    def __str__(self):
        return f"{self.field}: Reported '{self.reported_value}' vs. Extracted '{self.extracted_value}' (Impact: {self.impact:.2f})"

class FundingDetails(BaseModel):
    company_name: str
    amount: float
    round_type: str
    date: date
    source_url: str

class ExtractedDetails(FundingDetails):
    confidence_score: float = Field(ge=0.0, le=1.0)
    source_reliability: SourceReliability
    discrepancies: List[Discrepancy] = []
    verification_status: VerificationStatus = VerificationStatus.PENDING
    verification_notes: Optional[str] = None

    def calculate_overall_confidence(self) -> float:
        if not self.discrepancies:
            return self.confidence_score * self.source_reliability.score
        
        total_impact = sum(d.impact for d in self.discrepancies)
        discrepancy_factor = 1 - (total_impact / len(self.discrepancies))
        return self.confidence_score * self.source_reliability.score * discrepancy_factor

    def generate_verification_notes(self) -> str:
        notes = [f"Verification Status: {self.verification_status}"]
        notes.append(f"Source Reliability: {self.source_reliability.domain} ({'Verified' if self.source_reliability.is_verified_publisher else 'Unverified'} publisher, Score: {self.source_reliability.score:.2f})")
        
        if self.discrepancies:
            notes.append("\nDiscrepancies found:")
            for discrepancy in self.discrepancies:
                notes.append(f"- {discrepancy}")
        
        return "\n".join(notes)

class VerificationResult(BaseModel):
    company_name: str
    verification_status: VerificationStatus
    overall_confidence: float
    source_url: str
    discrepancies: List[Discrepancy]
    verification_notes: str