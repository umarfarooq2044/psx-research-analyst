import os
import sys
from sqlalchemy import create_engine, text

# The constructed URL with encoded password
URL = "postgresql://postgres:bGR%2FJP%2A3cSzv2%2FJ@db.teyjlbonzmhowalpoedu.supabase.co:5432/postgres"

print(f"🔌 Testing connection to: {URL.split('@')[-1]}")

try:
    engine = create_engine(URL)
    with engine.connect() as conn:
        print("✅ CONNECTION SUCCESSFUL!")
        result = conn.execute(text("SELECT version()")).fetchone()
        print(f"✅ DB VERSION: {result[0]}")
except Exception as e:
    print("\n❌ CONNECTION FAILED")
    print("-" * 20)
    print(e)
    print("-" * 20)
