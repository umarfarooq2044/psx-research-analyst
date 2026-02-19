"""
PSX Research Analyst - One-Time Sync: Local SQLite → Supabase
Uploads all announcements (including extracted PDF text) to Supabase.
After this, CI and local runs both use Supabase — only new announcements get inserted.

Usage:
  1. Add DATABASE_URL to your .env file
  2. Run: python sync_announcements_to_supabase.py
"""
import os
import sys
import time

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
if not DATABASE_URL:
    print("❌ DATABASE_URL not set in .env file!")
    print("   Add this line to your .env:")
    print("   DATABASE_URL=postgresql://postgres:PASSWORD@db.XXXXX.supabase.co:5432/postgres")
    sys.exit(1)


def get_local_sqlite_connection():
    """Connect to the local SQLite database"""
    import sqlite3
    db_path = os.path.join(os.path.dirname(__file__), 'psx_data.db')
    if not os.path.exists(db_path):
        print(f"❌ Local database not found: {db_path}")
        sys.exit(1)
    return sqlite3.connect(db_path)


def get_supabase_engine():
    """Connect to Supabase PostgreSQL"""
    from sqlalchemy import create_engine
    url = DATABASE_URL
    # Fix for SQLAlchemy: postgres:// → postgresql://
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return create_engine(url)


def sync_tickers(sqlite_conn, pg_engine):
    """Sync tickers first (FK dependency)"""
    cur = sqlite_conn.cursor()
    cur.execute("SELECT symbol, name, sector, is_active FROM tickers")
    rows = cur.fetchall()
    
    if not rows:
        print("  No tickers to sync.")
        return 0
    
    from sqlalchemy import text
    count = 0
    with pg_engine.connect() as conn:
        for symbol, name, sector, is_active in rows:
            try:
                conn.execute(text("""
                    INSERT INTO tickers (symbol, name, sector, is_active) 
                    VALUES (:sym, :name, :sector, :active)
                    ON CONFLICT (symbol) DO UPDATE SET 
                        name = EXCLUDED.name, 
                        sector = EXCLUDED.sector
                """), {'sym': symbol, 'name': name, 'sector': sector, 'active': is_active or 1})
                count += 1
            except Exception as e:
                pass  # Skip individual ticker errors
        conn.commit()
    
    print(f"  ✅ Synced {count} tickers")
    return count


def sync_announcements(sqlite_conn, pg_engine, batch_size=200):
    """Bulk sync announcements from local SQLite to Supabase PostgreSQL"""
    cur = sqlite_conn.cursor()
    cur.execute("""
        SELECT symbol, announcement_date, headline, content, pdf_url, 
               announcement_type, sentiment_score, processed
        FROM announcements
        ORDER BY id
    """)
    rows = cur.fetchall()
    
    if not rows:
        print("  No announcements to sync.")
        return 0, 0
    
    total = len(rows)
    print(f"  📊 Found {total} announcements in local SQLite")
    
    from sqlalchemy import text
    inserted = 0
    skipped = 0
    errors = 0
    
    with pg_engine.connect() as conn:
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            
            for row in batch:
                symbol, ann_date, headline, content, pdf_url, ann_type, sentiment, processed = row
                try:
                    # Use ON CONFLICT to skip duplicates
                    result = conn.execute(text("""
                        INSERT INTO announcements 
                            (symbol, announcement_date, headline, content, pdf_url, 
                             announcement_type, sentiment_score, processed, created_at)
                        VALUES 
                            (:symbol, :ann_date, :headline, :content, :pdf_url, 
                             :ann_type, :sentiment, :processed, NOW())
                        ON CONFLICT (symbol, headline, announcement_date) DO UPDATE SET
                            content = CASE 
                                WHEN EXCLUDED.content IS NOT NULL AND EXCLUDED.content != '' 
                                THEN EXCLUDED.content 
                                ELSE announcements.content 
                            END,
                            pdf_url = COALESCE(EXCLUDED.pdf_url, announcements.pdf_url),
                            processed = GREATEST(EXCLUDED.processed, announcements.processed),
                            sentiment_score = COALESCE(EXCLUDED.sentiment_score, announcements.sentiment_score)
                    """), {
                        'symbol': symbol,
                        'ann_date': ann_date,
                        'headline': headline,
                        'content': content,
                        'pdf_url': pdf_url,
                        'ann_type': ann_type,
                        'sentiment': sentiment,
                        'processed': processed or 0
                    })
                    inserted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 5:
                        print(f"    ⚠️ Error for {symbol}: {str(e)[:80]}")
            
            conn.commit()
            pct = min(100, (i + len(batch)) * 100 // total)
            print(f"    Progress: {i + len(batch)}/{total} ({pct}%) — {inserted} upserted, {errors} errors", end='\r')
    
    print(f"\n  ✅ Synced {inserted} announcements ({errors} errors)")
    return inserted, errors


def verify_sync(pg_engine):
    """Quick verification of Supabase data"""
    from sqlalchemy import text
    with pg_engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM announcements")).scalar()
        with_content = conn.execute(text("SELECT COUNT(*) FROM announcements WHERE content IS NOT NULL AND content != ''")).scalar()
        with_pdf = conn.execute(text("SELECT COUNT(*) FROM announcements WHERE pdf_url IS NOT NULL AND pdf_url != ''")).scalar()
        tickers = conn.execute(text("SELECT COUNT(*) FROM tickers")).scalar()
    
    print(f"\n  📊 Supabase verification:")
    print(f"     Tickers:              {tickers}")
    print(f"     Total announcements:  {total}")
    print(f"     With PDF URL:         {with_pdf}")
    print(f"     With extracted text:  {with_content}")


if __name__ == '__main__':
    print("=" * 60)
    print("📤 Syncing Local SQLite → Supabase")
    print("=" * 60)
    start = time.time()
    
    # Connect
    print("\n[1/4] Connecting...")
    sqlite_conn = get_local_sqlite_connection()
    pg_engine = get_supabase_engine()
    print(f"  ✅ Connected to both databases")
    
    # Ensure tables exist in Supabase
    print("\n[2/4] Ensuring Supabase tables...")
    from database.models import Base
    Base.metadata.create_all(bind=pg_engine)
    print(f"  ✅ Tables ready")
    
    # Sync tickers first (FK dependency)
    print("\n[3/4] Syncing tickers...")
    sync_tickers(sqlite_conn, pg_engine)
    
    # Sync announcements
    print("\n[4/4] Syncing announcements...")
    sync_announcements(sqlite_conn, pg_engine)
    
    # Verify
    verify_sync(pg_engine)
    
    sqlite_conn.close()
    elapsed = time.time() - start
    print(f"\n✅ Done in {elapsed:.1f}s")
