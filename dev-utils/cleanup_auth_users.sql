-- ⚠️  WARNING: Run these queries in the Supabase SQL Editor
-- This will delete ALL users from auth.users and related tables
-- Make sure you have backups if needed!

-- 1. First delete from profiles table (your custom table)
DELETE FROM public.profiles;

-- 2. Delete from auth-related tables that reference users
-- Delete user sessions
DELETE FROM auth.sessions;

-- Delete user refresh tokens  
DELETE FROM auth.refresh_tokens;

-- Delete user identities (for social auth)
DELETE FROM auth.identities;

-- Delete audit log entries (optional - keeps logs clean)
DELETE FROM auth.audit_log_entries;

-- 3. Finally delete from auth.users (this is the main table)
DELETE FROM auth.users;

-- 4. Reset sequences if you want clean IDs (optional)
-- Note: Only run these if you want to start user IDs from 1 again
-- ALTER SEQUENCE auth.refresh_tokens_id_seq RESTART WITH 1;
-- ALTER SEQUENCE auth.audit_log_entries_instance_id_seq RESTART WITH 1;

-- 5. Verify deletion
SELECT 'auth.users count:' as table_name, COUNT(*) as count FROM auth.users
UNION ALL
SELECT 'auth.sessions count:', COUNT(*) FROM auth.sessions  
UNION ALL
SELECT 'auth.refresh_tokens count:', COUNT(*) FROM auth.refresh_tokens
UNION ALL
SELECT 'auth.identities count:', COUNT(*) FROM auth.identities
UNION ALL
SELECT 'public.profiles count:', COUNT(*) FROM public.profiles;

-- After running this, all users should be deleted and you can create new ones 