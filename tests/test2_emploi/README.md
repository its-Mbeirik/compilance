# Test #2 — Contrat de Travail (CDI)

Test obligatoire n°2 du cahier des charges PFE :
*« Vérification de conformité des contrats de travail avec le Code du Travail,
la législation sociale et les conventions collectives. »*

## Fichiers

| Fichier | Rôle |
|---|---|
| `contrat_travail_test2.md` | CDI synthétique entre TECHNOVA SARL et un développeur, gravement non conforme |
| `expected_findings.md` | Ground truth — 17 non-conformités délibérées (10 critiques, 6 majeures, 1 mineure) |

## Catégories de violations couvertes

- Période d'essai abusive
- Durée du travail excessive + heures supplémentaires non rémunérées
- Salaire potentiellement sous-SMIG
- Congés payés insuffisants + jours fériés non majorés
- Congé maternité illégal + discrimination
- Régime maladie abusif
- Clause de non-concurrence excessive
- Atteinte à la liberté syndicale
- Propriété intellectuelle abusive
- Rupture sans préavis + clause pénale de démission
- Exclusion des tribunaux du travail
- CNSS optionnelle
- Mobilité géographique imposée
- Modification unilatérale des fonctions

Le système doit détecter ces 17 problèmes (vrais positifs) sans en inventer
d'autres (faux positifs).

## Usage

Identique à Test #1 : ingest corpus → upload via `/upload` (type "Contrat de travail") →
comparer à la ground truth pour calculer précision / rappel / F1.

## Recommandation

Pour la matrice de confusion finale, prévoir un **3e cas de test** : un contrat
conforme avec 2-3 anomalies subtiles, pour mesurer le taux de faux positifs sur
un contrat "presque correct" (plus représentatif de la réalité professionnelle).
