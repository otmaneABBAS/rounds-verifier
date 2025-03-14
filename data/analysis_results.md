# Résultats de l'Analyse des Données

## Structure des Données

### Colonnes disponibles :
- Company ID : int64
- Name : object (texte)
- Website : object (texte)
- Round : object (texte)
- Amount (USD M) : float64
- Year : int64
- Month : float64
- Investors : object (texte)
- News link : object (texte)
- Standardised round label : object (texte)

### Statistiques Descriptives :
- Nombre total d'entrées : 15,181
- Période couverte : 1994 à 2025
- Montant moyen : 2.27M USD
- Montant minimum : 0M USD
- Montant maximum : 99M USD

### Valeurs Manquantes :
- News link : 13,863 manquants (91%)
- Standardised round label : 15,181 manquants (100%)
- Investors : 8,749 manquants (58%)
- Website : 40 manquants
- Month : 12 manquants

## Visualisations
Les graphiques sont sauvegardés dans le fichier 'funding_analysis.png' dans le dossier data.

## Implications pour la Vérification
1. Seulement 9% des rounds ont un lien vers une news
2. Les montants varient considérablement (0 à 99M USD)
3. Les données récentes (2016-2025) sont plus nombreuses
4. Beaucoup d'informations manquantes sur les investisseurs 