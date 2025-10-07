/*
  # Add Performance Indexes

  1. Indexes for Users Table
    - Add index on `username` for faster authentication lookups
    - Add index on `email` for email-based queries
    - Add index on `role` for role-based filtering

  2. Indexes for Clients Table
    - Add index on `dni_number` for unique identifier lookups
    - Add composite index on `first_name, last_name` for name searches
    - Add index on `is_active` for filtering active clients
    - Add index on `created_at` for temporal queries

  3. Indexes for Client Biometrics Table
    - Add composite index on `client_id, type, is_active` for biometric lookups
    - Add index on `type` for filtering by biometric type
    - Add index on `is_active` for filtering active biometrics
    - Add index on `created_at` for temporal queries

  4. Notes
    - All indexes use IF NOT EXISTS to prevent errors on rerun
    - Indexes improve query performance for frequently accessed data
    - Composite indexes optimize multi-column queries
*/

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_clients_dni_number ON clients(dni_number);

CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(first_name, last_name);

CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);

CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_biometrics_client_type_active ON client_biometrics(client_id, type, is_active);

CREATE INDEX IF NOT EXISTS idx_biometrics_type ON client_biometrics(type);

CREATE INDEX IF NOT EXISTS idx_biometrics_is_active ON client_biometrics(is_active);

CREATE INDEX IF NOT EXISTS idx_biometrics_created_at ON client_biometrics(created_at DESC);
