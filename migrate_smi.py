import os
import sys
from sqlalchemy import text
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.models import get_engine

def run_migration():
    engine = get_engine()
    print(f"Running migration on: {'Supabase' if 'supabase' in str(engine.url) else 'Local DB'}")
    
    with engine.connect() as conn:
        # Check if columns exist and add them if not
        # This is for PostgreSQL (Supabase)
        try:
            # AI Decisions columns
            conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS signal VARCHAR;"))
            conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS future_path TEXT;"))
            conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN IF NOT EXISTS black_swan TEXT;"))
            
            # Technical Indicators columns (added for SMI-v3 Ultra)
            conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN IF NOT EXISTS obv FLOAT;"))
            conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN IF NOT EXISTS accumulation_distribution FLOAT;"))
            conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN IF NOT EXISTS atr FLOAT;"))
            conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN IF NOT EXISTS volume_acceleration FLOAT;"))
            conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN IF NOT EXISTS trend VARCHAR;"))
            
            conn.commit()
            print("✅ Migration Successful: Added SMI-v1 and SMI-v3 Ultra columns.")
        except Exception as e:
            # If SQLite, the syntax is different or it might already have been handled by create_all if fresh
            print(f"Migration Info: {e}")
            print("Attempting SQLite fallback...")
            try:
                # SQLite doesn't support ADD COLUMN IF NOT EXISTS easily in one line without check
                conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN signal VARCHAR;"))
                conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN future_path TEXT;"))
                conn.execute(text("ALTER TABLE ai_decisions ADD COLUMN black_swan TEXT;"))
                conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN obv FLOAT;"))
                conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN accumulation_distribution FLOAT;"))
                conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN atr FLOAT;"))
                conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN volume_acceleration FLOAT;"))
                conn.execute(text("ALTER TABLE technical_indicators ADD COLUMN trend VARCHAR;"))
                conn.commit()
            except:
                print("Columns likely already exist in SQLite.")

if __name__ == "__main__":
    run_migration()
