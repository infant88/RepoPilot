-- PostgreSQL pgvector initialization script
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log completion
DO $$
BEGIN
   RAISE NOTICE 'pgvector and uuid-ossp extensions initialized successfully.';
END $$;
