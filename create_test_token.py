#!/usr/bin/env python3
"""
Generate test JWT tokens for authentication testing
"""
import os
import uuid
from jose import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_test_token(user_id: str, email: str, role: str = "free"):
    """Create a test JWT token"""
    secret = os.getenv("SUPABASE_JWT_SECRET", "test_secret_key")
    
    payload = {
        "sub": user_id,
        "email": email,
        "iat": datetime.utcnow(),
        "exp": datetime.utcnow() + timedelta(hours=1),
        "role": role
    }
    
    return jwt.encode(payload, secret, algorithm="HS256")

if __name__ == "__main__":
    # Create tokens for different roles using proper UUID format
    users = [
        (str(uuid.uuid4()), "free@example.com", "free"),
        (str(uuid.uuid4()), "subscriber@example.com", "subscriber"),
        (str(uuid.uuid4()), "admin@example.com", "admin")
    ]
    
    print("🔐 Generated Test JWT Tokens (with UUID format)")
    print("=" * 60)
    
    for user_id, email, role in users:
        token = create_test_token(user_id, email, role)
        print(f"\n{role.upper()} USER:")
        print(f"ID: {user_id}")
        print(f"Email: {email}")
        print(f"Token: {token}")
        print("Test command:")
        print(f'curl -H "Authorization: Bearer {token}" http://localhost:8000/me')
    
    print("\n✨ These tokens use proper UUID format and won't generate database errors!")
    print("\nNote: These test users don't exist in the database, so they'll default to 'free' role.")
    print("To test actual roles, create real users in Supabase Auth and get real JWT tokens.") 