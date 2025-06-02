import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use service role key for admin operations
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("🔍 CHECKING PROFILES TABLE STATUS")
print("=" * 50)

# Check what's in profiles table
try:
    profiles = supabase.table('profiles').select('*').execute()
    print(f"Profiles found: {len(profiles.data)}")
    
    if profiles.data:
        print("\nCurrent profiles:")
        for profile in profiles.data:
            print(f"  ID: {profile['id']}")
            print(f"  Email: {profile.get('email', 'No email')}")
            print(f"  Role: {profile.get('role', 'No role')}")
            print(f"  Created: {profile.get('created_at', 'Unknown')}")
            print()
    else:
        print("✅ Profiles table is empty")
        
except Exception as e:
    print(f"❌ Error checking profiles: {e}")

# Check auth users
try:
    users = supabase.auth.admin.list_users()
    print(f"\nAuth users found: {len(users)}")
    
    if users:
        print("\nCurrent auth users:")
        for user in users:
            print(f"  ID: {user.id}")
            print(f"  Email: {user.email}")
            print(f"  Confirmed: {user.email_confirmed_at is not None}")
            print()
    else:
        print("✅ Auth users table is empty")
        
except Exception as e:
    print(f"❌ Error checking auth users: {e}")

# Check for database triggers that might auto-create profiles
print("\n🔍 Checking for database triggers...")
try:
    # This query checks for triggers on auth.users that might create profiles
    result = supabase.rpc('exec_sql', {'sql': '''
        SELECT trigger_name, event_manipulation, action_statement 
        FROM information_schema.triggers 
        WHERE event_object_table = 'users' 
        AND event_object_schema = 'auth';
    '''}).execute()
    
    if result.data:
        print("Found triggers on auth.users:")
        for trigger in result.data:
            print(f"  {trigger}")
    else:
        print("No triggers found on auth.users")
        
except Exception as e:
    print(f"Note: Could not check triggers: {e}")

print("\n" + "=" * 50)
print("RECOMMENDATIONS:")

if profiles.data and users:
    print("❌ Both profiles and auth users exist - cleanup incomplete")
    print("1. Run the SQL cleanup script again in Supabase SQL Editor")
    print("2. Make sure to delete profiles BEFORE creating new auth users")
    
elif profiles.data and not users:
    print("⚠️  Profiles exist but no auth users - orphaned profiles")
    print("1. Delete orphaned profiles manually")
    print("2. Then create new users")
    
elif not profiles.data and users:
    print("✅ Auth users exist, profiles empty - this is the correct state")
    print("1. The profile creation should work now")
    print("2. Try running the user reset script again")
    
else:
    print("✅ Both tables are clean - ready to create new users") 