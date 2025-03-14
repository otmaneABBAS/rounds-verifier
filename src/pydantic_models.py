from typing import List, Optional
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field

class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    PENDING = "PENDING"

class SourceReliability(BaseModel):
    domain: str
    score: float
    verification_status: VerificationStatus

class FundingAnnouncement(BaseModel):
    id: str
    company_name: str
    company_url: str
    round_type: str
    amount: float
    year: int
    month: Optional[int]
    investors: Optional[str]
    news_link: Optional[str]

class Discrepancy(BaseModel):
    field: str
    reported_value: str
    extracted_value: str
    impact: float

class VerificationResult(BaseModel):
    company_name: str
    verification_status: VerificationStatus
    overall_confidence: float
    news_link: Optional[str]
    source_reliability: Optional[SourceReliability]
    discrepancies: List[Discrepancy]
    verification_notes: str

    def calculate_confidence(self) -> float:
        """Calculate overall confidence based on source reliability and discrepancies."""
        if not self.source_reliability:
            return 0.0
        
        base_confidence = self.source_reliability.score
        discrepancy_penalty = sum(d.impact for d in self.discrepancies)
        
        return max(0.0, min(1.0, base_confidence - discrepancy_penalty)) 