-- init.sql — exécuté automatiquement au premier démarrage du container PostgreSQL
-- Cf. PDF section 3.5 Listing 5

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------
-- Table principale : articles juridiques indexés (OHADA + Code du Travail)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_articles (
    id               TEXT PRIMARY KEY,          -- ex. "OHADA-AUSCGIE-311"
    jurisdiction     TEXT NOT NULL,             -- "ohada" | "mauritania_labor"
    code_name        TEXT NOT NULL,             -- "AUSCGIE" | "CODE_TRAVAIL_MR"
    article_number   TEXT NOT NULL,             -- "311"
    hierarchy_path   TEXT,                      -- "Livre 2 > Titre 1 > Chapitre 3"
    full_text        TEXT NOT NULL,
    language         CHAR(2) DEFAULT 'fr',      -- "fr" | "ar"
    version_date     DATE,                      -- date de la version du texte
    country_override JSONB DEFAULT '{}',        -- dérogations nationales mauritaniennes
    embedding        vector(1024)               -- BGE-M3 (dim 1024)
);

-- Index HNSW pour la recherche cosinus rapide (supporte des millions de vecteurs)
CREATE INDEX IF NOT EXISTS articles_hnsw_idx
    ON legal_articles USING hnsw (embedding vector_cosine_ops);

-- Index sur jurisdiction pour filtrage rapide
CREATE INDEX IF NOT EXISTS articles_juris_idx
    ON legal_articles (jurisdiction);

-- Index de recherche plein texte (utile pour la recherche hybride)
CREATE INDEX IF NOT EXISTS articles_fts_idx
    ON legal_articles USING gin (to_tsvector('french', full_text));

-- -----------------------------------------------------------------------
-- Table : contrats soumis par les utilisateurs
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS contracts (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_type     TEXT NOT NULL,                 -- "statuts" | "contrat_travail"
    source_path  TEXT NOT NULL,                 -- chemin fichier uploadé
    jurisdiction TEXT,                          -- "ohada" | "mauritania_labor"
    uploaded_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------
-- Table : résultats d'analyse
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analyses (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_id   UUID REFERENCES contracts(id) ON DELETE CASCADE,
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | running | done | error
    findings_json JSONB,                            -- list[Finding] sérialisé
    error_log     TEXT,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    finished_at   TIMESTAMPTZ
);
