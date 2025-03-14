"""
Funding Announcement Verification System

This package provides tools for verifying funding announcements by:
1. Analyzing content from news sources
2. Extracting and comparing funding details
3. Assessing source reliability
4. Generating detailed verification reports
"""

from .pydantic_models import (
    FundingAnnouncement,
    SourceReliability,
    Discrepancy,
    VerificationResult,
    VerificationStatus
)
from .ai_verifier import AIFundingVerifier

__version__ = "0.1.0"
__all__ = [
    'FundingAnnouncement',
    'SourceReliability',
    'Discrepancy',
    'VerificationResult',
    'VerificationStatus',
    'AIFundingVerifier'
]


