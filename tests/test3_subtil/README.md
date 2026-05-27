# Test #3 — Contrat majoritairement conforme (mesure de précision)

Contrat de travail synthétique d'une auditrice senior chez SAHARA CONSULTING SARL.
Le contrat est rédigé de manière professionnelle et conforme dans son ensemble,
mais comporte **2 anomalies subtiles** délibérées :

1. **Clause de non-concurrence sans contrepartie financière** (MAJEURE)
2. **Renouvellement de période d'essai imprécis** (MINEURE)

## Pourquoi ce 3e test ?

Tests 1 et 2 sont délibérément truffés de violations grossières — ils mesurent
si le système **détecte** bien les non-conformités (rappel).

Test #3 mesure l'inverse : si le système **hallucine** des problèmes là où il
n'y en a pas (précision). C'est plus représentatif de la réalité métier où la
majorité des contrats sont rédigés correctement.

| Test | Mesure principale | Findings attendus |
|---|---|---|
| Test #1 (statuts SARL) | Rappel | 10 |
| Test #2 (CDI grossier) | Rappel | 17 |
| **Test #3 (CDI subtil)** | **Précision** | **2** |

Combiné, on peut calculer le F1 global du système.
