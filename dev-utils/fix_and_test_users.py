import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use service role key for admin operations
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Expected user roles
EXPECTED_ROLES = {
    'free-user@test.com': {'role': 'free', 'subscription_status': 'none'},
    'paid-user@test.com': {'role': 'subscriber', 'subscription_status': 'active'},
    'admin-user@test.com': {'role': 'admin', 'subscription_status': 'none'}
}

print("🔧 FIXING USER ROLES AND TESTING AUTH")
print("=" * 50)

# Step 1: Fix the roles in profiles table
print("1. Fixing user roles...")
try:
    for email, expected in EXPECTED_ROLES.items():
        result = supabase.table('profiles').update({
            'role': expected['role'],
            'subscription_status': expected['subscription_status']
        }).eq('email', email).execute()
        
        if result.data:
            print(f"   ✅ Updated {email} → role: {expected['role']}")
        else:
            print(f"   ❌ Failed to update {email}")
            
except Exception as e:
    print(f"   ❌ Error updating roles: {e}")

# Step 2: Test authentication for each user
print("\n2. Testing authentication...")

def test_auth(email, password="testpassword123"):
    try:
        # Create client with anon key for auth testing
        auth_client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        
        response = auth_client.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.user and response.session:
            print(f"   ✅ Auth works: {email}")
            
            # Test JWT validation
            import jwt
            try:
                payload = jwt.decode(
                    response.session.access_token,
                    os.getenv('SUPABASE_JWT_SECRET'),
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                print(f"   ✅ JWT valid: {payload.get('email')}")
                return True
            except Exception as jwt_error:
                print(f"   ⚠️  JWT invalid: {jwt_error}")
                return False
        else:
            print(f"   ❌ Auth failed: {email}")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth error {email}: {e}")
        return False

# Test all users
auth_results = {}
for email in EXPECTED_ROLES.keys():
    auth_results[email] = test_auth(email)

# Step 3: Verify profiles
print("\n3. Verifying final state...")
try:
    profiles = supabase.table('profiles').select('*').execute()
    
    for profile in profiles.data:
        email = profile['email']
        expected = EXPECTED_ROLES.get(email, {})
        
        print(f"\n   📧 {email}")
        print(f"      Role: {profile['role']} (expected: {expected.get('role', 'unknown')})")
        print(f"      Subscription: {profile['subscription_status']} (expected: {expected.get('subscription_status', 'unknown')})")
        print(f"      Auth works: {auth_results.get(email, False)}")
        
except Exception as e:
    print(f"   ❌ Error checking final state: {e}")

# Step 4: Summary
print("\n" + "=" * 50)
print("SETUP SUMMARY")
print("=" * 50)

all_working = all(auth_results.values())

if all_working:
    print("🎉 SUCCESS! All users are working correctly!")
    print()
    print("You can now log in to your application with:")
    print("- Admin: admin-user@test.com / testpassword123")
    print("- Subscriber: paid-user@test.com / testpassword123")  
    print("- Free user: free-user@test.com / testpassword123")
    print()
    print("Your Supabase authentication is working! 🚀")
else:
    print("⚠️  Some users have authentication issues")
    print("Check the JWT secret in your .env file")

print("\nNote: You have a database trigger that auto-creates profiles.")
print("Future user creation will work automatically!") 