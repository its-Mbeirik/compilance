# Test #2 — Ground Truth: Non-conformités attendues

Ground truth pour `contrat_travail_test2.md`. Ce contrat de travail viole
gravement et délibérément le Code du Travail mauritanien et la Convention
Collective Générale du Travail (CCGT). Il sert à évaluer la précision et le
rappel du système agentique sur les contrats d'emploi (Phase 5, Test n°2).

---

## NC-001 — Période d'essai abusivement longue
- **Article visé :** Article 2
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail (CT) — durée maximale de la période d'essai (typiquement 1 à 6 mois selon la catégorie)
- **Description :** Une période d'essai de **12 mois** excède très largement la durée maximale légale autorisée pour un contrat CDI en Mauritanie. Pour un cadre/employé qualifié, le plafond est généralement de 6 mois maximum.
- **Correction :** Ramener la période d'essai à la durée maximale légale (3 mois pour les employés, 6 mois pour les cadres) avec possibilité d'un seul renouvellement écrit.

## NC-002 — Durée hebdomadaire de travail excessive
- **Article visé :** Article 5
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail mauritanien — durée légale du travail (40 heures/semaine)
- **Description :** La durée fixée à **52 heures par semaine** dépasse la durée légale. La durée légale du travail en Mauritanie est de 40 heures hebdomadaires.
- **Correction :** Fixer la durée hebdomadaire à 40 heures et prévoir un régime conforme pour les heures supplémentaires.

## NC-003 — Absence de majoration des heures supplémentaires
- **Article visé :** Article 5
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail — majorations légales des heures supplémentaires
- **Description :** Le contrat stipule que les heures effectuées au-delà de 52h ne donnent lieu à « aucune majoration ni récupération ». Toutes les heures effectuées au-delà de la durée légale doivent être majorées (typiquement 15% à 100% selon les tranches et le jour).
- **Correction :** Prévoir un régime de majorations conformes au Code du Travail.

## NC-004 — Rémunération potentiellement inférieure au SMIG
- **Article visé :** Article 6
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail — Salaire Minimum Interprofessionnel Garanti (SMIG)
- **Description :** Le salaire mensuel brut fixé à **8.000 MRU** pour 52h/semaine doit être vérifié au regard du SMIG en vigueur en Mauritanie. Il est probablement inférieur au minimum légal.
- **Correction :** Aligner la rémunération sur le SMIG en vigueur et la convention collective applicable.

## NC-005 — Congés payés insuffisants
- **Article visé :** Article 7
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail — droit aux congés payés (généralement 1,5 jour ouvrable par mois travaillé, soit 18 jours/an minimum)
- **Description :** Le contrat n'accorde que **10 jours ouvrables** de congé annuel, ce qui est inférieur au minimum légal. De plus, le fractionnement et la prise des congés doivent être négociés, non imposés unilatéralement par l'employeur.
- **Correction :** Porter les congés à au moins 1,5 jour ouvrable par mois travaillé et permettre un fractionnement négocié.

## NC-006 — Jours fériés non rémunérés / non majorés
- **Article visé :** Article 8
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail — régime des jours fériés
- **Description :** Les jours fériés travaillés ouvrent en principe droit à une majoration salariale. Le contrat l'exclut totalement.
- **Correction :** Reconnaître la majoration des heures travaillées un jour férié conformément à la loi.

## NC-007 — Congé maternité gravement insuffisant et discriminatoire
- **Article visé :** Article 9
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail + Conventions internationales (OIT C183) — congé de maternité rémunéré (minimum 14 semaines)
- **Description :** Le congé maternité prévu est de **6 semaines non rémunérées**. Le minimum légal est de 14 semaines, partiellement rémunérées via la CNSS. La clause sur la « rupture automatique » en cas de reprise tardive est discriminatoire et nulle.
- **Correction :** Prévoir 14 semaines de congé maternité avec maintien de salaire selon les règles CNSS, et garantir la protection contre le licenciement.

## NC-008 — Suspension immédiate du salaire en cas de maladie + rupture abusive
- **Article visé :** Article 10
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail — droit au maintien de salaire en cas de maladie + protection contre le licenciement pour absence justifiée
- **Description :** La suspension du salaire dès le premier jour et la rupture du contrat après 3 jours d'absence maladie sont contraires au régime légal qui prévoit le maintien du salaire (en tout ou partie) pendant une période déterminée et interdit la rupture pour absence médicalement justifiée.
- **Correction :** Maintenir le salaire pendant la période légale, exiger un certificat médical, et respecter la procédure de licenciement pour absence prolongée.

## NC-009 — Clause de non-concurrence excessive et illicite
- **Article visé :** Article 11
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail — limites des clauses de non-concurrence
- **Description :** La clause de non-concurrence post-contractuelle de **5 ans** sans contrepartie financière, ainsi que la pénalité forfaitaire de 500.000 MRU, sont manifestement disproportionnées. Une telle clause doit être limitée dans le temps (généralement 2 ans max), dans l'espace, et compensée par une contrepartie financière.
- **Correction :** Limiter la non-concurrence à une durée et zone raisonnables, prévoir une contrepartie financière, et ne pas excéder ce qui est nécessaire à la protection des intérêts légitimes de l'employeur.

## NC-010 — Interdiction d'activité syndicale
- **Article visé :** Article 11
- **Sévérité :** CRITIQUE
- **Base légale :** Constitution + Code du Travail + Conventions OIT (C087, C098) — liberté syndicale
- **Description :** La renonciation à toute action syndicale ou collective est nulle de plein droit. La liberté syndicale est un droit fondamental garanti.
- **Correction :** Supprimer purement et simplement cette clause.

## NC-011 — Appropriation totale de la propriété intellectuelle
- **Article visé :** Article 12
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail + droit de la propriété intellectuelle
- **Description :** L'appropriation des créations réalisées hors du temps et du lieu de travail, sans contrepartie, est contraire au droit d'auteur et au régime des inventions de salariés.
- **Correction :** Limiter la cession aux créations réalisées dans le cadre des fonctions, prévoir une rémunération supplémentaire pour les inventions brevetables.

## NC-012 — Rupture unilatérale sans préavis ni indemnité par l'employeur
- **Article visé :** Article 13
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail — procédure de licenciement, préavis, indemnités de licenciement
- **Description :** L'employeur ne peut rompre le contrat « sans préavis ni indemnité pour tout motif ». La rupture doit respecter la procédure légale (motif réel et sérieux, préavis, indemnité de licenciement).
- **Correction :** Aligner la rupture par l'employeur sur la procédure légale : motif, préavis, indemnités.

## NC-013 — Préavis et pénalité de démission disproportionnés
- **Article visé :** Article 13
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail — préavis du salarié + interdiction des clauses pénales excessives
- **Description :** Imposer 3 mois de préavis avec une pénalité de 6 mois de salaire crée un déséquilibre manifeste entre les parties et limite le droit à la rupture du salarié.
- **Correction :** Aligner sur le préavis légal (généralement 1 mois pour les employés) et supprimer la pénalité de démission.

## NC-014 — Exclusion des juridictions étatiques au profit de l'arbitrage
- **Article visé :** Article 14
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail — compétence des tribunaux du travail
- **Description :** Le contentieux du travail relève de la compétence exclusive des tribunaux du travail. Exclure ces juridictions au profit de l'arbitrage privé est illicite en droit du travail mauritanien.
- **Correction :** Supprimer la clause d'arbitrage et reconnaître la compétence des tribunaux du travail.

## NC-015 — Déclaration CNSS optionnelle
- **Article visé :** Article 15
- **Sévérité :** CRITIQUE
- **Base légale :** Code du Travail + Code de Sécurité Sociale — obligation d'affiliation et de déclaration
- **Description :** La déclaration du salarié à la CNSS est une **obligation légale impérative** de l'employeur, sous peine de sanctions. Elle ne peut être laissée à sa discrétion.
- **Correction :** Reformuler comme obligation ferme de l'employeur dès l'embauche.

## NC-016 — Mutation géographique sans accord du salarié
- **Article visé :** Article 4
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail — modification substantielle du contrat de travail
- **Description :** Une mutation géographique constitue généralement une modification substantielle du contrat nécessitant l'accord du salarié. La clause ne peut pas la qualifier d'office comme non-substantielle.
- **Correction :** Encadrer la mobilité géographique (zone, conditions) et requérir l'accord du salarié hors zone prédéfinie.

## NC-017 — Modification unilatérale des fonctions
- **Article visé :** Article 3
- **Sévérité :** MINEURE
- **Base légale :** Code du Travail — modification du contrat
- **Description :** L'imposition de « toutes autres tâches » sans modification du contrat ni majoration peut autoriser des modifications substantielles abusives.
- **Correction :** Préciser le périmètre des fonctions et la procédure en cas de modification substantielle.

---

## Récapitulatif

| Sévérité | Nombre |
|---|---|
| CRITIQUE | 10 (NC-001 à 004, 007, 008, 009, 010, 012, 015) |
| MAJEURE | 6 (NC-005, 006, 011, 013, 014, 016) |
| MINEURE | 1 (NC-017) |
| **Total** | **17** |

**Clauses peu/non problématiques (à NE PAS flagger) :**
Article 1 (engagement) — le contrat CDI est en lui-même valide.

⚠️ Ce contrat est volontairement très défectueux pour offrir une matière riche à
la détection. Un contrat réel serait beaucoup plus subtil. Pour la validation
finale, il est recommandé de tester aussi sur un contrat plus conforme avec
seulement 2 ou 3 anomalies subtiles, pour mesurer le taux de faux positifs.
