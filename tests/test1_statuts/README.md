# Test #1 — Statuts d'entreprise (SARL)

Test obligatoire n°1 du cahier des charges PFE :
*« Vérification complète des statuts d'une entreprise contre le Code des Sociétés et les lois applicables. »*

## Fichiers

| Fichier | Rôle |
|---|---|
| `statuts_technova_sarl.md` | Document d'entrée — statuts synthétiques d'une SARL mauritanienne |
| `expected_findings.md` | Ground truth — 10 non-conformités délibérément insérées |

## Usage

1. Le système agentique ingère `statuts_technova_sarl.md`.
2. Il produit une liste de findings (clauses non conformes, manquantes, contradictoires).
3. On compare les findings du système à `expected_findings.md` pour calculer :
   - **Vrais Positifs (TP)** : non-conformités détectées et présentes dans la ground truth
   - **Faux Positifs (FP)** : findings du système absents de la ground truth
   - **Faux Négatifs (FN)** : non-conformités de la ground truth non détectées
   - **Précision, Rappel, F1**

## Note

Ce document est **synthétique**. Pour la soutenance, il faudra idéalement le remplacer
par de vrais statuts notariés (anonymisés), et faire valider la ground truth
par un juriste expert (cf. Phase 5 du cahier des charges).

Conversion possible en PDF/DOCX via Pandoc :
```bash
pandoc statuts_technova_sarl.md -o statuts_technova_sarl.pdf
pandoc statuts_technova_sarl.md -o statuts_technova_sarl.docx
```
