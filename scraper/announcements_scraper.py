"""
PSX Research Analyst - High-Performance Announcements Scraper (AsyncIO)
Scrapes company announcements from PSX company pages concurrently.
"""
import aiohttp
import asyncio
import nest_asyncio
from bs4 import BeautifulSoup
import re
from datetime import datetime
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PSX_BASE_URL, COMPANY_URL_TEMPLATE,
    REQUEST_TIMEOUT, MAX_RETRIES
)
from database.db_manager import db

async def fetch_company_page_async(session: aiohttp.ClientSession, symbol: str) -> Optional[str]:
    """
    Fetch the HTML content of a company page asynchronously
    """
    url = COMPANY_URL_TEMPLATE.format(ticker=symbol)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(url, headers=headers, timeout=REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:
                    await asyncio.sleep(2 * (attempt + 1))
                else:
                    return None
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                await asyncio.sleep(1)
            else:
                return None
    return None

def parse_announcements(symbol: str, html: str) -> List[Dict]:
    """
    Parse announcements from company page HTML (CPU bound, remains synchronous)
    """
    soup = BeautifulSoup(html, 'lxml')
    announcements = []
    
    # PDF links
    pdf_links = soup.find_all('a', href=re.compile(r'/download/document/\d+\.pdf'))
    for link in pdf_links:
        pdf_url = link.get('href', '')
        if not pdf_url.startswith('http'):
            pdf_url = PSX_BASE_URL + pdf_url
        
        parent = link.find_parent(['tr', 'div', 'li'])
        headline = ""
        announcement_date = None
        
        if parent:
            text_content = parent.get_text(strip=True, separator=' ')
            headline = text_content.replace('View', '').replace('PDF', '').strip()
            date_match = re.search(r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})', text_content)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    for fmt in ['%d-%m-%Y', '%d/%m/%Y', '%d-%m-%y', '%d/%m/%y']:
                        try:
                            announcement_date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                            break
                        except ValueError: continue
                except: pass
        
        if not headline:
            doc_id_match = re.search(r'/(\d+)\.pdf', pdf_url)
            headline = f"Announcement #{doc_id_match.group(1)}" if doc_id_match else "Announcement"
        
        announcements.append({
            'symbol': symbol,
            'headline': headline[:500],
            'pdf_url': pdf_url,
            'announcement_type': categorize_announcement(headline.lower()),
            'announcement_date': announcement_date or datetime.now().strftime('%Y-%m-%d')
        })
    
    # Text links
    view_links = soup.find_all('a', href=re.compile(r'javascript:'))
    for link in view_links:
        if link.get_text(strip=True) == 'View':
            parent = link.find_parent(['tr', 'div', 'li'])
            if parent:
                text_content = parent.get_text(strip=True, separator=' ')
                headline = text_content.replace('View', '').replace('PDF', '').strip()
                if headline and len(headline) > 5:
                    announcements.append({
                        'symbol': symbol,
                        'headline': headline[:500],
                        'pdf_url': None,
                        'announcement_type': categorize_announcement(headline.lower()),
                        'announcement_date': datetime.now().strftime('%Y-%m-%d')
                    })
    return announcements

def categorize_announcement(headline_lower: str) -> str:
    """Categorize announcement based on keywords"""
    if any(kw in headline_lower for kw in ['dividend', 'bonus', 'payout']): return 'dividend'
    if any(kw in headline_lower for kw in ['financial', 'result', 'quarterly', 'annual', 'half year']): return 'financial_results'
    if any(kw in headline_lower for kw in ['agm', 'meeting', 'eogm']): return 'meeting'
    if any(kw in headline_lower for kw in ['director', 'board', 'appointment']): return 'board_change'
    if any(kw in headline_lower for kw in ['material', 'merger', 'acquisition', 'contract']): return 'material_info'
    return 'general'

async def process_ticker_announcements(session: aiohttp.ClientSession, symbol: str, semaphore: asyncio.Semaphore) -> int:
    """Process a single ticker asynchronously"""
    async with semaphore:
        html = await fetch_company_page_async(session, symbol)
        if not html:
            return 0
        
        announcements = parse_announcements(symbol, html)
        new_count = 0
        for ann in announcements:
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

async def scrape_all_announcements_async(symbols: List[str], concurrency: int = 10, show_progress: bool = True) -> Dict:
    """
    Scrape announcements for all symbols concurrently.
    """
    semaphore = asyncio.Semaphore(concurrency)
    async with aiohttp.ClientSession() as session:
        tasks = [process_ticker_announcements(session, symbol, semaphore) for symbol in symbols]
        
        if show_progress:
            results = await tqdm.gather(*tasks, desc="Scraping announcements")
        else:
            results = await asyncio.gather(*tasks)
            
    total_new = sum(results)
    print(f"✅ Processed {len(symbols)} tickers, found {total_new} new announcements")
    return {
        'processed': len(symbols),
        'new_announcements': total_new
    }

def scrape_all_announcements(symbols: List[str], show_progress: bool = True, smart_mode: bool = True) -> Dict:
    """
    Synchronous wrapper for orchestrator.
    
    Args:
        symbols: List of ticker symbols to scrape
        show_progress: Show progress bar
        smart_mode: If True, prioritize active companies (reduces scraping by ~50%)
    """
    if smart_mode and len(symbols) > 150:
        import random
        # Priority list: first 100 symbols (typically sorted by market cap / KSE-100)
        priority_symbols = symbols[:100]
        # Sample 50 from the rest
        remaining = symbols[100:]
        sample_size = min(50, len(remaining))
        sampled = random.sample(remaining, sample_size) if remaining else []
        
        symbols_to_scrape = priority_symbols + sampled
        print(f"🎯 [Smart Mode] Scraping announcements for {len(symbols_to_scrape)} priority companies (skipping {len(symbols) - len(symbols_to_scrape)})")
    else:
        symbols_to_scrape = symbols
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            nest_asyncio.apply()
            task = loop.create_task(scrape_all_announcements_async(symbols_to_scrape, show_progress=show_progress))
            return loop.run_until_complete(task)
        else:
            task = loop.create_task(scrape_all_announcements_async(symbols_to_scrape, show_progress=show_progress))
            return loop.run_until_complete(task)
    except Exception:
        return asyncio.run(scrape_all_announcements_async(symbols_to_scrape, show_progress=show_progress))

def scrape_all_announcements_full(symbols: List[str], show_progress: bool = True) -> Dict:
    """Force scrape ALL announcements (no smart filtering)"""
    return scrape_all_announcements(symbols, show_progress=show_progress, smart_mode=False)

if __name__ == "__main__":
    test_symbols = ["MARI", "OGDC", "HBL", "ENGRO", "LUCK"]
    print(f"Testing async announcements scraper for {len(test_symbols)} tickers...")
    asyncio.run(scrape_all_announcements_async(test_symbols))
