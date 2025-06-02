-- Create Test Users for Each Role Level
-- Run this script to populate the database with test accounts

-- Insert Free User
INSERT INTO profiles (id, email, role, subscription_status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'free-user@test.com',
    'free',
    'none',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    role = EXCLUDED.role,
    subscription_status = EXCLUDED.subscription_status,
    updated_at = NOW();

-- Insert Paid/Subscriber User  
INSERT INTO profiles (id, email, role, subscription_status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'paid-user@test.com',
    'subscriber',
    'active',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    role = EXCLUDED.role,
    subscription_status = EXCLUDED.subscription_status,
    updated_at = NOW();

-- Insert Admin User
INSERT INTO profiles (id, email, role, subscription_status, created_at, updated_at)
VALUES (
    gen_random_uuid(),
    'admin-user@test.com',
    'admin',
    'active',
    NOW(),
    NOW()
) ON CONFLICT (email) DO UPDATE SET
    role = EXCLUDED.role,
    subscription_status = EXCLUDED.subscription_status,
    updated_at = NOW();

-- Verify the insertions
SELECT 
    email,
    role,
    subscription_status,
    created_at
FROM profiles 
WHERE email IN ('free-user@test.com', 'paid-user@test.com', 'admin-user@test.com')
ORDER BY role; 