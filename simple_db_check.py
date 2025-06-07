import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
from core.settings import settings

async def check_db():
    # Create a simple engine for this check
    engine = create_async_engine(
        settings.db_connection_string,
        echo=False,
        pool_pre_ping=True,
        future=True
    )
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        try:
            print('=== CHECKING AVAILABLE TABLES ===')
            result = await session.execute(text("""
                SELECT table_schema, table_name 
                FROM information_schema.tables 
                WHERE table_schema IN ('public', 'auth') 
                AND table_type = 'BASE TABLE'
                ORDER BY table_schema, table_name
            """))
            tables = result.fetchall()
            for table in tables:
                print(f'{table[0]}.{table[1]}')
            
            print('\n=== USER_PROFILES TABLE ===')
            try:
                result = await session.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_profiles' AND table_schema = 'public'
                    ORDER BY ordinal_position
                """))
                columns = result.fetchall()
                if columns:
                    print('Columns:')
                    for col in columns:
                        print(f'  {col[0]}: {col[1]}')
                    
                    # Check data
                    result = await session.execute(text('SELECT id, email, role, subscription_status FROM user_profiles LIMIT 10'))
                    users = result.fetchall()
                    print(f'\nUser profiles ({len(users)} shown):')
                    for user in users:
                        print(f'  ID: {user[0][:8]}..., Email: {user[1]}, Role: {user[2]}, Sub: {user[3]}')
                else:
                    print('user_profiles table not found or no columns')
            except Exception as e:
                print(f'Error with user_profiles: {e}')
            
            print('\n=== AUTH.USERS TABLE ===')
            try:
                result = await session.execute(text('SELECT id, email FROM auth.users LIMIT 5'))
                users = result.fetchall()
                print(f'Auth users ({len(users)} shown):')
                for user in users:
                    print(f'  ID: {user[0][:8]}..., Email: {user[1]}')
            except Exception as e:
                print(f'Error with auth.users: {e}')
                
        except Exception as e:
            print(f'Error: {e}')
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db()) 