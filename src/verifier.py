import logging
from typing import Dict, Any, List
import os
from .types import ExtractedDetails, SourceReliability, Discrepancy, VerificationResult
from .content_analyzer import ContentAnalyzer

class FundingVerifier:
    def __init__(self):
        """Initialize the funding verifier."""
        self.confidence_thresholds = {
            'VERIFIED': 0.8,
            'PARTIALLY_VERIFIED': 0.5
        }
    
    def verify_announcement(
        self,
        company: str,
        amount: float,
        round_type: str,
        date: str,
        source_url: str,
        content: str
    ) -> Dict[str, Any]:
        """Verify a funding announcement."""
        try:
            # Create content analyzer instance
            content_analyzer = ContentAnalyzer(api_key=os.getenv('OPENAI_API_KEY'))
            
            # Extract details and assess reliability
            extracted_details, source_reliability = content_analyzer.analyze_content(
                content=content,
                source_url=source_url
            )
            
            # Find discrepancies
            discrepancies = self._find_discrepancies(
                reported={
                    'company': company,
                    'amount': amount,
                    'round_type': round_type,
                    'date': date
                },
                extracted=extracted_details
            )
            
            # Calculate confidence scores
            confidence_scores = self._calculate_confidence_scores(
                source_reliability=source_reliability,
                discrepancies=discrepancies
            )
            
            # Determine verification status
            status = self._determine_verification_status(
                overall_confidence=confidence_scores['overall']
            )
            
            # Create verification notes
            notes = self._generate_verification_notes(
                status=status,
                discrepancies=discrepancies,
                source_reliability=source_reliability
            )
            
            # Create verification result
            result = VerificationResult(
                company_name=company,
                verification_status=status,
                overall_confidence=confidence_scores['overall'],
                source_url=source_url,
                source_reliability=source_reliability,
                reported_details={
                    'company': company,
                    'amount': amount,
                    'round_type': round_type,
                    'date': date
                },
                extracted_details=extracted_details,
                discrepancies=discrepancies,
                verification_notes=notes
            )
            
            return result.__dict__
            
        except Exception as e:
            logging.error(f"Error verifying announcement: {str(e)}")
            raise
    
    def _find_discrepancies(
        self,
        reported: Dict[str, Any],
        extracted: ExtractedDetails
    ) -> List[Discrepancy]:
        """Find discrepancies between reported and extracted details."""
        discrepancies = []
        
        # Compare company names
        if reported['company'].lower() != extracted.company_name.lower():
            discrepancies.append(Discrepancy(
                field='company',
                reported_value=reported['company'],
                extracted_value=extracted.company_name,
                impact=0.8  # High impact
            ))
        
        # Compare amounts (allow 5% difference)
        amount_diff = abs(reported['amount'] - extracted.amount) / reported['amount']
        if amount_diff > 0.05:
            discrepancies.append(Discrepancy(
                field='amount',
                reported_value=reported['amount'],
                extracted_value=extracted.amount,
                impact=0.6  # Medium-high impact
            ))
        
        # Compare round types
        if reported['round_type'].lower() != extracted.round_type.lower():
            discrepancies.append(Discrepancy(
                field='round_type',
                reported_value=reported['round_type'],
                extracted_value=extracted.round_type,
                impact=0.4  # Medium impact
            ))
        
        # Compare dates
        if reported['date'] != extracted.date:
            discrepancies.append(Discrepancy(
                field='date',
                reported_value=reported['date'],
                extracted_value=extracted.date,
                impact=0.3  # Medium-low impact
            ))
        
        return discrepancies
    
    def _calculate_confidence_scores(
        self,
        source_reliability: SourceReliability,
        discrepancies: List[Discrepancy]
    ) -> Dict[str, float]:
        """Calculate confidence scores for the verification."""
        # Base confidence from source reliability
        base_confidence = source_reliability.overall_score
        
        # Calculate impact of discrepancies
        if discrepancies:
            max_impact = max(d.impact for d in discrepancies)
            discrepancy_factor = 1 - (max_impact * 0.8)  # Reduce confidence based on worst discrepancy
        else:
            discrepancy_factor = 1.0
        
        # Calculate overall confidence
        overall_confidence = base_confidence * discrepancy_factor
        
        return {
            'source_reliability': source_reliability.overall_score,
            'discrepancy_factor': discrepancy_factor,
            'overall': overall_confidence
        }
    
    def _determine_verification_status(self, overall_confidence: float) -> str:
        """Determine verification status based on confidence score."""
        if overall_confidence >= self.confidence_thresholds['VERIFIED']:
            return 'VERIFIED'
        elif overall_confidence >= self.confidence_thresholds['PARTIALLY_VERIFIED']:
            return 'PARTIALLY_VERIFIED'
        else:
            return 'UNVERIFIED'
    
    def _generate_verification_notes(
        self,
        status: str,
        discrepancies: List[Discrepancy],
        source_reliability: SourceReliability
    ) -> str:
        """Generate human-readable verification notes."""
        notes = []
        
        # Add status note
        notes.append(f"Verification Status: {status}")
        
        # Add source reliability note
        notes.append(
            f"Source Reliability: {source_reliability.domain} "
            f"({'Verified' if source_reliability.is_verified_publisher else 'Unverified'} publisher, "
            f"Score: {source_reliability.overall_score:.2f})"
        )
        
        # Add discrepancy notes
        if discrepancies:
            notes.append("\nDiscrepancies found:")
            for d in discrepancies:
                notes.append(
                    f"- {d.field.title()}: Reported '{d.reported_value}' vs. "
                    f"Extracted '{d.extracted_value}' (Impact: {d.impact:.2f})"
                )
        else:
            notes.append("\nNo discrepancies found.")
        
        return "\n".join(notes) 