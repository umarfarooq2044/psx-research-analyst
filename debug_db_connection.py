import os
import sys
from sqlalchemy import create_engine, text

    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

    print("="*60)
    print("DATABASE CONNECTION DEBUGGER")
    print("="*60)
    
    # 1. Check Env Var
    db_url = os.environ.get('DATABASE_URL')
    print(f"Checking DATABASE_URL environment variable...")
    if not db_url:
        print("❌ DATABASE_URL is NOT set.")
        print("   -> System will fall back to SQLite (Local Mode).")
        print("   -> Data will NOT be saved to Supabase.")
    else:
        masked = db_url.replace(db_url.split('@')[0], 'postgresql://****:****') if '@' in db_url else 'Invalid Format'
        print(f"✅ DATABASE_URL is set: {masked}")
        
    # 2. Check DB Manager Logic
    try:
        from database.db_manager import db
        print(f"\nDBManager Initialized.")
        print(f"Engine Dialect: {db.engine.dialect.name}")
        
        if db.engine.dialect.name == 'sqlite':
            print("⚠️ RUNNING IN SQLITE MODE")
            print("   This explains why you don't see tables in Supabase.")
        else:
            print("✅ RUNNING IN POSTGRESQL MODE")
            
            # 3. Test Connection
            print("\nTesting Connection to Supabase...")
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                print("✅ Connection Successful! (SELECT 1 returned)")
                
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")
        
if __name__ == "__main__":
    debug_connection()
