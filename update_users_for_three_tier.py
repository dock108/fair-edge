import os
import psycopg2
import uuid
from datetime import datetime

def update_users():
    # Parse the DATABASE_URL
    db_url = os.getenv('DB_CONNECTION_STRING')
    if not db_url:
        print('❌ No DB_CONNECTION_STRING found')
        return

    # Remove asyncpg part for psycopg2
    db_url = db_url.replace('postgresql+asyncpg://', 'postgresql://')

    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        print('=== UPDATING USERS FOR THREE-TIER SYSTEM ===')
        
        # 1. Create a basic user for testing
        basic_user_id = str(uuid.uuid4())
        basic_email = 'basic-user@test.com'
        
        # Check if basic user already exists
        cur.execute('SELECT id FROM profiles WHERE email = %s', (basic_email,))
        existing_basic = cur.fetchone()
        
        if not existing_basic:
            cur.execute("""
                INSERT INTO profiles (id, email, role, subscription_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (basic_user_id, basic_email, 'basic', 'active', datetime.utcnow(), datetime.utcnow()))
            print(f'✅ Created basic user: {basic_email}')
        else:
            print(f'ℹ️  Basic user already exists: {basic_email}')
            
        # 2. Update existing subscriber to premium (for clarity)
        cur.execute("""
            UPDATE profiles 
            SET role = 'premium', updated_at = %s
            WHERE role = 'subscriber'
        """, (datetime.utcnow(),))
        
        updated_count = cur.rowcount
        if updated_count > 0:
            print(f'✅ Updated {updated_count} subscriber(s) to premium role')
        
        # 3. Ensure existing free user has proper role
        cur.execute("""
            UPDATE profiles 
            SET role = 'free', subscription_status = 'none', updated_at = %s
            WHERE email = 'free-user@test.com'
        """, (datetime.utcnow(),))
        
        if cur.rowcount > 0:
            print('✅ Updated free user with correct role')
        
        # Commit changes
        conn.commit()
        
        # Show updated distribution
        cur.execute("""
            SELECT role, COUNT(*) as count 
            FROM profiles 
            GROUP BY role 
            ORDER BY 
                CASE role 
                    WHEN 'admin' THEN 1 
                    WHEN 'premium' THEN 2 
                    WHEN 'basic' THEN 3 
                    WHEN 'free' THEN 4 
                    ELSE 5 
                END
        """)
        
        roles = cur.fetchall()
        print('\n📊 Updated role distribution:')
        for role, count in roles:
            print(f'   {role}: {count} users')
        
        # Show all users for verification
        cur.execute('SELECT id, email, role, subscription_status FROM profiles ORDER BY role')
        users = cur.fetchall()
        print('\n👥 All users:')
        for user in users:
            user_id = str(user[0])[:8] + '...'
            print(f'   {user_id} | {user[1]} | role: {user[2]} | sub: {user[3]}')
        
        conn.close()
        print('\n✅ Database update completed!')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    update_users() 