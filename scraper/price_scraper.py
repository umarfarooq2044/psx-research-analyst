"""
PSX Research Analyst - Price Scraper
Fetches price and volume data for all tickers from PSX
"""
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from tqdm import tqdm
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    PSX_BASE_URL, TIMESERIES_URL_TEMPLATE,
    REQUEST_DELAY, REQUEST_TIMEOUT, MAX_RETRIES
)
from database.db_manager import db


def fetch_intraday_data(symbol: str) -> Optional[Dict]:
    """
    Fetch intraday price/volume data for a single ticker
    Returns dict with price stats or None on error
    """
    url = TIMESERIES_URL_TEMPLATE.format(ticker=symbol)
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 1 and data.get('data'):
                return parse_intraday_data(symbol, data['data'])
            else:
                return None
                
        except requests.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(REQUEST_DELAY * 2)
            else:
                print(f"Failed to fetch {symbol} after {MAX_RETRIES} attempts: {e}")
                return None
        except Exception as e:
            print(f"Error parsing {symbol}: {e}")
            return None
    
    return None


def parse_intraday_data(symbol: str, data: List) -> Dict:
    """
    Parse intraday data array into price statistics
    Data format: [[timestamp, price, volume], ...]
    """
    if not data:
        return None
    
    # Extract all prices and volumes
    prices = [item[1] for item in data if len(item) >= 2 and item[1] is not None]
    volumes = [item[2] for item in data if len(item) >= 3 and item[2] is not None]
    
    if not prices:
        return None
    
    # Calculate statistics
    result = {
        'symbol': symbol,
        'close_price': prices[0],  # Most recent price (data is in reverse chronological order)
        'open_price': prices[-1] if prices else prices[0],  # First trade price
        'high_price': max(prices),
        'low_price': min(prices),
        'volume': sum(volumes) if volumes else 0,
        'trade_count': len(data),
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    return result


def fetch_all_prices(symbols: List[str], show_progress: bool = True) -> List[Dict]:
    """
    Fetch prices for all given symbols
    
    Args:
        symbols: List of ticker symbols
        show_progress: Show progress bar
    
    Returns:
        List of price data dictionaries
    """
    results = []
    today = datetime.now().strftime('%Y-%m-%d')
    
    iterator = tqdm(symbols, desc="Fetching prices") if show_progress else symbols
    
    for symbol in iterator:
        price_data = fetch_intraday_data(symbol)
        
        if price_data:
            results.append(price_data)
            
            # Save to database
            db.insert_price(
                symbol=symbol,
                date=today,
                open_price=price_data.get('open_price'),
                high_price=price_data.get('high_price'),
                low_price=price_data.get('low_price'),
                close_price=price_data.get('close_price'),
                volume=price_data.get('volume')
            )
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    print(f"Successfully fetched prices for {len(results)}/{len(symbols)} tickers")
    return results


def get_price_summary(symbol: str) -> Optional[Dict]:
    """
    Get a comprehensive price summary for a ticker including 52-week data
    """
    # Get latest price
    latest = db.get_latest_price(symbol)
    if not latest:
        return None
    
    # Get 52-week high/low
    high_52w, low_52w = db.get_52_week_high_low(symbol)
    
    # Get historical prices for calculations
    history = db.get_price_history(symbol, days=30)
    
    # Calculate average volume (20 days)
    volumes = [h['volume'] for h in history[:20] if h.get('volume')]
    avg_volume = sum(volumes) / len(volumes) if volumes else 0
    
    return {
        'symbol': symbol,
        'close_price': latest.get('close_price'),
        'volume': latest.get('volume'),
        'high_today': latest.get('high_price'),
        'low_today': latest.get('low_price'),
        'high_52w': high_52w,
        'low_52w': low_52w,
        'avg_volume_20d': avg_volume,
        'price_history': history
    }


def calculate_price_change(symbol: str) -> Tuple[float, float]:
    """
    Calculate daily price change and percentage
    Returns (change, change_percent) or (0, 0) if not enough data
    """
    history = db.get_price_history(symbol, days=2)
    
    if len(history) < 2:
        return 0, 0
    
    today_close = history[0].get('close_price', 0)
    yesterday_close = history[1].get('close_price', 0)
    
    if not yesterday_close:
        return 0, 0
    
    change = today_close - yesterday_close
    change_percent = (change / yesterday_close) * 100
    
    return change, change_percent


if __name__ == "__main__":
    # Test with a few sample tickers
    test_symbols = ["MARI", "OGDC", "HBL", "LUCK", "ENGRO"]
    
    print("Testing price scraper...")
    results = fetch_all_prices(test_symbols, show_progress=True)
    
    for result in results:
        print(f"\n{result['symbol']}:")
        print(f"  Close: Rs. {result['close_price']:.2f}")
        print(f"  High: Rs. {result['high_price']:.2f}")
        print(f"  Low: Rs. {result['low_price']:.2f}")
        print(f"  Volume: {result['volume']:,}")
