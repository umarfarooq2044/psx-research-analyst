import sys

def check_env():
    # Fix Windows console encoding
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
    print("🔍 CLOUD ENVIRONMENT DIAGNOSTIC")
    print("="*40)
    
    # 1. Check Database
    db_url = os.environ.get("DATABASE_URL")
    if db_url:
        print("✅ DATABASE_URL: SET")
        if "supabase" in db_url:
             print("   - Type: Supabase (PostgreSQL)")
        elif "sqlite" in db_url:
             print("   - Type: SQLite (Local)")
        else:
             print("   - Type: Unknown")
    else:
        print("❌ DATABASE_URL: MISSING (Using SQLite/Ephemeral!)")
        print("   -> Go to Settings > Secrets in GitHub and add DATABASE_URL")

    # 2. Check Gemini
    ai_key = os.environ.get("GEMINI_API_KEY")
    if ai_key:
        print("✅ GEMINI_API_KEY: SET")
        print("   -> AI Features: ENABLED")
    else:
        print("⚠️ GEMINI_API_KEY: MISSING")
        print("   -> AI Features: DISABLED (Safe Mode)")

    # 3. Check Email
    email = os.environ.get("EMAIL_SENDER")
    pwd = os.environ.get("EMAIL_PASSWORD")
    if email and pwd:
        print("✅ EMAIL CREDENTIALS: SET")
    else:
        print("❌ EMAIL CREDENTIALS: MISSING (No reports will send)")

    print("="*40)
    
    # Simple Connection Test
    if db_url and "postgres" in db_url:
        print("\nTesting DB Connection...")
        try:
            from sqlalchemy import create_engine
            engine = create_engine(db_url)
            with engine.connect() as conn:
                print("✅ Connection Successful!")
        except Exception as e:
            print(f"❌ Connection Failed: {e}")

if __name__ == "__main__":
    check_env()
