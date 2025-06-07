import os
import psycopg2
from datetime import datetime

def update_existing_user():
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
        
        print('=== UPDATING EXISTING USER TO BASIC ===')
        
        # 1. Update the free user to basic for testing
        cur.execute("""
            UPDATE profiles 
            SET role = 'basic', 
                subscription_status = 'active',
                updated_at = %s
            WHERE email = 'free-user@test.com'
        """, (datetime.utcnow(),))
        
        if cur.rowcount > 0:
            print('✅ Updated free-user@test.com to basic role')
        else:
            print('❌ Could not find free-user@test.com to update')
            
        # 2. Update existing subscriber to premium (for clarity)
        cur.execute("""
            UPDATE profiles 
            SET role = 'premium', updated_at = %s
            WHERE role = 'subscriber'
        """, (datetime.utcnow(),))
        
        updated_count = cur.rowcount
        if updated_count > 0:
            print(f'✅ Updated {updated_count} subscriber(s) to premium role')
        
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
        
        # Now we need to create a new free user
        print('\n=== CREATING NEW FREE USER ===')
        print('We now have basic and premium users, but we need a free user for testing.')
        print('You can create one through the frontend signup, or we can add one to auth.users + profiles')
        
    except Exception as e:
        print(f'❌ Error: {e}')
        if 'conn' in locals():
            conn.rollback()
            conn.close()

if __name__ == "__main__":
    update_existing_user() 