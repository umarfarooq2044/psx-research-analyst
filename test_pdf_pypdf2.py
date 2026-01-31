"""
Simple test to verify PyPDF2 PDF reading works
"""
import requests
from io import BytesIO
from PyPDF2 import PdfReader
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from database.models import get_connection
from config import PSX_BASE_URL

# Force stdout to flush immediately
sys.stdout.reconfigure(line_buffering=True)

print("Starting PDF test...")
print("="*50)

# Get a PDF URL from database
conn = get_connection()
cur = conn.cursor()
cur.execute("""
    SELECT pdf_url, headline, symbol FROM announcements
    WHERE pdf_url IS NOT NULL AND pdf_url != ''
    LIMIT 1
""")
row = cur.fetchone()
conn.close()

if not row:
    print("No PDF URLs found in database!")
    sys.exit(1)

pdf_url, headline, symbol = row
print(f"Symbol: {symbol}")
print(f"Headline: {headline[:60]}...")
print(f"PDF URL: {pdf_url}")
print()

# Ensure full URL
if not pdf_url.startswith('http'):
    full_url = PSX_BASE_URL + pdf_url
else:
    full_url = pdf_url

print(f"Full URL: {full_url}")
print()

# Try to fetch the PDF
print("Fetching PDF...")
try:
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    response = requests.get(full_url, headers=headers, timeout=30)
    response.raise_for_status()
    print(f"Downloaded: {len(response.content)} bytes")
except Exception as e:
    print(f"Failed to download: {e}")
    sys.exit(1)

# Try to read the PDF
print()
print("Reading PDF with PyPDF2...")
try:
    pdf_file = BytesIO(response.content)
    reader = PdfReader(pdf_file)
    print(f"Number of pages: {len(reader.pages)}")
    
    # Extract text from first page
    if reader.pages:
        first_page = reader.pages[0]
        text = first_page.extract_text()
        if text:
            print(f"Text length: {len(text)} chars")
            print()
            print("First 500 characters:")
            print("-"*50)
            print(text[:500])
        else:
            print("No text extracted from first page")
except Exception as e:
    print(f"Failed to read PDF: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print()
print("="*50)
print("Test completed successfully!")
