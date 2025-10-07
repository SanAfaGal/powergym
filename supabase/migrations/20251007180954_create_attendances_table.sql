/*
  # Create attendances table

  1. New Tables
    - `attendances`
      - `id` (uuid, primary key) - Unique identifier for each attendance record
      - `client_id` (uuid, foreign key) - References the client who checked in
      - `check_in` (timestamptz) - Timestamp when client checked in
      - `biometric_type` (biometric_type enum) - Type of biometric used for verification
      - `meta_info` (jsonb) - Additional metadata for the attendance record

  2. Security
    - Enable RLS on `attendances` table
    - Add policy for authenticated users to view attendances
    - Add policy for authenticated users to create attendances

  3. Indexes
    - Add index on `client_id` for faster queries
    - Add index on `check_in` for time-based queries
    - Add composite index for client and check-in time queries

  4. Notes
    - Attendance records are created when a client's identity is validated via face recognition
    - biometric_type indicates which biometric method was used for validation
    - meta_info can store additional context like confidence score, device info, etc.
*/

CREATE TABLE IF NOT EXISTS attendances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  check_in TIMESTAMPTZ NOT NULL DEFAULT now(),
  biometric_type biometric_type,
  meta_info JSONB DEFAULT '{}'::jsonb
);

ALTER TABLE attendances ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Authenticated users can view all attendances" ON attendances;
CREATE POLICY "Authenticated users can view all attendances"
  ON attendances FOR SELECT
  TO authenticated
  USING (true);

DROP POLICY IF EXISTS "Authenticated users can create attendances" ON attendances;
CREATE POLICY "Authenticated users can create attendances"
  ON attendances FOR INSERT
  TO authenticated
  WITH CHECK (true);

CREATE INDEX IF NOT EXISTS idx_attendances_client_id ON attendances(client_id);
CREATE INDEX IF NOT EXISTS idx_attendances_check_in ON attendances(check_in DESC);
CREATE INDEX IF NOT EXISTS idx_attendances_client_check_in ON attendances(client_id, check_in DESC);