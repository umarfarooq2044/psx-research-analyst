"""Test PDF download and extraction"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper.pdf_analyzer import download_pdf, extract_text_from_pdf, parse_financial_metrics, analyze_company_reports
from database.models import get_connection

print("Testing PDF Analysis System")
print("="*60)

# Get a financial results PDF 
conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT symbol, headline, pdf_url 
    FROM announcements 
    WHERE pdf_url IS NOT NULL 
    AND (headline LIKE '%Financial Result%' OR headline LIKE '%Quarterly%' OR headline LIKE '%Annual%')
    LIMIT 3
""")
rows = cur.fetchall()
conn.close()

print(f"Found {len(rows)} financial report PDFs to test\n")

for symbol, headline, pdf_url in rows:
    print(f"Testing: {symbol}")
    print(f"  Headline: {headline[:60]}...")
    print(f"  URL: {pdf_url[:50]}...")
    
    # Download
    print("  Downloading...", end=" ")
    filepath = download_pdf(pdf_url, symbol)
    if filepath:
        print(f"OK - {os.path.basename(filepath)}")
        
        # Extract text
        print("  Extracting text...", end=" ")
        text = extract_text_from_pdf(filepath)
        print(f"OK - {len(text)} characters")
        
        # Parse metrics
        print("  Parsing financial metrics...")
        metrics = parse_financial_metrics(text)
        
        # Show found metrics
        found_metrics = {k: v for k, v in metrics.items() if v is not None}
        if found_metrics:
            print(f"  Found metrics:")
            for k, v in found_metrics.items():
                print(f"    - {k}: {v}")
        else:
            print("  No metrics extracted (may need pattern tuning)")
        
        # Show text preview
        print(f"\n  Text preview (first 500 chars):")
        print(f"  {text[:500]}...")
    else:
        print("FAILED")
    
    print()
    print("-"*60)
