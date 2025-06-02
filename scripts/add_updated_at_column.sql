-- Add updated_at column to profiles table
-- This column is needed for tracking when profile records are modified

ALTER TABLE profiles 
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Update existing records to have the updated_at timestamp set to created_at
UPDATE profiles 
SET updated_at = created_at 
WHERE updated_at IS NULL;

-- Verify the column was added
\d profiles; 