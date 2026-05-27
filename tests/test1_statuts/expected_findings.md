# Test #1 — Ground Truth: Non-conformités attendues

Ce fichier liste les non-conformités **délibérément insérées** dans `statuts_technova_sarl.md`.
Il sert de **référence (gold standard)** pour évaluer le système agentique :
matrice de confusion, précision, rappel, F1 (Phase 5 du cahier des charges).

**Format :** chaque finding contient `id`, `article` visé, `sévérité`, `règle juridique`,
`description`, et `correction attendue`. Le système doit produire des findings
sémantiquement équivalents pour être comptés comme **Vrais Positifs**.

---

## NC-001 — Capital social inférieur au minimum légal
- **Article visé :** Article 7
- **Sévérité :** CRITIQUE
- **Base légale :** Code de Commerce mauritanien (Loi n° 2000-05), dispositions sur le capital minimum des SARL
- **Description :** Le capital social est fixé à 80.000 MRU, ce qui est inférieur au minimum légal requis pour la constitution d'une SARL en Mauritanie.
- **Correction :** Porter le capital à au moins le minimum légal en vigueur.

## NC-002 — Objet social rédigé en termes trop généraux
- **Article visé :** Article 3
- **Sévérité :** MAJEURE
- **Base légale :** Principe de spécialité de l'objet social (Code de Commerce)
- **Description :** L'objet social « toutes activités commerciales, industrielles et de services » est trop large et vague pour identifier précisément l'activité réelle de la société.
- **Correction :** Préciser les activités principales et secondaires.

## NC-003 — Cession libre des parts aux tiers non autorisée
- **Article visé :** Article 8
- **Sévérité :** CRITIQUE
- **Base légale :** Code de Commerce — régime de cession des parts en SARL
- **Description :** L'article 8 prévoit que les parts sont « librement cessibles » au profit de tiers. La SARL est une société fermée : la cession des parts à des non-associés requiert l'agrément de la majorité qualifiée des associés (généralement 3/4 du capital).
- **Correction :** Soumettre la cession aux tiers à l'agrément préalable des associés représentant au moins 3/4 du capital.

## NC-004 — Transmission par décès sans procédure d'agrément
- **Article visé :** Article 9
- **Sévérité :** MAJEURE
- **Base légale :** Code de Commerce — transmission des parts pour cause de décès
- **Description :** Les héritiers deviennent associés « sans formalité particulière ». Cette clause peut contrevenir aux exigences d'agrément si les statuts doivent prévoir un mécanisme protecteur pour les associés survivants.
- **Correction :** Prévoir une procédure d'agrément ou de rachat des parts par les associés survivants.

## NC-005 — Pouvoirs du gérant excessifs sans contrôle
- **Article visé :** Article 11
- **Sévérité :** MAJEURE
- **Base légale :** Code de Commerce — limitation des pouvoirs du gérant
- **Description :** Le gérant peut sans autorisation préalable vendre des immeubles, contracter des emprunts illimités, et donner des cautions. Ces actes graves doivent normalement être soumis à l'autorisation préalable des associés.
- **Correction :** Subordonner les actes de disposition importants (vente immobilière, emprunts au-delà d'un seuil, cautionnements) à une décision collective des associés.

## NC-006 — Auto-fixation de la rémunération du gérant
- **Article visé :** Article 12
- **Sévérité :** CRITIQUE
- **Base légale :** Code de Commerce — conflit d'intérêts, principe de la décision collective
- **Description :** La rémunération du gérant ne peut être fixée par lui-même. Il s'agit d'un conflit d'intérêts manifeste : cette décision relève des associés en assemblée.
- **Correction :** « La rémunération du gérant est fixée par décision collective des associés. »

## NC-007 — Majorité insuffisante pour les modifications statutaires
- **Article visé :** Article 14
- **Sévérité :** CRITIQUE
- **Base légale :** Code de Commerce — règles de majorité pour la modification des statuts d'une SARL
- **Description :** Les modifications des statuts ne peuvent être adoptées à la « majorité simple ». La loi exige une majorité qualifiée (typiquement 3/4 des parts sociales).
- **Correction :** « Les décisions emportant modification des statuts sont prises à la majorité des associés représentant au moins les trois quarts du capital social. »

## NC-008 — Absence de clause sur le commissaire aux comptes
- **Article visé :** (clause manquante)
- **Sévérité :** MAJEURE
- **Base légale :** Code de Commerce — désignation obligatoire d'un commissaire aux comptes au-delà de certains seuils
- **Description :** Les statuts ne prévoient aucune clause relative à la désignation d'un commissaire aux comptes, alors qu'une telle désignation est obligatoire pour les SARL dépassant certains seuils (chiffre d'affaires, total bilan, effectif).
- **Correction :** Insérer un article prévoyant la désignation d'un commissaire aux comptes lorsque les seuils légaux sont franchis.

## NC-009 — Absence de mention de l'immatriculation au Registre du Commerce
- **Article visé :** (clause manquante)
- **Sévérité :** MINEURE
- **Base légale :** Code de Commerce — formalités de publicité
- **Description :** Les statuts ne mentionnent pas explicitement l'obligation d'immatriculation au Registre du Commerce et des Sociétés.
- **Correction :** Ajouter une mention explicite des formalités d'immatriculation.

## NC-010 — Durée du mandat de gérant non bornée
- **Article visé :** Article 10
- **Sévérité :** MINEURE
- **Base légale :** Pratique notariale et Code de Commerce
- **Description :** Le gérant est nommé pour une « durée indéterminée ». Bien que toléré, il est recommandé de fixer une durée déterminée (3 à 6 ans renouvelables) avec procédure de renouvellement.
- **Correction :** Fixer un mandat à durée déterminée renouvelable.

---

## Récapitulatif

| Sévérité | Nombre de findings |
|---|---|
| CRITIQUE | 4 (NC-001, NC-003, NC-006, NC-007) |
| MAJEURE | 4 (NC-002, NC-004, NC-005, NC-008) |
| MINEURE | 2 (NC-009, NC-010) |
| **Total** | **10** |

**Articles avec clauses conformes (à NE PAS flagger — pour mesurer les Faux Positifs) :**
Articles 1, 2, 4, 5, 6, 13 (partie ordinaire), 15, 16, 17, 18.
