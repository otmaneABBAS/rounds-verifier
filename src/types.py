from dataclasses import dataclass
from typing import Optional, Dict, Any, List

@dataclass
class ExtractedDetails:
    """Details extracted from funding announcement content."""
    company_name: str
    amount: float
    round_type: str
    date: str
    investors: Optional[List[str]] = None
    description: Optional[str] = None

@dataclass
class SourceReliability:
    """Assessment of source reliability."""
    domain: str
    is_verified_publisher: bool
    reliability_score: float
    content_quality_score: float
    overall_score: float

@dataclass
class Discrepancy:
    """Represents a discrepancy between reported and extracted details."""
    field: str
    reported_value: Any
    extracted_value: Any
    impact: float  # Impact score between 0 and 1

@dataclass
class VerificationResult:
    """Result of funding announcement verification."""
    company_name: str
    verification_status: str  # VERIFIED, PARTIALLY_VERIFIED, UNVERIFIED
    overall_confidence: float
    source_url: str
    source_reliability: SourceReliability
    reported_details: Dict[str, Any]
    extracted_details: ExtractedDetails
    discrepancies: List[Discrepancy]
    verification_notes: str 