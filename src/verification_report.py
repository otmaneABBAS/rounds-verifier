from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from .models import FundingDetails, SourceReliability, Discrepancy
from .source_reliability import SourceReliability
from dataclasses import dataclass, asdict

class DiscrepancyDetail(BaseModel):
    """Details about a discrepancy between reported and extracted information."""
    field: str = Field(description="The field where the discrepancy was found")
    reported_value: str = Field(description="The value as reported")
    extracted_value: str = Field(description="The value as extracted")
    severity: float = Field(description="Severity score of the discrepancy (0-1)")
    impact: str = Field(description="Description of the impact of this discrepancy")

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
    
    def model_dump(self) -> Dict:
        """Convert the report to a dictionary."""
        return {
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
        }
    
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
        import os
        import json
        from datetime import datetime
        
        # Create directory if it doesn't exist
        os.makedirs(directory, exist_ok=True)
        
        # Generate filename
        filename = f"{directory}/{self.company_name}_{self.verification_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Save detailed text report
        with open(f"{filename}_report.txt", "w") as f:
            f.write(self.generate_detailed_report())
            
        # Save JSON data
        with open(f"{filename}_data.json", "w") as f:
            json.dump(self.model_dump(), f, indent=2, default=str)
            
        return filename 