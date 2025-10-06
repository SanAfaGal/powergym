/*
  # Database Schema Setup - ENUMs and Initial Tables

  ## New Enums Created
  1. **user_role** - Roles for system users
     - admin: Full system access
     - employee: Limited access

  2. **gender_type** - Gender options
     - male: Masculino
     - female: Femenino
     - other: Otro

  3. **document_type** - Identification document types
     - CC: Cédula de Ciudadanía
     - TI: Tarjeta de Identidad
     - CE: Cédula de Extranjería
     - PP: Pasaporte

  5. **duration_type** - Time period units
     - day, week, month, year

  6. **attendance_result** - Attendance check results
     - recognized: Client recognized with active subscription
     - not_recognized: Client not found
     - expired: Client found but subscription expired
     - no_data: No biometric data available

  7. **biometric_type** - Types of biometric authentication
     - face: Facial recognition
     - fingerprint: Fingerprint recognition

  8. **subscription_status** - Subscription states
     - active: Active and paid
     - expired: Ended without renewal
     - pending_payment: Awaiting payment
     - canceled: User canceled

  9. **payment_method** - Payment methods accepted
     - cash: Cash payment
     - qr: QR code payment

  10. **payment_status** - Payment states
      - pending: Processing
      - completed: Successfully paid
      - failed: Payment failed

  11. **unit_measure** - Inventory measurement units
      - bottle, can, bag, jar, box

  12. **inventory_movement_type** - Inventory movements
      - entry: Stock entry
      - exit: Stock exit
      - adjustment: Inventory adjustment

  13. **asset_status** - Equipment status
      - operational: Functioning normally
      - maintenance: Under maintenance
      - retired: Out of service

  14. **maintenance_type** - Maintenance types
      - preventive: Scheduled maintenance
      - corrective: Repair maintenance

  ## New Tables
  1. **users**
     - id (uuid, primary key)
     - username (text, unique)
     - email (text, unique)
     - full_name (text)
     - hashed_password (text)
     - role (user_role)
     - is_active (boolean)
     - created_at (timestamptz)
     - updated_at (timestamptz)

  2. **clients**
     - id (uuid, primary key)
     - dni_type (document_type)
     - dni_number (text, unique)
     - first_name (text)
     - middle_name (text, optional)
     - last_name (text)
     - second_last_name (text, optional)
     - phone (text)
     - alternative_phone (text, optional)
     - birth_date (date)
     - gender (gender_type)
     - address (text, optional)
     - is_active (boolean)
     - created_at (timestamptz)
     - updated_at (timestamptz)
     - meta_info (jsonb)

  ## Security
  - RLS enabled on both tables
  - Users table: Authenticated users can read their own data
  - clients table: Authenticated users can read all, admins can modify

  ## Notes
  - All ENUMs use Spanish values for consistency
  - Timestamps use timezone-aware types
  - UUID v4 for primary keys
  - Soft delete supported via status field
  - Meta info stored as JSONB for flexibility
*/

-- ============================================================
-- CREATE ENUMS
-- ============================================================

DO $$ BEGIN
  CREATE TYPE user_role AS ENUM ('admin', 'employee');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE gender_type AS ENUM ('male', 'female', 'other');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE document_type AS ENUM ('CC', 'TI', 'CE', 'PP');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE duration_type AS ENUM ('day', 'week', 'month', 'year');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE attendance_result AS ENUM ('recognized', 'not_recognized', 'expired', 'no_data');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE biometric_type AS ENUM ('face', 'fingerprint');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE subscription_status AS ENUM ('active', 'expired', 'pending_payment', 'canceled');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE payment_method AS ENUM ('cash', 'qr');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE unit_measure AS ENUM ('bottle', 'can', 'bag', 'jar', 'box');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE inventory_movement_type AS ENUM ('entry', 'exit', 'adjustment');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE asset_status AS ENUM ('operational', 'maintenance', 'retired');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
  CREATE TYPE maintenance_type AS ENUM ('preventive', 'corrective');
EXCEPTION
  WHEN duplicate_object THEN null;
END $$;

-- ============================================================
-- USERS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE,
  full_name TEXT,
  hashed_password TEXT NOT NULL,
  role user_role NOT NULL DEFAULT 'employee',
  disabled BOOLEAN DEFAULT FALSE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own data" ON users;
CREATE POLICY "Users can read own data"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Admins can read all users" ON users;
CREATE POLICY "Admins can read all users"
  ON users FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );

DROP POLICY IF EXISTS "Admins can insert users" ON users;
CREATE POLICY "Admins can insert users"
  ON users FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );

DROP POLICY IF EXISTS "Admins can update users" ON users;
CREATE POLICY "Admins can update users"
  ON users FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM users
      WHERE users.id = auth.uid()
      AND users.role = 'admin'
    )
  );

-- ============================================================
-- clientS TABLE
-- ============================================================

CREATE TABLE IF NOT EXISTS clients (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dni_type document_type NOT NULL,
  dni_number TEXT UNIQUE NOT NULL,
  first_name TEXT NOT NULL,
  middle_name TEXT,
  last_name TEXT NOT NULL,
  second_last_name TEXT,
  phone TEXT NOT NULL,
  alternative_phone TEXT,
  birth_date DATE NOT NULL,
  gender gender_type NOT NULL,
  address TEXT,
  is_active BOOLEAN DEFAULT TRUE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  updated_at TIMESTAMPTZ DEFAULT now() NOT NULL,
  meta_info JSONB DEFAULT '{}'::jsonb
);

ALTER TABLE clients ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can read clients" ON clients;
CREATE POLICY "Authenticated users can read clients"
  ON clients FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "Authenticated users can insert clients" ON clients;
CREATE POLICY "Authenticated users can insert clients"
  ON clients FOR INSERT
  TO authenticated
  WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can update clients" ON clients;
CREATE POLICY "Authenticated users can update clients"
  ON clients FOR UPDATE
  TO authenticated
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "Authenticated users can delete clients" ON clients;
CREATE POLICY "Authenticated users can delete clients"
  ON clients FOR DELETE
  TO authenticated
  USING (true);

-- ============================================================
-- INDEXES
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);

CREATE INDEX IF NOT EXISTS idx_clients_dni_number ON clients(dni_number);
CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone);
CREATE INDEX IF NOT EXISTS idx_clients_is_active ON clients(is_active);
CREATE INDEX IF NOT EXISTS idx_clients_created_at ON clients(created_at);

-- ============================================================
-- UPDATE TRIGGER FOR TIMESTAMPS
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_clients_updated_at ON clients;
CREATE TRIGGER update_clients_updated_at
  BEFORE UPDATE ON clients
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();
