-- Habilitar extensión pgvector
CREATE EXTENSION IF NOT EXISTS vector;

-- Verificar que la extensión está instalada
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'vector'
    ) THEN
        RAISE EXCEPTION 'pgvector extension could not be created';
    END IF;
END $$;