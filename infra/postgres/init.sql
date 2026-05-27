-- Enable pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Extension for trigram fuzzy matching (useful for hybrid search later)
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
