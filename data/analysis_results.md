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

# Analyse des Résultats de Vérification

## Seuils de Confiance

Le système utilise trois niveaux de vérification basés sur le score de confiance :

- **VERIFIED** : ≥ 80% (0.8)
  - Haute confiance dans les détails de l'annonce
  - Sources fiables multiples
  - Aucune différence significative

- **PARTIALLY_VERIFIED** : 60-79% (0.6-0.79)
  - Certains détails confirmés
  - Différences mineures présentes
  - Disponibilité limitée des sources

- **UNVERIFIED** : < 60% (< 0.6)
  - Différences majeures trouvées
  - Sources non fiables ou insuffisantes
  - Informations incohérentes

## Composantes du Score

Le score final est calculé en combinant plusieurs facteurs avec leurs poids respectifs :

1. **Fiabilité de la Source** (30%)
   - Évaluation de la réputation du domaine
   - Vérification du statut de l'éditeur
   - Âge et historique du domaine

2. **Cohérence des Données** (30%)
   - Comparaison des informations rapportées vs extraites
   - Vérification de la cohérence interne
   - Validation des détails clés

3. **Complétude des Données** (20%)
   - Présence de tous les champs requis
   - Qualité des informations fournies
   - Couverture des détails importants

4. **Qualité de l'Extraction** (10%)
   - Précision de l'analyse du contenu
   - Fiabilité de l'extraction des données
   - Qualité du traitement automatique

5. **Impact des Différences** (10%)
   - Sévérité des différences trouvées
   - Nombre de différences
   - Impact sur la fiabilité globale

## Calcul du Score

Le score final est calculé selon la formule suivante :

```python
# Score de base = fiabilité de la source
base_confidence = source_reliability.overall_score

# Facteur de différence basé sur les pires différences trouvées
if discrepancies:
    max_impact = max(d.impact for d in discrepancies)
    discrepancy_factor = 1 - (max_impact * 0.8)
else:
    discrepancy_factor = 1.0

# Score final
overall_confidence = base_confidence * discrepancy_factor
```

## Interprétation des Résultats

Les résultats sont présentés dans les rapports avec :
- Le score global de confiance
- Les scores individuels pour chaque composante
- Les différences trouvées et leur impact
- Le statut de vérification final
- Des notes détaillées sur la vérification 