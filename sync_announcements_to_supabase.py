"""
PSX Research Analyst - Full Sync with OCR Support
==================================================
Step 1: Extract text from ALL financial report PDFs using LOCAL SQLite
  - Uses PyMuPDF for digital PDFs (fast, reliable)
  - Falls back to Tesseract OCR for scanned image PDFs
Step 2: Upload all announcements with full text to Supabase
After this, CI reads from Supabase — no PSX scraping needed.

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

os.environ['PYTHONUNBUFFERED'] = '1'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL', '')
SQLITE_PATH = os.path.join(os.path.dirname(__file__), 'psx_data.db')

# Tesseract path (Windows default)
TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


# ============================================================================
# PDF Text Extraction: PyMuPDF + Tesseract OCR fallback
# ============================================================================

def extract_text_from_pdf_bytes(pdf_bytes):
    """
    Extract text from PDF bytes using a 2-stage pipeline:
    1. PyMuPDF (fitz) - fast, handles digital PDFs well
    2. Tesseract OCR via PyMuPDF rendering - for scanned image PDFs
    
    Returns: (text, method) where method is 'pymupdf', 'ocr', or None
    """
    import fitz  # PyMuPDF
    import warnings
    warnings.filterwarnings('ignore')
    
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception:
        return None, None
    
    # Stage 1: Try PyMuPDF text extraction (fast)
    text_parts = []
    for page in doc:
        page_text = page.get_text()
        if page_text:
            text_parts.append(page_text)
    
    full_text = "\n".join(text_parts).strip()
    
    if len(full_text) >= 200:
        doc.close()
        return full_text, 'pymupdf'
    
    # Stage 2: OCR with Tesseract (for scanned pages)
    try:
        import pytesseract
        from PIL import Image
        from io import BytesIO
        
        # Set Tesseract path
        if os.path.exists(TESSERACT_PATH):
            pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        
        ocr_parts = []
        for page_num, page in enumerate(doc):
            # Render page as image (300 DPI for good OCR quality)
            mat = fitz.Matrix(300/72, 300/72)  # 300 DPI
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            
            # OCR the image
            img = Image.open(BytesIO(img_bytes))
            page_text = pytesseract.image_to_string(img, lang='eng')
            
            if page_text and page_text.strip():
                ocr_parts.append(page_text.strip())
        
        doc.close()
        ocr_text = "\n".join(ocr_parts).strip()
        
        if len(ocr_text) >= 100:
            return ocr_text, 'ocr'
        else:
            return None, None
            
    except ImportError:
        doc.close()
        return None, None
    except Exception as e:
        doc.close()
        return None, None


def clean_financial_text(text):
    """Clean extracted text for storage"""
    import re
    if not text:
        return text
    # Remove excessive whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove null bytes
    text = text.replace('\x00', '')
    return text.strip()


def pull_announcements_from_supabase(pg_engine, batch_size=500):
    """
    Download ALL announcements from Supabase to local SQLite.
    This ensures local SQLite has everything that was scraped on CI/Cloud.
    """
    print(f"\n[0.1] Pulling announcements from Supabase...")
    from sqlalchemy import text
    
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    
    inserted = 0
    updated = 0
    
    with pg_engine.connect() as pg:
        # Get total count first
        total_cloud = pg.execute(text("SELECT COUNT(*) FROM announcements")).scalar()
        print(f"  Cloud contains {total_cloud} announcements.")
        
        # Pull in batches
        for offset in range(0, total_cloud, batch_size):
            rows = pg.execute(text(f"SELECT symbol, announcement_date, headline, content, pdf_url, announcement_type, sentiment_score, processed FROM announcements ORDER BY id LIMIT {batch_size} OFFSET {offset}")).fetchall()
            
            for row in rows:
                symbol, ann_date, headline, content, pdf_url, ann_type, sentiment, processed = row
                
                # Check if exists locally
                cur.execute("SELECT id, content, processed FROM announcements WHERE symbol = ? AND headline = ? AND announcement_date = ?", (symbol, headline, ann_date))
                local_row = cur.fetchone()
                
                if not local_row:
                    cur.execute("INSERT INTO announcements (symbol, announcement_date, headline, content, pdf_url, announcement_type, sentiment_score, processed) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (symbol, ann_date, headline, content, pdf_url, ann_type, sentiment, processed or 0))
                    inserted += 1
                else:
                    # Update if cloud version has more info
                    local_id, local_content, local_processed = local_row
                    if (content and not local_content) or (processed and processed > local_processed):
                        cur.execute("UPDATE announcements SET content = COALESCE(?, content), processed = MAX(?, processed), sentiment_score = COALESCE(?, sentiment_score) WHERE id = ?", (content, processed, sentiment, local_id))
                        updated += 1
            
            conn.commit()
            done = min(offset + len(rows), total_cloud)
            print(f"    [{done}/{total_cloud}] {done*100//total_cloud}% pulled...", end='\r', flush=True)
            
    conn.close()
    print(f"\n  ✅ Pulled {inserted} new announcements, updated {updated} existing.")


# ============================================================================
# STEP 1: Extract PDF text locally (all unprocessed financial reports)
# ============================================================================

def extract_all_pdf_text_locally():
    """
    Extract text from ALL financial report PDFs using LOCAL SQLite.
    Uses PyMuPDF + Tesseract OCR for scanned images.
    """
    # Force local SQLite
    saved_url = os.environ.pop('DATABASE_URL', None)
    
    try:
        conn = sqlite3.connect(SQLITE_PATH)
        cur = conn.cursor()
        
        # Reset previously failed ones to try again with OCR
        cur.execute("UPDATE announcements SET processed = 0 WHERE processed = 2")
        reset_count = cur.rowcount
        conn.commit()
        if reset_count > 0:
            print(f"  Reset {reset_count} previously failed PDFs for OCR retry")
        
        # Count pending
        cur.execute("""
            SELECT COUNT(*) FROM announcements 
            WHERE pdf_url IS NOT NULL AND pdf_url != '' AND processed = 0
        """)
        total_pending = cur.fetchone()[0]
        
        # Financial report keywords
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
            print("  All financial report PDFs already extracted!")
            conn.close()
            return
        
        # Check Tesseract availability
        try:
            import pytesseract
            if os.path.exists(TESSERACT_PATH):
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
            ver = pytesseract.get_tesseract_version()
            print(f"  Tesseract OCR: v{ver} (scanned PDFs will be OCR'd)")
        except Exception:
            print("  Tesseract OCR: NOT available (scanned PDFs will be skipped)")
        
        import requests
        from config import PSX_BASE_URL
        
        extracted = 0
        ocr_count = 0
        failed = 0
        
        for i, (ann_id, symbol, headline, pdf_url) in enumerate(financial_pending):
            try:
                if not pdf_url.startswith('http'):
                    pdf_url = PSX_BASE_URL + pdf_url
                
                # Download PDF
                resp = requests.get(pdf_url, timeout=20, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                })
                
                if resp.status_code != 200:
                    cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                    failed += 1
                    continue
                
                # Extract text (PyMuPDF first, then OCR fallback)
                raw_text, method = extract_text_from_pdf_bytes(resp.content)
                
                if raw_text and len(raw_text.strip()) >= 100:
                    clean_text = clean_financial_text(raw_text)
                    cur.execute(
                        "UPDATE announcements SET content = ?, processed = 1 WHERE id = ?",
                        (clean_text, ann_id)
                    )
                    extracted += 1
                    if method == 'ocr':
                        ocr_count += 1
                else:
                    cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                    failed += 1
                
            except Exception as e:
                cur.execute("UPDATE announcements SET processed = 2 WHERE id = ?", (ann_id,))
                failed += 1
            
            # Commit every 5 and show progress
            if (i + 1) % 5 == 0 or i == len(financial_pending) - 1:
                conn.commit()
                print(f"    [{i+1}/{len(financial_pending)}] {extracted} extracted ({ocr_count} via OCR), {failed} failed", flush=True)
        
        conn.commit()
        conn.close()
        
        print(f"\n  PDF extraction complete!")
        print(f"    Digital (PyMuPDF):  {extracted - ocr_count}")
        print(f"    Scanned (OCR):     {ocr_count}")
        print(f"    Failed:            {failed}")
        
    finally:
        if saved_url:
            os.environ['DATABASE_URL'] = saved_url


# ============================================================================
# STEP 2: Upload everything to Supabase
# ============================================================================

def get_supabase_engine():
    from sqlalchemy import create_engine
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return create_engine(url)


def sync_tickers_to_supabase(pg_engine):
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
                        name = EXCLUDED.name, sector = EXCLUDED.sector
                """), {'sym': symbol, 'name': name, 'sector': sector, 'active': is_active or 1})
                count += 1
            except Exception:
                pass
        pg.commit()
    print(f"  Synced {count} tickers")


def sync_announcements_to_supabase(pg_engine, batch_size=100):
    conn = sqlite3.connect(SQLITE_PATH)
    cur = conn.cursor()
    cur.execute("""
        SELECT symbol, announcement_date, headline, content, pdf_url, 
               announcement_type, sentiment_score, processed
        FROM announcements ORDER BY id
    """)
    rows = cur.fetchall()
    conn.close()
    
    total = len(rows)
    if not total:
        print("  No announcements to sync.")
        return
    
    with_content = sum(1 for r in rows if r[3])
    print(f"  Local: {total} announcements, {with_content} with extracted text")
    
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
                                THEN EXCLUDED.content ELSE announcements.content END,
                            pdf_url = COALESCE(EXCLUDED.pdf_url, announcements.pdf_url),
                            processed = GREATEST(EXCLUDED.processed, announcements.processed),
                            sentiment_score = COALESCE(EXCLUDED.sentiment_score, announcements.sentiment_score)
                    """), {
                        'symbol': symbol, 'ann_date': ann_date, 'headline': headline,
                        'content': content, 'pdf_url': pdf_url, 'ann_type': ann_type,
                        'sentiment': sentiment, 'processed': processed or 0
                    })
                    upserted += 1
                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f"    Error for {symbol}: {str(e)[:80]}")
            pg.commit()
            done = min(i + len(batch), total)
            print(f"    [{done}/{total}] {done*100//total}% uploaded...", flush=True)
    
    print(f"  Uploaded {upserted} announcements to Supabase ({errors} errors)")


def verify_supabase(pg_engine):
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
    
    print(f"\n  Supabase verification:")
    print(f"     Tickers:               {tickers}")
    print(f"     Total announcements:   {total}")
    print(f"     With PDF URL:          {with_pdf}")
    print(f"     With full report text: {with_content}")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print(" PSX Full Sync: Pull -> Extract (OCR) -> Push back to Supabase")
    print("=" * 60, flush=True)
    overall_start = time.time()
    
    if not DATABASE_URL:
        print("\n❌ DATABASE_URL not set in .env file!")
        sys.exit(1)
        
    pg_engine = get_supabase_engine()
    
    # ── Step 0: Pull from Supabase ──
    print("\n" + "-" * 60)
    print("STEP 0: Pulling missing announcements from Supabase")
    print("-" * 60, flush=True)
    pull_announcements_from_supabase(pg_engine)
    
    # ── Step 1: Extract PDFs using LOCAL SQLite ──
    print("\n" + "-" * 60)
    print("STEP 1: Extracting PDF text (PyMuPDF + Tesseract OCR)")
    print("-" * 60, flush=True)
    extract_all_pdf_text_locally()
    
    # ── Step 2: Upload to Supabase ──
    print("\n" + "-" * 60)
    print("STEP 2: Uploading to Supabase")
    print("-" * 60, flush=True)
    
    print("\n[2.1] Ensuring tables exist...", flush=True)
    from database.models import Base
    Base.metadata.create_all(bind=pg_engine)
    print("  Tables ready")
    
    print("\n[2.2] Syncing tickers...", flush=True)
    sync_tickers_to_supabase(pg_engine)
    
    print("\n[2.3] Uploading announcements + text...", flush=True)
    sync_announcements_to_supabase(pg_engine)
    
    print("\n[2.4] Verifying...", flush=True)
    verify_supabase(pg_engine)
    
    elapsed = time.time() - overall_start
    print(f"\n{'=' * 60}")
    print(f" Done in {elapsed:.1f}s")
    print(f" CI reads from Supabase - no PSX scraping needed!")
    print(f"{'=' * 60}")
