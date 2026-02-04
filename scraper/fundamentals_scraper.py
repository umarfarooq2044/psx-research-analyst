"""
PSX Research Analyst - Fundamentals Scraper
Fetches financial ratios and data from PSX Company Pages (HTML)
"""
import aiohttp
import asyncio
import nest_asyncio
from bs4 import BeautifulSoup
import re
import sys
import os
from typing import List, Dict, Optional
from tqdm.asyncio import tqdm
from datetime import datetime

# Windows Unicode Fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, REQUEST_DELAY
from database.db_manager import db

CONCURRENCY_LIMIT = 10 # Lower limit for HTML scraping to avoid load issues

class FundamentalsScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def fetch_company_page(self, session, symbol):
        url = f"https://dps.psx.com.pk/company/{symbol}"
        try:
            async with self.semaphore:
                async with session.get(url, timeout=REQUEST_TIMEOUT, headers=self.headers) as response:
                    if response.status == 200:
                        html = await response.text()
                        return symbol, html
        except Exception as e:
            # print(f"Error fetching {symbol}: {e}")
            pass
        return symbol, None

    def parse_float(self, text):
        try:
            # Handle brackets for negative: "(15.72)" -> -15.72
            clean = text.replace(',', '').strip()
            if '(' in clean and ')' in clean:
                clean = '-' + clean.replace('(', '').replace(')', '')
            return float(clean)
        except:
            return None

    def parse_fundamentals(self, symbol, html):
        if not html:
            return None
            
        soup = BeautifulSoup(html, 'html.parser')
        data = {
            'eps': None, 'eps_growth': None, 'gross_margin': None, 
            'net_margin': None, 'peg_ratio': None, 'market_cap': None
        }
        
        tables = soup.find_all('table')
        
        # Strategy: Look for specific row headers in ALL tables
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cols = row.find_all(['th', 'td'])
                if len(cols) < 2: continue
                
                header = cols[0].text.strip().lower()
                val_text = cols[1].text.strip() # Latest year/value
                
                if not val_text: continue
                
                if 'eps' == header or 'earnings per share' in header:
                    # Avoid 'EPS Growth' here if strictly matching
                    if 'growth' not in header:
                        data['eps'] = self.parse_float(val_text)
                
                elif 'eps growth' in header:
                    data['eps_growth'] = self.parse_float(val_text)
                    
                elif 'gross profit margin' in header:
                    data['gross_margin'] = self.parse_float(val_text)
                    
                elif 'net profit margin' in header:
                    data['net_margin'] = self.parse_float(val_text)
                    
                elif 'peg' in header:
                    data['peg_ratio'] = self.parse_float(val_text)
                    
                elif 'shares' in header and 'outstanding' in header:
                    # Use shares to calc market cap if price known, else skip
                    pass

        # Calculate P/E if we have EPS and Price
        if data['eps']:
            latest_price = db.get_latest_price(symbol)
            if latest_price and latest_price.get('close_price'):
                price = latest_price['close_price']
                if data['eps'] != 0:
                    data['pe_ratio'] = round(price / data['eps'], 2)
                    
                # Market Cap (Approx if shares not known, can't calculate easily without shares)
                # But sometimes Market Cap is in profile text. Skipping for now.
        
        return data

    async def scrape_all(self, symbols: List[str]):
        print(f"🧬 Scraping fundamentals for {len(symbols)} companies...")
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_company_page(session, s) for s in symbols]
            
            # Use Tqdm
            results = []
            for coro in tqdm.as_completed(tasks, desc="Fetching Pages"):
                symbol, html = await coro
                if html:
                    fund_data = self.parse_fundamentals(symbol, html)
                    if fund_data and (fund_data['eps'] is not None or fund_data['net_margin'] is not None):
                        db.save_fundamentals(symbol, fund_data)
                        results.append(fund_data)
        
        print(f"✅ Saved fundamentals for {len(results)} companies")
        return results

def run_fundamentals_scraper(limit=None, force_all=False):
    """
    Run fundamentals scraper with smart caching.
    Only scrapes symbols that need refresh (stale > 7 days or missing).
    
    Args:
        limit: Optional limit on number of symbols to scrape
        force_all: If True, scrape all symbols regardless of freshness
    """
    scraper = FundamentalsScraper()
    
    if force_all:
        # Legacy mode: scrape all
        tickers = db.get_all_tickers()
        symbols = [t['symbol'] for t in tickers]
        print(f"🧬 [Force Mode] Scraping fundamentals for ALL {len(symbols)} companies...")
    else:
        # Smart mode: only stale/missing symbols
        symbols = db.get_symbols_needing_fundamentals(days_threshold=7)
        print(f"🧬 [Smart Mode] {len(symbols)} companies need fundamental refresh...")
        
        if len(symbols) == 0:
            print("✅ All fundamentals are fresh (< 7 days old). Skipping scrape.")
            return []
    
    if limit:
        symbols = symbols[:limit]
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            nest_asyncio.apply()
            task = loop.create_task(scraper.scrape_all(symbols))
            return loop.run_until_complete(task)
        else:
            task = loop.create_task(scraper.scrape_all(symbols))
            return loop.run_until_complete(task)
    except Exception:
        return asyncio.run(scraper.scrape_all(symbols))

if __name__ == "__main__":
    # Test on a few
    run_fundamentals_scraper(limit=5)
