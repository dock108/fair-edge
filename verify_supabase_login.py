import os
from supabase import create_client, Client
from dotenv import load_dotenv
import json  # For parsing potential JSON in exceptions

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

ADMIN_EMAIL = "admin-user@test.com"
# !!! IMPORTANT: Update this if you set a different password via the Supabase Dashboard UI !!!
ADMIN_PASSWORD = "admin123"  # Or your new password, e.g., "NewSupabasePassword123!"

def main():
    print(f"Attempting to log in to Supabase at {SUPABASE_URL}...")
    print(f"Using email: {ADMIN_EMAIL}")
    print(f"Using password: {ADMIN_PASSWORD}")
    
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("Error: SUPABASE_URL or SUPABASE_ANON_KEY not found in .env")
        return

    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        print("Supabase client created.")
        
        response = supabase.auth.sign_in_with_password({"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        
        if response.user:
            print("\n✅ Supabase Login Successful!")
            print(f"User ID: {response.user.id}")
            print(f"Email: {response.user.email}")
            print(f"Role from user object (might be None): {response.user.role}")
            print(f"User Metadata (should contain role): {response.user.user_metadata}")
            if response.session:
                print(f"Access Token: {response.session.access_token[:30]}...")
        else:
            print("\n❌ Supabase Login Failed.")
            # The Supabase client returns an APIResponse object which might contain an error attribute
            # that is an instance of APIError or similar, not always directly on response.error
            error_details = None
            if hasattr(response, 'error') and response.error:  # Check direct error attribute
                error_details = response.error
            elif hasattr(response, 'data') and hasattr(response.data, 'error'):  # Check error in data attribute
                error_details = response.data.error

            if error_details:
                print(f"Error Name: {getattr(error_details, 'name', 'N/A')}")
                print(f"Error Message: {getattr(error_details, 'message', 'No message')}")
                print(f"Error Status: {getattr(error_details, 'status', 'N/A')}")
            else:
                print("Unknown error during login. Raw response content:")
                # Print raw response if possible, might be different for sync client
                if hasattr(response, 'content'):
                    print(response.content)
                else:
                    print(response)  # Fallback to printing the response object itself

    except Exception as e:
        print(f"\n❌ An exception occurred: {str(e)}")
        # If the supabase client raises an APIError, it might have more details
        # GotrueHttpError is a common one for auth issues with the sync client
        if hasattr(e, 'json') and callable(e.json):
            try:
                error_json = e.json()
                print(f"   Supabase API Error JSON: {json.dumps(error_json, indent=2)}")
            except json.JSONDecodeError:
                print("   Could not parse Supabase API Error as JSON.")
            except Exception as json_ex:
                print(f"   Error parsing Supabase API Error JSON: {json_ex}")
        elif hasattr(e, 'message'):  # Some errors might just have a message
            print(f"   Error message from exception: {e.message}")

if __name__ == "__main__":
    main() 