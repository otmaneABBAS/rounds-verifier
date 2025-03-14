import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from .data_operations import load_csv

def analyze_data_structure(file_path: str):
    """Analyze the structure of the dataset"""
    df = load_csv(file_path)
    if df is None:
        return
    
    print("\n=== Structure des Données ===")
    print("\nColonnes disponibles:")
    for col in df.columns:
        print(f"- {col}: {df[col].dtype}")
    
    print("\nAperçu des données:")
    print(df.head())
    
    print("\nStatistiques descriptives:")
    print(df.describe())
    
    print("\nValeurs manquantes par colonne:")
    print(df.isnull().sum())
    return df

def analyze_funding_rounds(df: pd.DataFrame):
    """Analyze funding rounds distribution"""
    print("\n=== Analyse des Rounds de Financement ===")
    
    print("\nDistribution des types de rounds:")
    print(df['Round'].value_counts())
    
    print("\nMontant moyen par type de round:")
    print(df.groupby('Round')['Amount (USD M)'].mean().sort_values(ascending=False))
    
    print("\nNombre de rounds par année:")
    print(df['Year'].value_counts().sort_index())
    
    print("\nPourcentage de rounds avec news link:")
    has_news = (~df['News link'].isna()).mean() * 100
    print(f"{has_news:.2f}% des rounds ont un lien vers une news")

def create_visualizations(df: pd.DataFrame):
    """Create visualizations for funding analysis"""
    plt.figure(figsize=(12, 6))
    
    # Distribution des montants de financement
    plt.subplot(1, 2, 1)
    sns.histplot(data=df, x='Amount (USD M)', bins=50)
    plt.title('Distribution des Montants de Financement')
    plt.xlabel('Montant (USD M)')
    
    # Évolution temporelle
    plt.subplot(1, 2, 2)
    yearly_amounts = df.groupby('Year')['Amount (USD M)'].sum()
    yearly_amounts.plot(kind='bar')
    plt.title('Montant Total de Financement par Année')
    plt.xlabel('Année')
    plt.ylabel('Montant Total (USD M)')
    
    plt.tight_layout()
    plt.savefig('data/funding_analysis.png')
    print("\nGraphiques sauvegardés dans 'data/funding_analysis.png'")

if __name__ == "__main__":
    input_path = "data/sample.csv"
    df = analyze_data_structure(input_path)
    if df is not None:
        analyze_funding_rounds(df)
        create_visualizations(df)
    