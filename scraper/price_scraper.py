"""
PSX Research Analyst - High-Performance Price Scraper (AsyncIO)
Fetches price and volume data for all tickers concurrently.
Up to 50x faster than synchronous scraping.
"""
import aiohttp
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from tqdm.asyncio import tqdm
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PSX_BASE_URL, TIMESERIES_URL_TEMPLATE,
    REQUEST_TIMEOUT, MAX_RETRIES
)
from database.db_manager import db

# Concurrency limit to be polite to the server
CONCURRENCY_LIMIT = 20

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

class AsyncPriceScraper:
    """
    Asynchronous price scraper using aiohttp.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    
    async def fetch_intraday_data(self, session: aiohttp.ClientSession, symbol: str) -> Optional[Dict]:
        """Fetch intraday data for a single symbol asynchronously"""
        url = TIMESERIES_URL_TEMPLATE.format(ticker=symbol)
        
        for attempt in range(MAX_RETRIES):
            try:
                async with self.semaphore:  # Limit concurrent requests
                    async with session.get(url, timeout=REQUEST_TIMEOUT, headers=self.headers) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get('status') == 1 and data.get('data'):
                                return self.parse_intraday_data(symbol, data['data'])
                            return None
                        elif response.status == 429:  # Rate limited
                            wait_time = (attempt + 1) * 2
                            print(f"⚠️ Rate limit for {symbol}. Waiting {wait_time}s...")
                            await asyncio.sleep(wait_time)
                        else:
                            return None
            except asyncio.TimeoutError:
                pass
            except Exception as e:
                # print(f"Error fetching {symbol}: {e}")
                pass
            
            # Exponential backoff for retries
            await asyncio.sleep(1 * (attempt + 1))
        
        return None

    def parse_intraday_data(self, symbol: str, data: List) -> Dict:
        """Parse raw API response"""
        if not data:
            return None
        
        # Extract valid prices/volumes
        prices = [item[1] for item in data if len(item) >= 2 and item[1] is not None]
        volumes = [item[2] for item in data if len(item) >= 3 and item[2] is not None]
        
        if not prices:
            return None
            
        result = {
            'symbol': symbol,
            'close_price': prices[0],  # Most recent
            'open_price': prices[-1] if prices else prices[0],
            'high_price': max(prices),
            'low_price': min(prices),
            'volume': sum(volumes) if volumes else 0,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return result

    async def fetch_all_prices_async(self, symbols: List[str]) -> List[Dict]:
        """Fetch all prices concurrently"""
        start_time = time.time()
        print(f"🚀 Starting async scrape for {len(symbols)} tickers...")
        
        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_intraday_data(session, symbol) for symbol in symbols]
            
            # Use tqdm for progress bar
            processed_data = await tqdm.gather(*tasks, desc="Fetching Prices")
            
            # Filter None results
            results = [r for r in processed_data if r is not None]
        
        duration = time.time() - start_time
        print(f"✅ Scraped {len(results)}/{len(symbols)} stocks in {duration:.2f} seconds!")
        
        # Save to DB (Sync operation - do in bulk if possible, but simple loop is fine for DB)
        self.save_results_to_db(results)
        
        return results
    
    def save_results_to_db(self, results: List[Dict]):
        """Save all results to database"""
        today = datetime.now().strftime('%Y-%m-%d')
        print("💾 Saving to database...")
        
        for price_data in results:
            db.insert_price(
                symbol=price_data['symbol'],
                date_str=today,
                open_price=price_data.get('open_price'),
                high_price=price_data.get('high_price'),
                low_price=price_data.get('low_price'),
                close_price=price_data.get('close_price'),
                volume=price_data.get('volume')
            )
        print("✓ Data saved.")

# ============================================================================
# BRIDGE FOR EXISTING CODE
# ============================================================================

def fetch_all_prices(symbols: List[str], show_progress: bool = True) -> List[Dict]:
    """
    Synchronous wrapper for async scraper.
    Replaces the old fetch_all_prices function.
    """
    scraper = AsyncPriceScraper()
    
    # Run async loop
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    return asyncio.run(scraper.fetch_all_prices_async(symbols))

if __name__ == "__main__":
    # Test
    test_symbols = ["MARI", "OGDC", "HBL", "LUCK", "ENGRO", "TRG", "SYS", "AVN"]
    results = fetch_all_prices(test_symbols)
    print(f"Sample: {results[0] if results else 'None'}")
