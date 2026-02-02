import os
import sys
from sqlalchemy import text
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.models import get_engine, init_database

def run_v2_migration():
    engine = get_engine()
    print(f"Running SMI-v2 Migration on: {'Supabase' if 'supabase' in str(engine.url) else 'Local DB'}")
    
    # 1. Check/Add technical_indicators columns
    tech_cols = [
        ("obv", "FLOAT"),
        ("accumulation_distribution", "FLOAT"),
        ("atr", "FLOAT"),
        ("volume_acceleration", "FLOAT")
    ]
    
    # 2. Check/Add ai_decisions columns
    ai_cols = [
        ("score", "INTEGER"),
        ("catalyst", "TEXT")
    ]
    
    with engine.connect() as conn:
        # Technical Indicators
        for col_name, col_type in tech_cols:
            try:
                conn.execute(text(f"ALTER TABLE technical_indicators ADD COLUMN {col_name} {col_type};"))
                conn.commit()
                print(f"Added {col_name} to technical_indicators")
            except Exception as e:
                print(f"{col_name} in technical_indicators likely exists or error: {e}")

        # AI Decisions
        for col_name, col_type in ai_cols:
            try:
                conn.execute(text(f"ALTER TABLE ai_decisions ADD COLUMN {col_name} {col_type};"))
                conn.commit()
                print(f"Added {col_name} to ai_decisions")
            except Exception as e:
                print(f"{col_name} in ai_decisions likely exists or error: {e}")

    # 3. Initialize new tables (LeverageData)
    init_database()
    print("SMI-v2 Migration Complete.")

if __name__ == "__main__":
    run_v2_migration()
