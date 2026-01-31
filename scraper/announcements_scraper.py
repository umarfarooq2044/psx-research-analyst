"""
PSX Research Analyst - Announcements Scraper
Scrapes company announcements from PSX company pages
"""
import requests
from bs4 import BeautifulSoup
import re
import time
from datetime import datetime
from typing import List, Dict, Optional
from tqdm import tqdm
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PSX_BASE_URL, COMPANY_URL_TEMPLATE,
    REQUEST_DELAY, REQUEST_TIMEOUT, MAX_RETRIES
)
from database.db_manager import db


def fetch_company_page(symbol: str) -> Optional[str]:
    """
    Fetch the HTML content of a company page
    """
    url = COMPANY_URL_TEMPLATE.format(ticker=symbol)
    
    for attempt in range(MAX_RETRIES):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response.text
            
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_DELAY * 2)
            else:
                print(f"Failed to fetch company page for {symbol}: {e}")
                return None
    
    return None


def parse_announcements(symbol: str, html: str) -> List[Dict]:
    """
    Parse announcements from company page HTML
    """
    soup = BeautifulSoup(html, 'lxml')
    announcements = []
    
    # Find announcement section
    # PSX pages typically have announcement links with PDF downloads
    
    # Look for PDF links (these are announcements)
    pdf_links = soup.find_all('a', href=re.compile(r'/download/document/\d+\.pdf'))
    
    for link in pdf_links:
        pdf_url = link.get('href', '')
        if not pdf_url.startswith('http'):
            pdf_url = PSX_BASE_URL + pdf_url
        
        # Try to find associated text/headline
        # Usually in parent or sibling elements
        parent = link.find_parent(['tr', 'div', 'li'])
        headline = ""
        announcement_date = None
        
        if parent:
            # Get all text content
            text_content = parent.get_text(strip=True, separator=' ')
            # Clean up the headline
            headline = text_content.replace('View', '').replace('PDF', '').strip()
            
            # Try to extract date if present
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text_content)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    # Try different date formats
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y']:
                        try:
                            announcement_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                            break
                        except ValueError:
                            continue
                except:
                    pass
        
        if not headline:
            # Extract document ID from URL as fallback
            doc_id_match = re.search(r'/(\d+)\.pdf', pdf_url)
            headline = f"Announcement #{doc_id_match.group(1)}" if doc_id_match else "Announcement"
        
        # Determine announcement type
        announcement_type = categorize_announcement(headline.lower())
        
        announcements.append({
            'symbol': symbol,
            'headline': headline[:500],  # Limit headline length
            'pdf_url': pdf_url,
            'announcement_type': announcement_type,
            'announcement_date': announcement_date or datetime.now().strftime('%Y-%m-%d')
        })
    
    # Also look for text announcements (View links with JavaScript)
    view_links = soup.find_all('a', href=re.compile(r'javascript:'))
    for link in view_links:
        if link.get_text(strip=True) == 'View':
            parent = link.find_parent(['tr', 'div', 'li'])
            if parent:
                text_content = parent.get_text(strip=True, separator=' ')
                headline = text_content.replace('View', '').replace('PDF', '').strip()
                
                if headline and len(headline) > 5:
                    announcement_type = categorize_announcement(headline.lower())
                    announcements.append({
                        'symbol': symbol,
                        'headline': headline[:500],
                        'pdf_url': None,
                        'announcement_type': announcement_type,
                        'announcement_date': datetime.now().strftime('%Y-%m-%d')
                    })
    
    return announcements


def categorize_announcement(headline_lower: str) -> str:
    """
    Categorize announcement based on keywords in headline
    """
    if any(kw in headline_lower for kw in ['dividend', 'bonus', 'payout']):
        return 'dividend'
    elif any(kw in headline_lower for kw in ['financial', 'result', 'quarterly', 'annual', 'half year']):
        return 'financial_results'
    elif any(kw in headline_lower for kw in ['agm', 'meeting', 'eogm']):
        return 'meeting'
    elif any(kw in headline_lower for kw in ['director', 'board', 'appointment']):
        return 'board_change'
    elif any(kw in headline_lower for kw in ['material', 'merger', 'acquisition', 'contract']):
        return 'material_info'
    else:
        return 'general'


def scrape_announcements_for_ticker(symbol: str) -> int:
    """
    Scrape and save announcements for a single ticker
    Returns number of new announcements found
    """
    html = fetch_company_page(symbol)
    if not html:
        return 0
    
    announcements = parse_announcements(symbol, html)
    new_count = 0
    
    for ann in announcements:
        # insert_announcement returns True if new, False if duplicate
        is_new = db.insert_announcement(
            symbol=ann['symbol'],
            headline=ann['headline'],
            pdf_url=ann.get('pdf_url'),
            announcement_type=ann.get('announcement_type'),
            announcement_date=ann.get('announcement_date')
        )
        if is_new:
            new_count += 1
    
    return new_count


def scrape_all_announcements(symbols: List[str], show_progress: bool = True) -> Dict:
    """
    Scrape announcements for all given symbols
    
    Returns:
        Dict with total and new announcement counts
    """
    total_new = 0
    total_processed = 0
    
    iterator = tqdm(symbols, desc="Scraping announcements") if show_progress else symbols
    
    for symbol in iterator:
        new_count = scrape_announcements_for_ticker(symbol)
        total_new += new_count
        total_processed += 1
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    print(f"Processed {total_processed} tickers, found {total_new} new announcements")
    return {
        'processed': total_processed,
        'new_announcements': total_new
    }


def get_recent_announcements_summary(days: int = 7) -> List[Dict]:
    """
    Get summary of recent announcements with company names
    """
    announcements = db.get_recent_announcements(days=days)
    
    # Group by symbol
    by_symbol = {}
    for ann in announcements:
        symbol = ann['symbol']
        if symbol not in by_symbol:
            ticker = db.get_ticker(symbol)
            by_symbol[symbol] = {
                'symbol': symbol,
                'name': ticker['name'] if ticker else symbol,
                'announcements': []
            }
        by_symbol[symbol]['announcements'].append(ann)
    
    return list(by_symbol.values())


if __name__ == "__main__":
    # Test with sample tickers
    test_symbols = ["MARI", "OGDC", "HBL"]
    
    print("Testing announcements scraper...")
    result = scrape_all_announcements(test_symbols, show_progress=True)
    
    print(f"\nResults: {result}")
    
    # Show recent announcements
    print("\nRecent announcements:")
    for ann in db.get_recent_announcements(days=30)[:10]:
        print(f"  [{ann['symbol']}] {ann['headline'][:60]}...")
