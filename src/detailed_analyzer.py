import pandas as pd
import numpy as np
from datetime import datetime

def load_verification_data():
    """Load the verification results and extracted details"""
    extracted_df = pd.read_csv("results/extracted_details.csv")
    verification_df = pd.read_csv("results/verification_results.csv")
    return extracted_df, verification_df

def analyze_amount_differences(extracted_df):
    """Analyze the differences between reported and extracted amounts"""
    extracted_df['Amount_Difference'] = abs(
        pd.to_numeric(extracted_df['Reported Amount'], errors='coerce') - 
        pd.to_numeric(extracted_df['Extracted Amount'], errors='coerce')
    )
    extracted_df['Amount_Difference_Percentage'] = (
        extracted_df['Amount_Difference'] / 
        pd.to_numeric(extracted_df['Reported Amount'], errors='coerce')
    ) * 100
    
    return {
        'mean_difference': extracted_df['Amount_Difference'].mean(),
        'median_difference': extracted_df['Amount_Difference'].median(),
        'mean_percentage_diff': extracted_df['Amount_Difference_Percentage'].mean(),
        'median_percentage_diff': extracted_df['Amount_Difference_Percentage'].median()
    }

def analyze_round_type_matches(extracted_df):
    """Analyze the matches between reported and extracted round types"""
    extracted_df['Round_Match'] = (
        extracted_df['Reported Round'].str.lower() == 
        extracted_df['Extracted Round'].str.lower()
    )
    
    return {
        'total_matches': extracted_df['Round_Match'].sum(),
        'match_rate': (extracted_df['Round_Match'].sum() / len(extracted_df)) * 100
    }

def perform_detailed_analysis():
    """Perform detailed analysis of verification results"""
    extracted_df, verification_df = load_verification_data()
    
    # Merge dataframes
    analysis_df = pd.merge(extracted_df, verification_df, on='Company')
    
    # 1. Compare Extracted Details
    amount_analysis = analyze_amount_differences(analysis_df)
    round_analysis = analyze_round_type_matches(analysis_df)
    
    # 2. Verification Logic Analysis
    verification_analysis = {
        'total_entries': len(analysis_df),
        'verified_entries': len(analysis_df[analysis_df['Verification Status'] == 'verified']),
        'verification_rate': (len(analysis_df[analysis_df['Verification Status'] == 'verified']) / len(analysis_df)) * 100,
        'mean_confidence': analysis_df['Confidence Score'].mean(),
        'median_confidence': analysis_df['Confidence Score'].median()
    }
    
    # Create detailed results
    detailed_results = []
    for _, row in analysis_df.iterrows():
        result = {
            'Company': row['Company'],
            'Reported_Amount': row['Reported Amount'],
            'Extracted_Amount': row['Extracted Amount'],
            'Amount_Difference': abs(
                pd.to_numeric(row['Reported Amount'], errors='coerce') - 
                pd.to_numeric(row['Extracted Amount'], errors='coerce')
            ),
            'Amount_Difference_Percentage': (
                abs(pd.to_numeric(row['Reported Amount'], errors='coerce') - 
                    pd.to_numeric(row['Extracted Amount'], errors='coerce')) / 
                pd.to_numeric(row['Reported Amount'], errors='coerce')
            ) * 100 if pd.to_numeric(row['Reported Amount'], errors='coerce') != 0 else np.nan,
            'Reported_Round': row['Reported Round'],
            'Extracted_Round': row['Extracted Round'],
            'Round_Match': row['Reported Round'].lower() == row['Extracted Round'].lower() if pd.notna(row['Reported Round']) and pd.notna(row['Extracted Round']) else False,
            'Confidence_Score': row['Confidence Score'],
            'Verification_Status': row['Verification Status'],
            'Matches': row['Matches'],
            'Mismatches': row['Mismatches'],
            'News_URL': row['News URL'],
            'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        detailed_results.append(result)
    
    # Save detailed results
    detailed_df = pd.DataFrame(detailed_results)
    detailed_df.to_csv("results/detailed_analysis.csv", index=False)
    
    # Create summary report
    summary = {
        'Analysis_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'Total_Entries': verification_analysis['total_entries'],
        'Verified_Entries': verification_analysis['verified_entries'],
        'Verification_Rate': verification_analysis['verification_rate'],
        'Mean_Confidence_Score': verification_analysis['mean_confidence'],
        'Median_Confidence_Score': verification_analysis['median_confidence'],
        'Mean_Amount_Difference': amount_analysis['mean_difference'],
        'Median_Amount_Difference': amount_analysis['median_difference'],
        'Mean_Amount_Difference_Percentage': amount_analysis['mean_percentage_diff'],
        'Median_Amount_Difference_Percentage': amount_analysis['median_percentage_diff'],
        'Round_Type_Matches': round_analysis['total_matches'],
        'Round_Type_Match_Rate': round_analysis['match_rate']
    }
    
    # Save summary
    summary_df = pd.DataFrame([summary])
    summary_df.to_csv("results/analysis_summary.csv", index=False)
    
    return detailed_df, summary_df

if __name__ == "__main__":
    print("Starting detailed analysis...")
    detailed_df, summary_df = perform_detailed_analysis()
    print("\nAnalysis complete!")
    print(f"Detailed results saved to: results/detailed_analysis.csv")
    print(f"Summary saved to: results/analysis_summary.csv")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Total Entries Analyzed: {summary_df['Total_Entries'].iloc[0]}")
    print(f"Verification Rate: {summary_df['Verification_Rate'].iloc[0]:.1f}%")
    print(f"Mean Confidence Score: {summary_df['Mean_Confidence_Score'].iloc[0]:.3f}")
    print(f"Round Type Match Rate: {summary_df['Round_Type_Match_Rate'].iloc[0]:.1f}%")
    print(f"Median Amount Difference: {summary_df['Median_Amount_Difference'].iloc[0]:.2f}M USD")
    print(f"Median Amount Difference Percentage: {summary_df['Median_Amount_Difference_Percentage'].iloc[0]:.1f}%") 