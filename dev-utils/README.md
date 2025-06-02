# Development Utilities

This directory contains development and debugging scripts for the bet-intel application.

## Scripts

### `complete_user_reset.py`
**Purpose:** Complete reset of all Supabase users and creation of test users.
**Usage:** `python dev-utils/complete_user_reset.py`
**What it does:**
- Deletes all existing auth users and profiles
- Creates 3 test users: free, subscriber, and admin
- Tests authentication for all created users
- Provides login credentials for development

**Test Users Created:**
- `free-user@test.com` / `testpassword123` (role: free)
- `paid-user@test.com` / `testpassword123` (role: subscriber) 
- `admin-user@test.com` / `testpassword123` (role: admin)

### `debug_auth_flow.py`
**Purpose:** Comprehensive debugging of Supabase authentication flow.
**Usage:** `python dev-utils/debug_auth_flow.py`
**What it does:**
- Checks environment variables
- Tests Supabase client authentication
- Analyzes JWT token structure
- Tests JWT validation with different secrets
- Tests database profile lookup
- Simulates backend auth flow
- Provides troubleshooting recommendations

### `cleanup_auth_users.sql`
**Purpose:** SQL commands to manually clean Supabase auth tables.
**Usage:** Run in Supabase SQL Editor
**What it does:**
- Deletes all users from auth.users and related tables
- Cleans up sessions, tokens, and identities
- Provides verification queries
- Use when Python scripts can't delete users due to constraints

## When to Use These Scripts

- **Setting up development environment:** Use `complete_user_reset.py`
- **Login not working:** Use `debug_auth_flow.py` to diagnose issues
- **Can't delete users via API:** Use `cleanup_auth_users.sql` in Supabase dashboard
- **Need fresh start:** Use SQL cleanup + user reset script

## Notes

- These scripts use the service role key and can modify/delete production data
- Always check your `.env` file points to the correct Supabase project
- The scripts auto-confirm user emails for development convenience
- JWT secrets must match your Supabase project configuration 