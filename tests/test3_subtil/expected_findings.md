# Test #3 — Ground Truth: Contrat majoritairement conforme avec anomalies subtiles

Ce test sert à mesurer le **taux de faux positifs** du système. Le contrat
`contrat_travail_test3.md` est, dans l'ensemble, conforme au Code du Travail
mauritanien — mais comporte **2 anomalies subtiles** délibérées.

Un système performant doit :
- Détecter les 2 anomalies (vrais positifs)
- Ne PAS générer de findings sur les nombreuses clauses conformes (faibles faux positifs)

---

## NC-001 — Clause de non-concurrence sans contrepartie financière
- **Article visé :** Article 11
- **Sévérité :** MAJEURE
- **Base légale :** Code du Travail + jurisprudence — validité de la clause de non-concurrence
- **Description :** La clause de non-concurrence post-contractuelle de 3 ans sur tout le territoire mauritanien et sur tout le secteur audit/conseil est rédigée **sans contrepartie financière** versée à la Salariée. La jurisprudence moderne exige systématiquement une contrepartie pécuniaire pour la validité de telles clauses, en plus d'une limitation raisonnable dans le temps, l'espace et l'activité.
- **Correction :** Ajouter une contrepartie financière (par exemple 30 à 50% du salaire mensuel pendant la durée d'application), ou réduire significativement la portée de la clause (durée, périmètre géographique, activités).
- **Difficulté de détection :** MOYENNE — la clause paraît raisonnable dans sa forme, l'omission est ce qui pose problème.

## NC-002 — Renouvellement de la période d'essai non plafonné
- **Article visé :** Article 2
- **Sévérité :** MINEURE
- **Base légale :** Code du Travail — règles de renouvellement de la période d'essai
- **Description :** La clause autorise un renouvellement « une fois » de la période d'essai par simple accord écrit, sans préciser que ce renouvellement doit intervenir **avant l'expiration** de la période initiale et qu'il doit être motivé. Sans ces précisions, le renouvellement pourrait être considéré comme abusif.
- **Correction :** Préciser que le renouvellement doit être notifié par écrit avant l'expiration de la période initiale, et préciser les motifs justifiant ce renouvellement.
- **Difficulté de détection :** ÉLEVÉE — la clause est presque correcte, l'omission est doctrinale.

---

## Récapitulatif

| Sévérité | Nombre |
|---|---|
| CRITIQUE | 0 |
| MAJEURE | 1 (NC-001) |
| MINEURE | 1 (NC-002) |
| **Total** | **2** |

## Clauses conformes (à NE PAS flagger — mesure des faux positifs)

Le système ne devrait pas générer de finding négatif sur les articles suivants :

| Article | Sujet | Conformité |
|---|---|---|
| Art. 1 | Engagement CDI | ✅ Conforme |
| Art. 3 | Fonctions + avenant pour modification | ✅ Conforme |
| Art. 4 | Lieu + mobilité avec frais à charge employeur | ✅ Conforme |
| Art. 5 | 40h/semaine + majoration légale | ✅ Conforme |
| Art. 6 | Salaire 45.000 MRU > SMIG + primes | ✅ Conforme |
| Art. 7 | 1,5 jour ouvrable/mois | ✅ Conforme |
| Art. 8 | CNSS dès prise de fonction | ✅ Conforme |
| Art. 9 | Maternité par renvoi à la loi | ✅ Conforme |
| Art. 10 | Confidentialité | ✅ Conforme |
| Art. 12 | Rupture par renvoi à la loi | ✅ Conforme |
| Art. 13 | Tribunaux du travail | ✅ Conforme |
| Art. 14 | Renvoi général | ✅ Conforme |

## Mesures attendues

- **Précision** sur Test #3 = TP / (TP + FP). Avec 12 clauses conformes, chaque
  faux positif fait chuter significativement la précision.
- **Rappel** = TP / (TP + FN). Sur seulement 2 vrais positifs, manquer NC-001
  ramène le rappel à 50%.
- Test #3 est **complémentaire** des tests 1 et 2 :
  - Tests 1 & 2 mesurent le **rappel** (le système trouve-t-il les vraies violations ?)
  - Test #3 mesure la **précision** (le système hallucine-t-il des violations ?)
