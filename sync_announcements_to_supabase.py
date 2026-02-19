"""
PSX Research Analyst - Full Sync: Extract PDFs Locally → Upload to Supabase
============================================================================
Step 1: Extract text from ALL financial report PDFs using LOCAL SQLite
Step 2: Upload all announcements (with full text) from SQLite to Supabase
After this, CI reads from Supabase — only new announcements get inserted.

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

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'psx_data.db')


# ============================================================================
# STEP 1: Extract PDF text locally using SQLite (NOT Supabase)
# ============================================================================

def extract_all_pdf_text_locally():
    """
    Extract text from ALL financial report PDFs using LOCAL SQLite.
    Forces SQLite even if DATABASE_URL is set, so extractions are fast.
    """
    import warnings
    warnings.filterwarnings('ignore')  # Suppress PyPDF2 warnings
    
    # Force local SQLite by temporarily removing DATABASE_URL
    saved_url = os.environ.pop('DATABASE_URL', None)
    
    try:
        # Reimport to ensure we use SQLite
        # We do the DB operations directly with sqlite3 for speed
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        
        # Count pending financial reports
        cur.execute("""
            SELECT COUNT(*) FROM announcements 
            WHERE pdf_url IS NOT NULL AND pdf_url != '' AND processed = 0
        """)
        total_pending = cur.fetchone()[0]
        
        # Filter for financial keywords
        FINANCIAL_KEYWORDS = [
            'financial result', 'financial statement', 'quarterly report',
            'quarterly result', 'annual report', 'annual result',
            'half year', 'half-year', 'interim report', 'condensed interim',
            'un-audited', 'unaudited', 'audited financial', 'accounts for',
            'profit after tax', 'balance sheet', 'income statement',
            'cash flow statement', 'directors report',
        ]
        
        cur.execute("""
            SELECT id, symbol, headline, pdf_url FROM announcements 
            WHERE pdf_url IS NOT NULL AND pdf_url != '' AND processed = 0
            ORDER BY announcement_date DESC
        """)
        all_pending = cur.fetchall()
        
        financial_pending = [
            r for r in all_pending 
            if any(kw in r[2].lower() for kw in FINANCIAL_KEYWORDS)
        ]
        
        cur.execute("SELECT COUNT(*) FROM announcements WHERE processed = 1")
        already_done = cur.fetchone()[0]
        
        print(f"  Already extracted:     {already_done}")
        print(f"  Pending (total):       {total_pending}")
        print(f"  Pending (financial):   {len(financial_pending)}")
        
        if not financial_pending:
            print("  ✅ All financial report PDFs already extracted!")
            conn.close()
            return
        
        # Now extract PDFs using requests + PyPDF2 (synchronous, simpler)
        import requests
        from io import BytesIO
        from PyPDF2 import PdfReader
        from scraper.financial_report_scraper import clean_financial_text
        from config import PSX_BASE_URL
        
        extracted = 0
        failed = 0
        
        for i, (ann_id, symbol, headline, pdf_url) in enumerate(financial_pending):
            try:
                # Ensure full URL
                if not pdf_url.startswith('http'):
                    pdf_url = PSX_BASE_URL + pdf_url
                
                # Download PDF
                resp = requests.get(pdf_url, timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                })
                
                if resp.status_code != 200:
                    cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                    failed += 1
                    continue
                
                # Extract text
                reader = PdfReader(BytesIO(resp.content))
                raw_text = ""
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        raw_text += page_text + "\n"
                
                if len(raw_text.strip()) < 200:
                    # Scanned image PDF
                    cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                    failed += 1
                else:
                    clean_text = clean_financial_text(raw_text)
                    cur.execute(
                        "UPDATE announcements SET content = ?, processed = 1 WHERE id = ?",
                        (clean_text, ann_id)
                    )
                    extracted += 1
                
            except Exception as e:
                cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                failed += 1
            
            # Commit every 5 and show progress
            if (i + 1) % 5 == 0 or i == len(financial_pending) - 1:
                conn.commit()
                print(f"    [{i+1}/{len(financial_pending)}] {extracted} extracted, {failed} failed", flush=True)
        
        conn.commit()
        conn.close()
        
        print(f"\n  ✅ PDF extraction complete: {extracted} extracted, {failed} failed")
        
    finally:
        # Restore DATABASE_URL
        if saved_url:
            os.environ['DATABASE_URL'] = saved_url


# ============================================================================
# STEP 2: Upload everything from SQLite to Supabase
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


def sync_announcements_to_supabase(pg_engine, batch_size=100):
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
    
    with_content = sum(1 for r in rows if r[3])
    print(f"  📊 Local SQLite: {total} announcements, {with_content} with extracted text")
    
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
            print(f"    [{done}/{total}] {done*100//total}% uploaded...", flush=True)
    
    print(f"  ✅ Uploaded {upserted} announcements to Supabase ({errors} errors)")


def verify_supabase(pg_engine):
    """Verify Supabase has the data"""
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
    
    print(f"\n  📊 Supabase verification:")
    print(f"     Tickers:               {tickers}")
    print(f"     Total announcements:   {total}")
    print(f"     With PDF URL:          {with_pdf}")
    print(f"     With full report text: {with_content}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print(" PSX Full Sync: Extract PDFs Locally -> Upload to Supabase")
    print("=" * 60, flush=True)
    overall_start = time.time()
    
    # ── Step 1: Extract PDFs using LOCAL SQLite ──
    print("\n" + "-" * 60)
    print("STEP 1: Extracting PDF text (using local SQLite)")
    print("-" * 60, flush=True)
    extract_all_pdf_text_locally()
    
    # ── Step 2: Upload to Supabase ──
    if not DATABASE_URL:
        print("\n  DATABASE_URL not set. PDF extraction done, but skipping Supabase upload.")
        print("  Add DATABASE_URL to .env and re-run to upload.")
        sys.exit(0)
    
    print("\n" + "-" * 60)
    print("STEP 2: Uploading to Supabase")
    print("-" * 60, flush=True)
    
    pg_engine = get_supabase_engine()
    
    # Ensure tables
    print("\n[2.1] Ensuring tables exist...", flush=True)
    from database.models import Base
    Base.metadata.create_all(bind=pg_engine)
    print("  ✅ Tables ready")
    
    # Sync tickers
    print("\n[2.2] Syncing tickers...", flush=True)
    sync_tickers_to_supabase(pg_engine)
    
    # Sync announcements with text
    print("\n[2.3] Uploading announcements + extracted text...", flush=True)
    sync_announcements_to_supabase(pg_engine)
    
    # Verify
    print("\n[2.4] Verifying...", flush=True)
    verify_supabase(pg_engine)
    
    elapsed = time.time() - overall_start
    print(f"\n{'=' * 60}")
    print(f" Done in {elapsed:.1f}s")
    print(f" CI will now read from Supabase - no PSX scraping needed!")
    print(f"{'=' * 60}")
