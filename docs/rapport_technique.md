# Rapport Technique — Système Agentique de Vérification de Conformité Contractuelle

**Projet de Fin d'Études — Licence Professionnelle DI / IG / RT**
**Département MQI — ISCAE Mauritanie**

---

## 1. Introduction

### 1.1 Contexte

Les notaires et juristes mauritaniens consacrent une part significative de leur
activité à la vérification manuelle de la conformité des contrats avec les lois
en vigueur. Cette tâche est chronophage, sujette aux erreurs humaines, et devient
de plus en plus complexe face à l'évolution constante du cadre législatif et
réglementaire (Code du Travail amendé en 2024, Code de Commerce de 2000, Code
des Obligations et des Contrats, Convention Collective Générale du Travail,
conventions internationales).

### 1.2 Problématique scientifique

> **Comment automatiser de manière fiable et intelligente la vérification de la
> conformité d'un contrat avec les dispositions légales applicables ?**

Cette question soulève plusieurs sous-problèmes :

1. **Extraction structurée** : comment identifier précisément les clauses d'un
   document juridique non structuré (PDF, DOCX) ?
2. **Recherche contextuelle** : pour chaque clause, comment retrouver dans un
   corpus juridique volumineux les dispositions légales pertinentes ?
3. **Raisonnement juridique** : comment évaluer la conformité d'une clause
   au regard de plusieurs textes parfois contradictoires, avec un niveau de
   confiance traçable et auditable ?
4. **Reporting fidèle** : comment produire un rapport exploitable par un
   juriste, avec citations vérifiables ?

### 1.3 Objectifs

Concevoir et développer un **système agentique multi-agents** capable de :
- Analyser des documents contractuels (statuts d'entreprise, contrats de travail)
- Identifier les clauses à risque et les non-conformités
- Citer la base légale précise pour chaque finding
- Proposer des recommandations de correction
- Produire un rapport structuré exploitable par un juriste

---

## 2. État de l'Art

### 2.1 IA agentique et architectures multi-agents

Trois frameworks dominent l'orchestration d'agents LLM :

| Framework | Modèle | Forces | Faiblesses |
|---|---|---|---|
| **LangGraph** | Graphe d'état explicite (state machine) | Contrôle fin du flux, débuggable, supporte les cycles et la persistance | Courbe d'apprentissage, code plus verbeux |
| **CrewAI** | Métaphore "équipe d'agents" avec rôles | Très expressif, prompts naturels | Moins de contrôle sur le flux, débogage difficile |
| **AutoGen (Microsoft)** | Conversations multi-agents | Naturel pour les négociations agent-agent | Coût en tokens élevé, non déterministe |

**Choix : LangGraph.** Pour la vérification de conformité, le flux est connu
à l'avance (extraction → matching → vérification → rapport) et il est crucial
de pouvoir tracer chaque étape pour un audit juridique. Le modèle de graphe
explicite permet aussi d'introduire ultérieurement des boucles correctives
(Self-RAG, Corrective-RAG).

**Travaux apparentés appliqués au juridique :**

- *LegalBench* (Guha et al., 2023) : benchmark d'évaluation des LLMs sur des
  tâches juridiques. Les architectures multi-agents y surpassent les LLMs
  isolés sur les tâches de raisonnement multi-étapes.
- *Chatlaw* (Cui et al., 2023) : modèle juridique chinois qui utilise plusieurs
  experts spécialisés combinés par un agent superviseur.
- *Harvey AI* (industrie) : adopté par plusieurs cabinets internationaux,
  exploite une architecture similaire pour la revue de contrats.

### 2.2 Retrieval-Augmented Generation (RAG)

Le RAG (Lewis et al., 2020) répond au problème de l'hallucination des LLMs en
ancrant la génération dans un corpus de référence. Pour le juridique, où chaque
affirmation doit être traçable à une source, le RAG est essentiel.

**Variantes avancées étudiées :**

| Technique | Principe | Pertinence pour ce projet |
|---|---|---|
| **Naïf** | Retrieval → augmentation → génération | Baseline implémentée |
| **HyDE** (Gao et al., 2022) | Génère une réponse hypothétique, l'embed, puis cherche | Utile si les clauses du contrat n'utilisent pas le vocabulaire de la loi |
| **Self-RAG** (Asai et al., 2023) | Le LLM décide quand chercher, et critique sa propre génération | Pertinent pour réduire les faux positifs |
| **Corrective-RAG** (Yan et al., 2024) | Évalue la qualité des passages retrouvés, reformule si insuffisants | Améliore le rappel sur les clauses ambiguës |
| **GraphRAG** (Edge et al., 2024) | Construit un graphe de connaissances en amont | Coûteux à construire, gain marginal sur un corpus de codes |

**Roadmap d'évolution** : démarrer avec un RAG naïf (implémenté dans ce MVP),
puis intégrer Self-RAG sur la phase de vérification pour réduire les
hallucinations (cf. § 8).

### 2.3 Extraction d'information et NER juridique

**Approches considérées :**

1. **NER classique (spaCy, transformers)** : extraction d'entités nommées
   (montants, dates, parties, références d'articles). Précis mais nécessite un
   modèle entraîné sur du français juridique mauritanien — corpus annoté
   indisponible.
2. **LLM en mode "extracteur structuré"** : prompt qui demande au LLM de
   produire un JSON structuré. Plus flexible, fonctionne sans entraînement
   spécifique, mais plus coûteux et moins déterministe.
3. **Hybride** : LLM pour la structuration des clauses + regex pour les
   références d'articles + post-validation.

**Choix : approche hybride.** L'extraction est faite par le LLM avec instructions
strictes de sortie JSON, fallback sur regex `(?:article|art\.?)\s*\d+` pour
résister aux échecs. C'est documenté dans `backend/app/agents/extraction.py`.

---

## 3. Architecture du Système

### 3.1 Vue d'ensemble

```
┌─────────────┐         ┌────────────────────────────────────────────┐
│  Frontend   │         │  Backend FastAPI                           │
│  Next.js 15 │ ──HTTP─►│  ┌──────────────────────────────────────┐ │
│  + Tailwind │         │  │  LangGraph orchestrator              │ │
└─────────────┘         │  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌─────┐│ │
                        │  │  │Extract│→│Match │→│Verify│→│Report││ │
                        │  │  └──────┘ └──────┘ └──────┘ └─────┘│ │
                        │  │              ▲          ▲           │ │
                        │  └──────────────┼──────────┼───────────┘ │
                        │                 │          │             │
                        │  ┌──────────────▼──────────▼───────────┐ │
                        │  │  RAG : bge-m3 embeddings (1024d)    │ │
                        │  │       cosine retrieval (HNSW)       │ │
                        │  └─────────────────┬───────────────────┘ │
                        └────────────────────┼─────────────────────┘
                                             ▼
                        ┌────────────────────────────────────────┐
                        │  PostgreSQL 17 + pgvector              │
                        │  ┌──────────────┐ ┌─────────┐ ┌──────┐│
                        │  │legal_chunks  │ │contracts│ │finds ││
                        │  │ (vector idx) │ │         │ │      ││
                        │  └──────────────┘ └─────────┘ └──────┘│
                        └────────────────────────────────────────┘
```

### 3.2 Les quatre agents

#### Agent 1 — Extraction (`extraction.py`)

**Rôle** : transformer le texte brut du contrat en une liste structurée de
`Clause(ref, title, text, topic)`.

**Implémentation** : prompt système strict demandant une sortie JSON, fallback
regex en cas d'échec.

**Choix de conception** : on tronque le contrat à 30 000 caractères pour éviter
les coûts excessifs sur les très longs documents. Pour des statuts complexes
>30k, il faudrait introduire un pré-découpage par titre.

#### Agent 2 — Matching (`matching.py`)

**Rôle** : pour chaque clause extraite, retrouver les `k=5` passages de loi les
plus pertinents via recherche vectorielle.

**Implémentation** : requête construite à partir de `topic + title + extrait(400 chars)`,
embedding via bge-m3, distance cosine sur l'index HNSW.

**Choix de conception** : `k=5` est un compromis entre précision (k faible) et
rappel (k élevé). À évaluer empiriquement sur les tests.

#### Agent 3 — Vérification (`verification.py`)

**Rôle** : confronter chaque clause à ses passages légaux. Deux passes :
1. **Vérification clause-par-clause** : la clause contredit-elle un texte légal ?
2. **Détection des clauses manquantes** : quelles clauses obligatoires sont
   absentes du contrat ?

**Implémentation** : prompt expert juridique mauritanien, sortie JSON avec
`severity / category / description / recommendation / legal_basis / confidence`.

**Choix de conception** : produire un `Finding.confidence` permet de filtrer
ultérieurement les résultats faibles, et facilite la calibration du modèle.

#### Agent 4 — Reporting (`reporting.py`)

**Rôle** : agréger tous les findings en un rapport Markdown lisible par un
juriste, ordonné par sévérité.

**Implémentation** : pas d'appel LLM (déterministe), génération de Markdown
avec icônes de sévérité, citations légales, recommandations.

### 3.3 Schéma de données

```
legal_chunks
  id              UUID PK
  source_file     VARCHAR(512) INDEX
  source_title    VARCHAR(512)
  article_ref     VARCHAR(128) INDEX     -- "Article 23"
  chunk_index     INTEGER
  content         TEXT
  embedding       vector(1024) HNSW(cosine)
  chunk_metadata  JSONB
  created_at      TIMESTAMPTZ

contracts
  id                  UUID PK
  filename            VARCHAR(512)
  contract_type       VARCHAR(64)   -- 'statuts' | 'contrat_travail'
  raw_text            TEXT
  status              VARCHAR(32)   -- pending|processing|completed|failed
  contract_metadata   JSONB         -- { report: "...", saved_path: "..." }
  created_at, completed_at

findings
  id              UUID PK
  contract_id     UUID FK -> contracts.id ON DELETE CASCADE
  severity        VARCHAR(16)  -- CRITIQUE | MAJEURE | MINEURE
  category        VARCHAR(64)
  clause_ref      VARCHAR(128)
  clause_text     TEXT
  description     TEXT
  recommendation  TEXT
  legal_basis     JSONB        -- [{source, article, excerpt}, ...]
  confidence      FLOAT
  created_at      TIMESTAMPTZ
```

**Choix techniques :**
- **HNSW vs IVFFlat** : HNSW est choisi pour son temps de requête sub-linéaire
  et ses meilleures performances sur des corpus < 1M chunks. IVFFlat serait
  préférable au-delà.
- **Cosine vs L2** : cosine, standard pour les embeddings normalisés (bge-m3
  est normalisé par défaut).

### 3.4 Pipeline d'ingestion

```
PDF (Code du Travail)
   │
   ▼ pypdf.PdfReader
texte brut (~20 pages)
   │
   ▼ chunker.chunk_legal_text()  -- article-aware
[Chunk("Article 1", "..."), Chunk("Article 2", "..."), ...]
   │
   ▼ embed_texts(batch_size=16) via bge-m3
[[0.12, -0.04, ...], ...]  (1024-dim, normalized)
   │
   ▼ INSERT INTO legal_chunks
```

Le **chunker article-aware** est une optimisation clé : il découpe le texte
sur les frontières d'articles (`Article 12`, `Art. 12`), ce qui permet à
chaque chunk de représenter une disposition légale atomique. Pour les
articles très longs, il sub-divise en gardant la référence d'article en
métadonnée.

---

## 4. Choix Technologiques

### 4.1 LLM : DeepSeek

**Justification** :
- API OpenAI-compatible (intégration triviale via `langchain-openai`)
- Coût ~10x inférieur à GPT-4 (≈ 0.27 USD / 1M tokens d'entrée)
- Performance excellente en français (souvent à parité avec GPT-4 sur les
  benchmarks de raisonnement)
- Disponibilité d'une version "reasoning" pour les tâches complexes (option future)

### 4.2 Embeddings : BAAI/bge-m3

**Justification** :
- **Multilingue** (>100 langues) : crucial pour le français juridique
  mauritanien, qui peut contenir des termes en arabe
- **1024 dimensions** : bon compromis qualité / vitesse / stockage
- **Long-context** (jusqu'à 8192 tokens) : utile pour les articles de loi
  étendus
- **Local** : zéro coût marginal, zéro dépendance réseau, zéro fuite de
  données vers un fournisseur tiers (important pour un produit juridique)
- État de l'art sur les benchmarks MTEB multilingues

### 4.3 PostgreSQL + pgvector

**Justification** :
- Une seule base de données pour les données relationnelles ET vectorielles
  (vs. architecture polyglotte Postgres + Pinecone/Weaviate)
- Transactions ACID sur les findings (cohérence garantie)
- Index HNSW disponible depuis pgvector 0.5
- Open source, déployable on-premise (souveraineté des données juridiques)

### 4.4 FastAPI + Next.js

**Justification** :
- FastAPI : async natif, type-safety via Pydantic, documentation Swagger
  automatique
- Next.js 15 (App Router) + React 19 : SSR pour le SEO du site marketing,
  écosystème mature, déployable sur Vercel ou en self-hosted

---

## 5. Méthodologie d'Évaluation

### 5.1 Jeux de tests

Trois jeux de tests synthétiques ont été constitués :

| Test | Type | Mesure principale | Findings attendus |
|---|---|---|---|
| **Test #1** | Statuts SARL avec 10 violations grossières | Rappel | 10 (4 critiques, 4 majeures, 2 mineures) |
| **Test #2** | CDI avec 17 violations grossières | Rappel | 17 (10 critiques, 6 majeures, 1 mineure) |
| **Test #3** | CDI conforme avec 2 anomalies subtiles | Précision | 2 (1 majeure, 1 mineure) |

### 5.2 Métriques

Pour chaque test, on calcule :

- **Vrais Positifs (TP)** : findings du système correspondant à la ground truth
- **Faux Positifs (FP)** : findings du système absents de la ground truth
- **Faux Négatifs (FN)** : findings de la ground truth absents du système
- **Précision** = TP / (TP + FP)
- **Rappel** = TP / (TP + FN)
- **F1** = 2 × P × R / (P + R)

Pour la **précision des citations légales**, on évalue manuellement, sur un
échantillon, si la base légale citée pour chaque finding est :
- ✅ Correcte et pertinente
- ⚠ Pertinente mais imprécise
- ❌ Hallucinée

### 5.3 Protocole de validation

1. Ingestion du corpus complet (Code du Travail, Code de Commerce, Code des
   Obligations, Convention Collective)
2. Exécution du système sur les 3 tests
3. Annotation manuelle des résultats par comparaison avec la ground truth
4. Calcul des métriques
5. **Validation croisée par un juriste expert** sur un sous-échantillon des
   findings (recommandé Phase 5 du cahier des charges)

### 5.4 Matrice de confusion attendue (cible)

| | Détecté Positif | Détecté Négatif |
|---|---|---|
| **Réellement Positif** | TP ≥ 80% du total | FN ≤ 20% |
| **Réellement Négatif** | FP ≤ 10% | TN ≥ 90% |

Objectifs : F1 ≥ 0.80 sur l'ensemble des tests combinés. Les CRITIQUES doivent
avoir un rappel ≥ 95% (on tolère moins de faux négatifs sur les violations
graves).

---

## 6. Limites connues

1. **Pas de jurisprudence** : le corpus se limite aux textes législatifs.
   L'évolution doctrinale et jurisprudentielle n'est pas couverte.
2. **Pas de support de l'arabe** : bien que bge-m3 le supporte, le corpus est
   en français, ce qui exclut les versions arabes officielles des textes.
3. **Pas de spécialisation par secteur** : un contrat dans le secteur minier
   ou pétrolier obéit à des règles spécifiques non couvertes.
4. **Dépendance au LLM** : les performances sont conditionnées par la qualité
   de DeepSeek sur le français juridique mauritanien. Une dégradation côté
   fournisseur impacte le système.
5. **Pas de mémoire d'apprentissage** : le système ne s'améliore pas avec
   l'usage. Une boucle de feedback humain (RLHF léger ou fine-tuning) serait
   nécessaire.

---

## 7. Apports scientifiques du projet

1. **Architecture multi-agents pour le juridique mauritanien** : application
   concrète et démonstrable des techniques LangGraph récentes (2024) à un
   contexte juridique national peu traité dans la littérature.
2. **Chunker article-aware** pour les codes français : implémentation simple
   mais efficace, valorisée comme contribution open-source potentielle.
3. **Méthodologie d'évaluation à trois niveaux** (rappel grossier, rappel
   subtil, précision) : grille reproductible pour l'évaluation de systèmes
   similaires.
4. **Démonstration de souveraineté technique** : pile entièrement déployable
   on-premise (Postgres + bge-m3 local), seul le LLM est externe (et
   substituable par un modèle local au besoin).

---

## 8. Roadmap

### Court terme (Phase 5)
- [ ] Ingestion complète du corpus + benchmark sur les 3 tests
- [ ] Validation manuelle par un juriste expert
- [ ] Rédaction du guide utilisateur

### Moyen terme
- [ ] Self-RAG sur l'agent de vérification : second appel LLM pour critiquer
  les findings de faible confiance
- [ ] Mode interactif Q&A : poser une question libre sur une clause spécifique
- [ ] Export PDF du rapport de conformité (mise en page notariale)
- [ ] Mode comparatif : comparer le contrat soumis à un modèle de référence

### Long terme
- [ ] Fine-tuning d'un modèle bge-m3 sur du français juridique mauritanien
  annoté
- [ ] Intégration de la jurisprudence (corpus à constituer)
- [ ] Support du contrat de bail commercial, du contrat de vente, etc.
- [ ] Tableau de bord analytique pour cabinets : volume de contrats analysés,
  taux de non-conformité moyen par type, etc.

---

## 9. Conclusion

Le système développé démontre la faisabilité technique d'une vérification
automatisée de conformité contractuelle pour le droit mauritanien, grâce à
une architecture multi-agents LangGraph couplée à un RAG vectoriel pgvector.
Les choix technologiques (DeepSeek, bge-m3, Postgres) privilégient un
équilibre entre performance, coût, et souveraineté des données — un critère
crucial dans le contexte juridique.

Les évaluations sur les trois jeux de tests synthétiques permettent de
caractériser les performances en termes de rappel et de précision. La
validation finale par un juriste expert reste l'étape clé pour la mise en
production, conformément aux exigences académiques du cahier des charges.

---

## Bibliographie indicative

- Asai, A. et al. (2023). *Self-RAG: Learning to Retrieve, Generate, and
  Critique through Self-Reflection*. arXiv:2310.11511.
- Cui, J. et al. (2023). *Chatlaw: Open-Source Legal Large Language Model
  with Integrated External Knowledge Bases*. arXiv:2306.16092.
- Edge, D. et al. (2024). *From Local to Global: A Graph RAG Approach to
  Query-Focused Summarization*. Microsoft Research.
- Gao, L. et al. (2022). *Precise Zero-Shot Dense Retrieval without
  Relevance Labels (HyDE)*. arXiv:2212.10496.
- Guha, N. et al. (2023). *LegalBench: A Collaboratively Built Benchmark
  for Measuring Legal Reasoning in Large Language Models*. arXiv:2308.11462.
- Lewis, P. et al. (2020). *Retrieval-Augmented Generation for Knowledge-
  Intensive NLP Tasks*. NeurIPS 2020.
- Yan, S.-Q. et al. (2024). *Corrective Retrieval Augmented Generation*.
  arXiv:2401.15884.
- Documentation officielle : LangGraph (https://langchain-ai.github.io/langgraph/),
  pgvector (https://github.com/pgvector/pgvector), DeepSeek API
  (https://api-docs.deepseek.com/), BAAI/bge-m3 (https://huggingface.co/BAAI/bge-m3).
