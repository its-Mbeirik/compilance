-- init.sql — exécuté automatiquement au premier démarrage du container PostgreSQL

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------
-- Table principale : articles juridiques mauritaniens
-- (Code du Travail, COC, Code du Commerce, Convention Collective, OIT)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS legal_articles (
    id               TEXT PRIMARY KEY,          -- ex. "MAURITANIA_LABOR-CODE_TRAVAIL_MR-10"
    jurisdiction     TEXT NOT NULL,             -- "mauritania_labor"
    code_name        TEXT NOT NULL,             -- "CODE_TRAVAIL_MR" | "COC_MR" | ...
    article_number   TEXT NOT NULL,             -- "10"
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
    doc_type     TEXT NOT NULL,                 -- "contrat_travail"
    source_path  TEXT NOT NULL,                 -- chemin fichier uploadé
    jurisdiction TEXT,                          -- "mauritania_labor"
    uploaded_at  TIMESTAMPTZ DEFAULT NOW()
);

-- -----------------------------------------------------------------------
-- Table : utilisateurs (admin, user, sub_user)
-- -----------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email         TEXT UNIQUE NOT NULL,
    name          TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL DEFAULT 'user',     -- admin | user | sub_user
    status        TEXT NOT NULL DEFAULT 'pending',  -- pending | approved | rejected
    parent_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    updated_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS users_email_idx  ON users (email);
CREATE INDEX IF NOT EXISTS users_status_idx ON users (status);
CREATE INDEX IF NOT EXISTS users_parent_idx ON users (parent_id);

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
