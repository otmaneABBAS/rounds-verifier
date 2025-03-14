import pandas as pd
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum

class VerificationStatus(Enum):
    VERIFIED = "Verified"
    UNVERIFIED = "Unverified"
    INCONCLUSIVE = "Inconclusive"

def load_verification_data(reports_dir: str = "reports") -> List[Dict]:
    """Load all verification data from JSON files in the reports directory."""
    verification_data = []
    for file in Path(reports_dir).glob("*_data.json"):
        with open(file, "r") as f:
            data = json.load(f)
            verification_data.append(data)
    return verification_data

def create_detailed_dataframe(verification_data: List[Dict]) -> pd.DataFrame:
    """Create a detailed DataFrame from verification data."""
    records = []
    
    for data in verification_data:
        # Determine verification status based on confidence and discrepancies
        confidence = data["overall_confidence"]
        num_discrepancies = len(data["discrepancies"])
        
        if confidence >= 0.8 and num_discrepancies == 0:
            status = VerificationStatus.VERIFIED.value
        elif confidence < 0.5 or num_discrepancies > 2:
            status = VerificationStatus.UNVERIFIED.value
        else:
            status = VerificationStatus.INCONCLUSIVE.value

        record = {
            "company_name": data["company_name"],
            "verification_id": data["verification_id"],
            "timestamp": data["timestamp"],
            "verification_status": status,
            "overall_confidence": data["overall_confidence"],
            "source_url": data["source_url"],
            
            # Supporting Evidence
            "source_reliability": {
                "domain": data["source_reliability"]["domain"],
                "is_verified_publisher": data["source_reliability"]["is_verified_publisher"],
                "has_https": data["source_reliability"]["has_https"],
                "domain_age_score": data["source_reliability"]["domain_age_score"],
                "content_quality_score": data["source_reliability"]["content_quality_score"]
            },
            
            # Reported vs Extracted Details
            "reported_details": {
                "amount": data["reported_details"]["amount"],
                "round_type": data["reported_details"]["round_type"],
                "date": data["reported_details"]["date"]
            },
            "extracted_details": {
                "amount": data["extracted_details"]["amount"],
                "round_type": data["extracted_details"]["round_type"],
                "date": data["extracted_details"]["date"]
            },
            
            # Confidence Scores
            "confidence_scores": {
                "source_reliability": data["confidence_scores"]["source_reliability"],
                "data_completeness": data["confidence_scores"]["data_completeness"],
                "data_consistency": data["confidence_scores"]["data_consistency"],
                "extraction_quality": data["confidence_scores"]["extraction_quality"],
                "discrepancy_impact": data["confidence_scores"]["discrepancy_impact"]
            },
            
            # Discrepancies
            "discrepancies": data["discrepancies"]
        }
        records.append(record)
    
    return pd.DataFrame(records)

def generate_excel_report(df: pd.DataFrame, output_path: str = "reports/verification_results.xlsx"):
    """Generate an Excel report with multiple sheets for different views of the data."""
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Summary sheet with verification status
        summary_df = df.groupby('verification_status').agg({
            'overall_confidence': ['count', 'mean'],
            'source_reliability': lambda x: x.apply(lambda y: y['content_quality_score']).mean()
        }).round(2)
        summary_df.columns = ['Number of Cases', 'Average Confidence', 'Average Source Quality']
        summary_df.to_excel(writer, sheet_name='Verification Summary')
        
        # Detailed results with supporting evidence
        detailed_df = df.copy()
        detailed_df['source_reliability'] = detailed_df['source_reliability'].apply(
            lambda x: f"Domain: {x['domain']}\nVerified Publisher: {x['is_verified_publisher']}\nContent Quality: {x['content_quality_score']:.2f}"
        )
        detailed_df['confidence_scores'] = detailed_df['confidence_scores'].apply(
            lambda x: f"Source Reliability: {x['source_reliability']:.2f}\nData Completeness: {x['data_completeness']:.2f}\nConsistency: {x['data_consistency']:.2f}"
        )
        detailed_df.to_excel(writer, sheet_name='Detailed Results', index=False)
        
        # Discrepancies analysis
        discrepancies_df = df[['company_name', 'verification_status', 'discrepancies']]
        discrepancies_df['discrepancy_count'] = discrepancies_df['discrepancies'].apply(len)
        discrepancies_df['discrepancy_details'] = discrepancies_df['discrepancies'].apply(
            lambda x: "\n".join(f"- {d['field']}: {d['reported_value']} vs {d['extracted_value']} (Severity: {d['severity']})"
                              for d in x)
        )
        discrepancies_df.to_excel(writer, sheet_name='Discrepancies', index=False)
        
        # Confidence metrics
        confidence_metrics = df[[
            'company_name', 'verification_status', 'overall_confidence',
            'source_reliability', 'confidence_scores'
        ]]
        confidence_metrics.to_excel(writer, sheet_name='Confidence Analysis', index=False)

def generate_reports():
    """Main function to generate all reports."""
    # Create reports directory if it doesn't exist
    os.makedirs("reports", exist_ok=True)
    
    # Load verification data
    verification_data = load_verification_data()
    
    if not verification_data:
        print("No verification data found in the reports directory.")
        return
    
    # Create detailed DataFrame
    df = create_detailed_dataframe(verification_data)
    
    # Save to CSV
    df.to_csv("reports/verification_detailed.csv", index=False)
    
    # Generate Excel report with multiple sheets
    generate_excel_report(df)
    
    # Print summary statistics
    print("\nVerification Summary Statistics:")
    print("-" * 30)
    print(f"Total Verifications: {len(df)}")
    print("\nStatus Breakdown:")
    status_counts = df['verification_status'].value_counts()
    for status, count in status_counts.items():
        print(f"- {status}: {count} ({count/len(df)*100:.1f}%)")
    print(f"\nAverage Confidence: {df['overall_confidence'].mean():.2f}")
    print(f"Total Discrepancies: {df['discrepancies'].apply(len).sum()}")
    print("\nReports generated:")
    print("1. reports/verification_detailed.csv")
    print("2. reports/verification_results.xlsx")

if __name__ == "__main__":
    generate_reports() 