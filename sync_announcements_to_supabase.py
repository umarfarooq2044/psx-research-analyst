"""
PSX Research Analyst - Full Sync: Extract PDFs Locally → Upload to Supabase
============================================================================
Step 1: Extract text from ALL financial report PDFs (locally, your home IP)
Step 2: Upload all announcements (with full text) to Supabase
Step 3: CI never needs to touch PSX again — just reads from Supabase

Usage:
  1. Add DATABASE_URL to your .env file
  2. Run: python sync_announcements_to_supabase.py
"""
import os
import sys
import time
import sqlite3

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
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'psx_data.db')


# ============================================================================
# STEP 1: Extract PDF text locally (all unprocessed financial reports)
# ============================================================================

def extract_all_pdf_text_locally():
    """
    Extract text from ALL financial report PDFs in local SQLite.
    This runs on your home IP (not rate-limited by PSX).
    Processes in batches until none are left.
    """
    from scraper.financial_report_scraper import (
        process_unprocessed_reports, get_extraction_stats
    )
    
    stats = get_extraction_stats()
    pending = stats['pending_financial']
    
    if pending == 0:
        print("  ✅ All financial report PDFs already extracted!")
        print(f"     Total extracted: {stats['extracted']}")
        return
    
    print(f"  📄 {pending} financial report PDFs need text extraction")
    print(f"     Already extracted: {stats['extracted']}")
    print(f"     Already failed (scanned): {stats['failed']}")
    
    total_extracted = 0
    total_failed = 0
    batch_num = 0
    
    while True:
        batch_num += 1
        print(f"\n  --- Batch {batch_num} ---")
        
        result = process_unprocessed_reports(batch_size=30, overall_timeout=300)
        
        if result.get('skipped'):
            break
        
        total_extracted += result.get('success', 0)
        total_failed += result.get('failed', 0)
        
        # Check if there are more
        stats = get_extraction_stats()
        remaining = stats['pending_financial']
        
        if remaining == 0:
            break
        
        print(f"  📊 Remaining: {remaining} financial PDFs")
        time.sleep(1)  # Brief pause between batches
    
    print(f"\n  ✅ PDF extraction complete!")
    print(f"     Extracted this run: {total_extracted}")
    print(f"     Failed (scanned):   {total_failed}")
    
    # Final stats
    stats = get_extraction_stats()
    print(f"     Total in DB:        {stats['extracted']} extracted, {stats['failed']} failed")


# ============================================================================
# STEP 2: Sync everything to Supabase
# ============================================================================

def get_supabase_engine():
    """Connect to Supabase PostgreSQL"""
    from sqlalchemy import create_engine
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return create_engine(url)


def sync_tickers_to_supabase(pg_engine):
    """Sync tickers first (FK dependency)"""
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("SELECT symbol, name, sector, is_active FROM tickers")
    rows = cur.fetchall()
    conn.close()
    
    if not rows:
        print("  No tickers to sync.")
        return
    
    from sqlalchemy import text
    count = 0
    with pg_engine.connect() as pg:
        for symbol, name, sector, is_active in rows:
            try:
                pg.execute(text("""
                    INSERT INTO tickers (symbol, name, sector, is_active) 
                    VALUES (:sym, :name, :sector, :active)
                    ON CONFLICT (symbol) DO UPDATE SET 
                        name = EXCLUDED.name, 
                        sector = EXCLUDED.sector
                """), {'sym': symbol, 'name': name, 'sector': sector, 'active': is_active or 1})
                count += 1
            except Exception:
                pass
        pg.commit()
    
    print(f"  ✅ Synced {count} tickers")


def sync_announcements_to_supabase(pg_engine, batch_size=200):
    """
    Upload ALL announcements (with extracted PDF text) to Supabase.
    Uses ON CONFLICT to skip duplicates and merge content.
    """
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, announcement_date, headline, content, pdf_url, 
               announcement_type, sentiment_score, processed
        FROM announcements
        ORDER BY id
    """)
    rows = cur.fetchall()
    conn.close()
    
    total = len(rows)
    if not total:
        print("  No announcements to sync.")
        return
    
    # Count what we have
    with_content = sum(1 for r in rows if r[3])  # content column
    with_pdf = sum(1 for r in rows if r[4])       # pdf_url column
    print(f"  📊 Local SQLite: {total} announcements")
    print(f"     With PDF URL:       {with_pdf}")
    print(f"     With extracted text: {with_content}")
    
    from sqlalchemy import text
    upserted = 0
    errors = 0
    
    with pg_engine.connect() as pg:
        for i in range(0, total, batch_size):
            batch = rows[i:i + batch_size]
            
            for row in batch:
                symbol, ann_date, headline, content, pdf_url, ann_type, sentiment, processed = row
                try:
                    pg.execute(text("""
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
                    upserted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f"    ⚠️ Error for {symbol}: {str(e)[:80]}")
            
            pg.commit()
            done = min(i + len(batch), total)
            print(f"    [{done}/{total}] {done*100//total}% uploaded...", end='\r')
    
    print(f"\n  ✅ Uploaded {upserted} announcements to Supabase ({errors} errors)")


def verify_supabase(pg_engine):
    """Verify Supabase has everything"""
    from sqlalchemy import text
    with pg_engine.connect() as pg:
        total = pg.execute(text("SELECT COUNT(*) FROM announcements")).scalar()
        with_content = pg.execute(text(
            "SELECT COUNT(*) FROM announcements WHERE content IS NOT NULL AND content != ''"
        )).scalar()
        with_pdf = pg.execute(text(
            "SELECT COUNT(*) FROM announcements WHERE pdf_url IS NOT NULL AND pdf_url != ''"
        )).scalar()
        tickers = pg.execute(text("SELECT COUNT(*) FROM tickers")).scalar()
    
    print(f"\n  📊 Supabase now has:")
    print(f"     Tickers:              {tickers}")
    print(f"     Announcements:        {total}")
    print(f"     With PDF URL:         {with_pdf}")
    print(f"     With full report text: {with_content}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("📤 PSX Full Sync: Extract PDFs → Upload to Supabase")
    print("=" * 60)
    overall_start = time.time()
    
    # ── Step 1: Extract all PDF text locally ──
    print("\n" + "─" * 60)
    print("STEP 1: Extracting PDF text from financial reports (local)")
    print("─" * 60)
    extract_all_pdf_text_locally()
    
    # ── Step 2: Upload to Supabase ──
    if not DATABASE_URL:
        print("\n❌ DATABASE_URL not set in .env file!")
        print("   Add this line to your .env:")
        print("   DATABASE_URL=postgresql://postgres:PASSWORD@db.XXXXX.supabase.co:5432/postgres")
        print("\n   PDF text extraction is done. Run again after adding DATABASE_URL to upload.")
        sys.exit(1)
    
    print("\n" + "─" * 60)
    print("STEP 2: Uploading to Supabase")
    print("─" * 60)
    
    pg_engine = get_supabase_engine()
    
    # Ensure tables exist
    print("\n[2.1] Ensuring Supabase tables...")
    from database.models import Base
    Base.metadata.create_all(bind=pg_engine)
    print("  ✅ Tables ready")
    
    # Sync tickers (FK dependency)
    print("\n[2.2] Syncing tickers...")
    sync_tickers_to_supabase(pg_engine)
    
    # Sync announcements with full text
    print("\n[2.3] Uploading announcements + extracted text...")
    sync_announcements_to_supabase(pg_engine)
    
    # Verify
    print("\n[2.4] Verifying...")
    verify_supabase(pg_engine)
    
    elapsed = time.time() - overall_start
    print(f"\n{'=' * 60}")
    print(f"✅ All done in {elapsed:.1f}s")
    print(f"   CI will now read from Supabase — no PSX scraping needed!")
    print(f"{'=' * 60}")
