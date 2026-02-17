"""
PSX Research Analyst - Financial Report PDF Scraper (Incremental)
Downloads company financial report PDFs, extracts full text, stores in DB.
Only processes NEW/unprocessed reports — no re-scanning on subsequent runs.

Status codes in announcements.processed:
  0 = Not yet processed (default)
  1 = Text extracted successfully
  2 = Extraction failed (scanned image / download error / empty)
"""
import asyncio
import aiohttp
import re
import os
import sys
import time

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
from io import BytesIO
from typing import List, Dict, Optional, Tuple
from PyPDF2 import PdfReader

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PSX_BASE_URL, REQUEST_TIMEOUT
from database.db_manager import db
from database.models import get_db_session, Announcement

# Keywords that identify financial report announcements
FINANCIAL_KEYWORDS = [
    'financial result', 'financial statement', 'quarterly report',
    'quarterly result', 'annual report', 'annual result',
    'half year', 'half-year', 'interim report', 'condensed interim',
    'un-audited', 'unaudited', 'audited financial', 'accounts for',
    'profit after tax', 'balance sheet', 'income statement',
    'cash flow statement', 'directors report',
]

# Max concurrent PDF downloads
MAX_WORKERS = 5
# Per-request timeout for PDF download (seconds)
PDF_DOWNLOAD_TIMEOUT = 45
# Minimum text length to consider extraction successful (filters scanned images)
MIN_TEXT_LENGTH = 200


def clean_financial_text(raw_text: str) -> str:
    """
    Clean extracted PDF text by removing noise while preserving financial data.
    """
    if not raw_text:
        return ""
    
    # Normalize whitespace (multiple spaces/tabs → single space)
    text = re.sub(r'[ \t]+', ' ', raw_text)
    
    # Collapse multiple newlines (3+ → 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove page headers/footers (common patterns)
    text = re.sub(r'Page \d+ of \d+', '', text)
    text = re.sub(r'(?i)this page is intentionally left blank', '', text)
    
    # Remove excessive dashes/underscores used as separators
    text = re.sub(r'[-_]{5,}', '---', text)
    text = re.sub(r'[=]{5,}', '===', text)
    
    # Remove null bytes and control characters (except newlines/tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)
    
    # Strip each line
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    return text.strip()


def _is_financial_report(headline: str) -> bool:
    """Check if an announcement headline indicates a financial report."""
    if not headline:
        return False
    lower = headline.lower()
    return any(kw in lower for kw in FINANCIAL_KEYWORDS)


def get_unprocessed_reports(limit: int = 50) -> List[Dict]:
    """
    Get announcements with PDF URLs that haven't been processed yet.
    Filters to only financial report-type announcements.
    """
    with get_db_session() as session:
        rows = session.query(Announcement).filter(
            Announcement.pdf_url.isnot(None),
            Announcement.pdf_url != '',
            Announcement.processed == 0
        ).order_by(Announcement.announcement_date.desc()).limit(limit * 3).all()
        
        # Filter for financial reports and apply limit
        results = []
        for row in rows:
            if _is_financial_report(row.headline):
                results.append({
                    'id': row.id,
                    'symbol': row.symbol,
                    'headline': row.headline,
                    'pdf_url': row.pdf_url,
                    'date': str(row.announcement_date) if row.announcement_date else None
                })
                if len(results) >= limit:
                    break
        
        return results


def update_announcement_content(announcement_id: int, content: Optional[str], status: int):
    """
    Save extracted PDF text to the announcement record.
    
    Args:
        announcement_id: The announcement row ID
        content: Extracted and cleaned text (None on failure)
        status: 1 = success, 2 = failed
    """
    with get_db_session() as session:
        ann = session.query(Announcement).filter_by(id=announcement_id).first()
        if ann:
            ann.content = content
            ann.processed = status


async def _extract_pdf_text(session: aiohttp.ClientSession, pdf_url: str) -> Tuple[Optional[str], int]:
    """
    Download a PDF and extract text in-memory.
    
    Returns:
        (cleaned_text, status) - status 1=success, 2=failed
    """
    # Ensure full URL
    if not pdf_url.startswith('http'):
        pdf_url = PSX_BASE_URL + pdf_url
    
    try:
        timeout = aiohttp.ClientTimeout(total=PDF_DOWNLOAD_TIMEOUT)
        async with session.get(pdf_url, timeout=timeout) as response:
            if response.status != 200:
                return None, 2
            
            # Read PDF bytes into memory (no disk write)
            pdf_bytes = await response.read()
            
            # Extract text with PyPDF
            reader = PdfReader(BytesIO(pdf_bytes))
            raw_text = ""
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    raw_text += page_text + "\n"
            
            # Validate: check if it's a scanned image (too little text)
            if len(raw_text.strip()) < MIN_TEXT_LENGTH:
                return None, 2  # Likely scanned image, needs OCR
            
            # Clean the text
            clean_text = clean_financial_text(raw_text)
            return clean_text, 1
            
    except asyncio.TimeoutError:
        return None, 2
    except Exception as e:
        return None, 2


async def _process_single_report(session: aiohttp.ClientSession, report: Dict, 
                                  semaphore: asyncio.Semaphore) -> Dict:
    """Process a single PDF report with concurrency control."""
    async with semaphore:
        symbol = report['symbol']
        ann_id = report['id']
        
        text, status = await _extract_pdf_text(session, report['pdf_url'])
        
        # Save to DB (sync call, but fast)
        try:
            update_announcement_content(ann_id, text, status)
        except Exception as e:
            print(f"  ⚠️ DB save failed for {symbol} (id={ann_id}): {e}")
            status = 2
        
        return {
            'symbol': symbol,
            'id': ann_id,
            'status': 'ok' if status == 1 else 'failed',
            'text_length': len(text) if text else 0
        }


async def _process_batch_async(reports: List[Dict]) -> Dict:
    """
    Process a batch of PDF reports concurrently.
    Per-task timeout is handled by aiohttp.ClientTimeout.
    """
    semaphore = asyncio.Semaphore(MAX_WORKERS)
    results = {'processed': 0, 'success': 0, 'failed': 0, 'details': []}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = [_process_single_report(session, r, semaphore) for r in reports]
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for item in completed:
                if isinstance(item, Exception):
                    results['failed'] += 1
                elif isinstance(item, dict):
                    results['processed'] += 1
                    if item['status'] == 'ok':
                        results['success'] += 1
                    else:
                        results['failed'] += 1
                    results['details'].append(item)
    except Exception as e:
        print(f"  ⚠️ PDF extraction error: {e}")
    
    return results


def process_unprocessed_reports(batch_size: int = 30, overall_timeout: int = 300) -> Dict:
    """
    Main entry point: find and process unprocessed financial report PDFs.
    
    This is incremental — only processes PDFs where processed=0.
    On subsequent runs, already-processed PDFs are skipped.
    
    Args:
        batch_size: Max reports to process in one run
        overall_timeout: Max seconds for the entire batch
        
    Returns:
        Dict with processing results
    """
    # Step 1: Find unprocessed financial report PDFs
    reports = get_unprocessed_reports(limit=batch_size)
    
    if not reports:
        print("  ✅ No new financial report PDFs to process.")
        return {'processed': 0, 'success': 0, 'failed': 0, 'skipped': True}
    
    print(f"  📄 Found {len(reports)} unprocessed financial report PDFs")
    
    # Show what we're processing
    symbols_summary = {}
    for r in reports:
        sym = r['symbol']
        symbols_summary[sym] = symbols_summary.get(sym, 0) + 1
    top_symbols = sorted(symbols_summary.items(), key=lambda x: -x[1])[:10]
    print(f"  📊 Companies: {', '.join(f'{s}({c})' for s,c in top_symbols)}")
    
    # Step 2: Process them with a thread-level overall timeout
    start = time.time()
    result = {'processed': 0, 'success': 0, 'failed': 0, 'details': []}
    
    def _run_in_thread():
        nonlocal result
        try:
            result = asyncio.run(_process_batch_async(reports))
        except Exception as e:
            print(f"  ⚠️ Async runner error: {e}")
    
    import threading
    thread = threading.Thread(target=_run_in_thread, daemon=True)
    thread.start()
    thread.join(timeout=overall_timeout)
    
    if thread.is_alive():
        print(f"  ⏰ PDF extraction timeout ({overall_timeout}s). Processed {result.get('processed', 0)}/{len(reports)}.")
    
    elapsed = time.time() - start
    
    print(f"  ✅ PDF extraction done in {elapsed:.1f}s → {result.get('success', 0)} extracted, {result.get('failed', 0)} failed")
    
    result['elapsed_seconds'] = round(elapsed, 1)
    return result


def get_financial_report_text(symbol: str, limit: int = 3) -> List[Dict]:
    """
    Get stored financial report text for a company.
    Only returns successfully extracted reports (processed=1).
    
    Args:
        symbol: Ticker symbol
        limit: Max reports to return
        
    Returns:
        List of dicts with headline, date, and extracted text
    """
    with get_db_session() as session:
        rows = session.query(Announcement).filter(
            Announcement.symbol == symbol,
            Announcement.processed == 1,
            Announcement.content.isnot(None)
        ).order_by(Announcement.announcement_date.desc()).limit(limit).all()
        
        return [{
            'id': row.id,
            'symbol': row.symbol,
            'headline': row.headline,
            'date': str(row.announcement_date) if row.announcement_date else None,
            'content': row.content,
            'text_length': len(row.content) if row.content else 0
        } for row in rows]


def get_extraction_stats() -> Dict:
    """Get statistics on PDF extraction progress."""
    with get_db_session() as session:
        total_with_pdf = session.query(Announcement).filter(
            Announcement.pdf_url.isnot(None),
            Announcement.pdf_url != ''
        ).count()
        
        extracted = session.query(Announcement).filter(
            Announcement.processed == 1
        ).count()
        
        failed = session.query(Announcement).filter(
            Announcement.processed == 2
        ).count()
        
        pending = session.query(Announcement).filter(
            Announcement.pdf_url.isnot(None),
            Announcement.pdf_url != '',
            Announcement.processed == 0
        ).count()
        
        # Count only financial report PDFs pending
        all_pending = session.query(Announcement).filter(
            Announcement.pdf_url.isnot(None),
            Announcement.pdf_url != '',
            Announcement.processed == 0
        ).all()
        financial_pending = sum(1 for a in all_pending if _is_financial_report(a.headline))
        
        return {
            'total_with_pdf': total_with_pdf,
            'extracted': extracted,
            'failed': failed,
            'pending_total': pending,
            'pending_financial': financial_pending
        }


if __name__ == "__main__":
    print("=" * 60)
    print("📄 PSX Financial Report PDF Extractor")
    print("=" * 60)
    
    # Show current stats
    stats = get_extraction_stats()
    print(f"\nCurrent stats:")
    print(f"  Total PDFs in DB:     {stats['total_with_pdf']}")
    print(f"  Already extracted:    {stats['extracted']}")
    print(f"  Failed (scanned):     {stats['failed']}")
    print(f"  Pending (financial):  {stats['pending_financial']}")
    print(f"  Pending (all):        {stats['pending_total']}")
    
    # Process
    print(f"\nProcessing up to 30 financial report PDFs...")
    result = process_unprocessed_reports(batch_size=30, overall_timeout=300)
    
    print(f"\nResults:")
    print(f"  Processed: {result.get('processed', 0)}")
    print(f"  Success:   {result.get('success', 0)}")
    print(f"  Failed:    {result.get('failed', 0)}")
