import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Use service role key for admin operations
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Test users to create
TEST_USERS = [
    {
        "email": "free-user@test.com",
        "password": "testpassword123",
        "role": "free",
        "subscription_status": "none"
    },
    {
        "email": "paid-user@test.com", 
        "password": "testpassword123",
        "role": "subscriber",
        "subscription_status": "active"
    },
    {
        "email": "admin-user@test.com",
        "password": "testpassword123", 
        "role": "admin",
        "subscription_status": "none"
    }
]

print("🧹 COMPLETE USER RESET AND SETUP")
print("=" * 60)
print("This will delete ALL users and recreate test users")
input("Press Enter to continue or Ctrl+C to cancel...")

def delete_all_auth_users():
    """Delete ALL users from auth.users table"""
    print("\n1. Deleting ALL auth users...")
    try:
        users = supabase.auth.admin.list_users()
        print(f"   Found {len(users)} auth users to delete")
        
        for user in users:
            try:
                supabase.auth.admin.delete_user(user.id)
                print(f"   ✅ Deleted: {user.email}")
            except Exception as e:
                print(f"   ❌ Error deleting {user.email}: {e}")
                
    except Exception as e:
        print(f"   ❌ Error listing auth users: {e}")

def delete_all_profiles():
    """Delete ALL profiles from profiles table"""
    print("\n2. Deleting ALL profiles...")
    try:
        # Get all profiles first
        all_profiles = supabase.table('profiles').select('id, email').execute()
        print(f"   Found {len(all_profiles.data)} profiles to delete")
        
        # Delete all profiles
        if all_profiles.data:
            result = supabase.table('profiles').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"   ✅ Deleted all profiles")
        else:
            print("   ℹ️  No profiles found")
            
    except Exception as e:
        print(f"   ❌ Error deleting profiles: {e}")

def create_auth_user(user_data):
    """Create user in auth.users table"""
    try:
        response = supabase.auth.admin.create_user({
            "email": user_data["email"],
            "password": user_data["password"],
            "email_confirm": True,  # Auto-confirm email
            "user_metadata": {
                "role": user_data["role"]
            }
        })
        
        if response.user:
            print(f"   ✅ Created auth user: {response.user.email} (ID: {response.user.id})")
            return response.user
        else:
            print(f"   ❌ Failed to create auth user: {user_data['email']}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating auth user {user_data['email']}: {e}")
        return None

def create_profile(auth_user, user_data):
    """Create corresponding profile in profiles table"""
    try:
        profile_data = {
            'id': auth_user.id,
            'email': auth_user.email,
            'role': user_data['role'],
            'subscription_status': user_data['subscription_status']
        }
        
        result = supabase.table('profiles').insert(profile_data).execute()
        
        if result.data:
            print(f"   ✅ Created profile: {auth_user.email} (Role: {user_data['role']})")
            return result.data[0]
        else:
            print(f"   ❌ Failed to create profile: {auth_user.email}")
            return None
            
    except Exception as e:
        print(f"   ❌ Error creating profile {auth_user.email}: {e}")
        return None

def test_authentication(user_data):
    """Test that authentication works for the created user"""
    try:
        # Create client with anon key for auth testing
        auth_client = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_ANON_KEY')
        )
        
        response = auth_client.auth.sign_in_with_password({
            "email": user_data["email"],
            "password": user_data["password"]
        })
        
        if response.user and response.session:
            print(f"   ✅ Auth test passed: {user_data['email']}")
            
            # Test JWT validation
            import jwt
            try:
                payload = jwt.decode(
                    response.session.access_token,
                    os.getenv('SUPABASE_JWT_SECRET'),
                    algorithms=["HS256"],
                    options={"verify_aud": False}
                )
                print(f"   ✅ JWT validation passed for: {payload.get('email')}")
                return True
            except Exception as jwt_error:
                print(f"   ⚠️  JWT validation failed: {jwt_error}")
                return False
        else:
            print(f"   ❌ Auth test failed: {user_data['email']}")
            return False
            
    except Exception as e:
        print(f"   ❌ Auth test error {user_data['email']}: {e}")
        return False

def main():
    # Step 1: Delete everything
    delete_all_auth_users()
    delete_all_profiles()
    
    # Step 2: Create new users
    print("\n3. Creating new test users...")
    created_users = []
    
    for user_data in TEST_USERS:
        print(f"\n   Creating: {user_data['email']} ({user_data['role']})")
        
        # Create auth user
        auth_user = create_auth_user(user_data)
        if not auth_user:
            continue
            
        # Create profile
        profile = create_profile(auth_user, user_data)
        if not profile:
            continue
            
        created_users.append({
            'auth_user': auth_user,
            'profile': profile,
            'user_data': user_data
        })
    
    # Step 3: Test authentication for all users
    print("\n4. Testing authentication...")
    all_tests_passed = True
    
    for created_user in created_users:
        success = test_authentication(created_user['user_data'])
        if not success:
            all_tests_passed = False
    
    # Step 4: Summary
    print("\n" + "=" * 60)
    print("SETUP COMPLETE!")
    print("=" * 60)
    
    if created_users:
        print(f"✅ Successfully created {len(created_users)} test users:")
        print()
        for created_user in created_users:
            user_data = created_user['user_data']
            auth_user = created_user['auth_user']
            print(f"📧 {user_data['email']}")
            print(f"   Password: {user_data['password']}")
            print(f"   Role: {user_data['role']}")
            print(f"   Subscription: {user_data['subscription_status']}")
            print(f"   Auth ID: {auth_user.id}")
            print()
        
        if all_tests_passed:
            print("✅ All authentication tests passed!")
            print()
            print("🎉 Your Supabase authentication is now working correctly!")
            print()
            print("For your web application, use:")
            print("- Admin: admin-user@test.com / testpassword123")
            print("- Subscriber: paid-user@test.com / testpassword123") 
            print("- Free user: free-user@test.com / testpassword123")
        else:
            print("⚠️  Some authentication tests failed - check JWT secret")
            
    else:
        print("❌ No users were created successfully")
        print("Check your Supabase configuration and try again")

if __name__ == "__main__":
    main() 