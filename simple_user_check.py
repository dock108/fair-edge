import os
import psycopg2

def check_users():
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
        
        print('=== CHECKING USER ROLES ===')
        
        # Check if profiles table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = 'profiles'
            )
        """)
        
        if not cur.fetchone()[0]:
            print('❌ Profiles table does not exist')
            conn.close()
            return
        
        print('✅ Profiles table exists')
        
        # Check role distribution
        cur.execute("""
            SELECT role, COUNT(*) as count 
            FROM profiles 
            WHERE role IS NOT NULL 
            GROUP BY role 
            ORDER BY count DESC
        """)
        
        roles = cur.fetchall()
        print('\n📊 Current role distribution:')
        total = 0
        for role, count in roles:
            print(f'   {role}: {count} users')
            total += count
        
        # Check NULL roles
        cur.execute('SELECT COUNT(*) FROM profiles WHERE role IS NULL')
        null_count = cur.fetchone()[0]
        if null_count > 0:
            print(f'   NULL role: {null_count} users')
            total += null_count
        
        print(f'\n👥 Total users: {total}')
        
        # Show sample users
        cur.execute('SELECT id, email, role, subscription_status FROM profiles LIMIT 5')
        users = cur.fetchall()
        print('\n📝 Sample users:')
        for user in users:
            user_id = str(user[0])[:8] + '...'
            print(f'   {user_id} | {user[1]} | role: {user[2]} | sub: {user[3]}')
        
        conn.close()
        
    except Exception as e:
        print(f'❌ Error: {e}')

if __name__ == "__main__":
    check_users() 