/*
  # Create client Biometrics Table

  ## New Extension
  - **vector** - PostgreSQL extension for vector similarity search and embeddings

  ## New Tables
  1. **client_biometrics**
     - id (uuid, primary key)
     - client_id (uuid, foreign key to clients)
     - type (biometric_type) - 'face' or 'fingerprint'
     - thumbnail (bytea) - Small preview image (mainly for face recognition)
     - embedding (vector(512)) - ML feature vector for similarity search
     - is_active (boolean) - Whether this biometric is currently active
     - created_at (timestamptz) - Record creation timestamp
     - updated_at (timestamptz) - Last update timestamp
     - meta_info (jsonb) - Flexible metadata storage

  ## Security
  - RLS enabled on client_biometrics table
  - Authenticated users can read all biometric records
  - Authenticated users can insert, update, and delete biometric records
  - Policies ensure only authenticated users have access to sensitive biometric data

  ## Constraints
  - Each client can have only ONE active biometric per type
  - Foreign key ensures biometric data is deleted when client is deleted (CASCADE)
  - Unique constraint on (client_id, type) with DEFERRABLE for safe updates

  ## Indexes
  - Index on client_id for fast client lookups
  - Index on type for filtering by biometric type
  - Index on is_active for active biometric queries
  - Vector index (HNSW) on embedding for fast similarity search

  ## Notes
  - Vector extension required for ML embedding storage and similarity search
  - Embedding dimension is 512, suitable for most modern face/fingerprint models
  - BYTEA columns store binary data efficiently
  - Unique constraint allows only one active biometric per type per client
  - CASCADE delete ensures orphaned biometric data is cleaned up
*/

-- ============================================================
-- ENABLE VECTOR EXTENSION
-- ============================================================

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================
-- client BIOMETRICS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS client_biometrics (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  type biometric_type NOT NULL,
  compressed_data BYTEA,
  thumbnail BYTEA,
  embedding vector(512),
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  meta_info JSONB DEFAULT '{}'::jsonb,
  CONSTRAINT unique_client_biometric_active UNIQUE (client_id, type) DEFERRABLE INITIALLY DEFERRED
);

ALTER TABLE client_biometrics ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- ROW LEVEL SECURITY POLICIES
-- ============================================================

DROP POLICY IF EXISTS "Authenticated users can read biometrics" ON client_biometrics;
CREATE POLICY "Authenticated users can read biometrics"
  ON client_biometrics FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "Authenticated users can insert biometrics" ON client_biometrics;
CREATE POLICY "Authenticated users can insert biometrics"
  ON client_biometrics FOR INSERT
  TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can update biometrics" ON client_biometrics;
CREATE POLICY "Authenticated users can update biometrics"
  ON client_biometrics FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can delete biometrics" ON client_biometrics;
CREATE POLICY "Authenticated users can delete biometrics"
  ON client_biometrics FOR DELETE
  TO authenticated
  USING (true);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_client_biometrics_client_id ON client_biometrics(client_id);
CREATE INDEX IF NOT EXISTS idx_client_biometrics_type ON client_biometrics(type);
CREATE INDEX IF NOT EXISTS idx_client_biometrics_is_active ON client_biometrics(is_active);
CREATE INDEX IF NOT EXISTS idx_client_biometrics_created_at ON client_biometrics(created_at);

-- Vector index for similarity search using HNSW algorithm
CREATE INDEX IF NOT EXISTS idx_client_biometrics_embedding ON client_biometrics
  USING hnsw (embedding vector_cosine_ops);

-- ============================================================
-- UPDATE TRIGGER FOR TIMESTAMPS
-- ============================================================

DROP TRIGGER IF EXISTS update_client_biometrics_updated_at ON client_biometrics;
CREATE TRIGGER update_client_biometrics_updated_at
  BEFORE UPDATE ON client_biometrics
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
