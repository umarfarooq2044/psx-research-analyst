"""
PSX Research Analyst - Global Indices Scraper
Fetches US and Asian market indices
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional, List
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT
from database.db_manager import db


# Index symbols for Yahoo Finance
GLOBAL_INDICES = {
    'sp500': '^GSPC',
    'nasdaq': '^IXIC',
    'dow': '^DJI',
    'nikkei': '^N225',
    'hang_seng': '^HSI',
    'shanghai': '000001.SS'
}


def fetch_global_indices() -> Dict:
    """
    Fetch all global market indices
    Returns dict with index values and changes
    """
    result = {
        'timestamp': datetime.now().isoformat()
    }
    
    for name, symbol in GLOBAL_INDICES.items():
        data = _fetch_yahoo_index(symbol)
        if data:
            result[name] = data.get('price')
            result[f'{name}_change'] = data.get('change_percent')
        else:
            result[name] = None
            result[f'{name}_change'] = None
    
    return result


def _fetch_yahoo_index(symbol: str) -> Optional[Dict]:
    """
    Fetch an index quote from Yahoo Finance
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        url = f"https://finance.yahoo.com/quote/{symbol}"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to find price
        price_elem = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
        change_elem = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
        
        price = None
        change = None
        
        if price_elem:
            price_text = price_elem.get('data-value') or price_elem.text
            try:
                price = float(price_text.replace(',', ''))
            except:
                pass
        
        if change_elem:
            change_text = change_elem.get('data-value') or change_elem.text
            try:
                change = float(change_text.replace('%', '').replace(',', ''))
            except:
                pass
        
        return {
            'price': price,
            'change_percent': change
        }
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def get_us_markets_summary() -> Dict:
    """
    Get US markets summary for reports
    """
    indices = fetch_global_indices()
    
    sp500_change = indices.get('sp500_change', 0) or 0
    nasdaq_change = indices.get('nasdaq_change', 0) or 0
    dow_change = indices.get('dow_change', 0) or 0
    
    avg_change = (sp500_change + nasdaq_change + dow_change) / 3
    
    if avg_change > 1:
        sentiment = 'positive'
        impact = 'bullish for emerging markets'
    elif avg_change < -1:
        sentiment = 'negative'
        impact = 'bearish for emerging markets'
    else:
        sentiment = 'mixed'
        impact = 'neutral'
    
    return {
        'sp500': indices.get('sp500'),
        'sp500_change': sp500_change,
        'nasdaq': indices.get('nasdaq'),
        'nasdaq_change': nasdaq_change,
        'dow': indices.get('dow'),
        'dow_change': dow_change,
        'sentiment': sentiment,
        'impact': impact
    }


def get_asian_markets_summary() -> Dict:
    """
    Get Asian markets summary for reports
    """
    indices = fetch_global_indices()
    
    nikkei_change = indices.get('nikkei_change', 0) or 0
    hang_seng_change = indices.get('hang_seng_change', 0) or 0
    
    avg_change = (nikkei_change + hang_seng_change) / 2
    
    if avg_change > 1:
        sentiment = 'positive'
    elif avg_change < -1:
        sentiment = 'negative'
    else:
        sentiment = 'mixed'
    
    return {
        'nikkei': indices.get('nikkei'),
        'nikkei_change': nikkei_change,
        'hang_seng': indices.get('hang_seng'),
        'hang_seng_change': hang_seng_change,
        'shanghai': indices.get('shanghai'),
        'shanghai_change': indices.get('shanghai_change'),
        'sentiment': sentiment
    }


def save_global_markets_data():
    """
    Fetch and save global markets data to database
    """
    from global_data.forex_scraper import fetch_usd_pkr
    from global_data.oil_prices import fetch_oil_prices
    
    # Fetch all data
    indices = fetch_global_indices()
    forex = fetch_usd_pkr() or {}
    oil = fetch_oil_prices() or {}
    
    # Combine all data
    global_data = {
        'sp500': indices.get('sp500'),
        'sp500_change': indices.get('sp500_change'),
        'nasdaq': indices.get('nasdaq'),
        'nasdaq_change': indices.get('nasdaq_change'),
        'dow': indices.get('dow'),
        'dow_change': indices.get('dow_change'),
        'nikkei': indices.get('nikkei'),
        'nikkei_change': indices.get('nikkei_change'),
        'hang_seng': indices.get('hang_seng'),
        'hang_seng_change': indices.get('hang_seng_change'),
        'shanghai': indices.get('shanghai'),
        'shanghai_change': indices.get('shanghai_change'),
        'wti_oil': oil.get('wti_oil'),
        'wti_change': oil.get('wti_change'),
        'brent_oil': oil.get('brent_oil'),
        'brent_change': oil.get('brent_change'),
        'usd_pkr': forex.get('usd_pkr'),
        'usd_pkr_change': forex.get('usd_pkr_change'),
        'gold': None,  # Will add gold later
        'gold_change': None
    }
    
    # Save to database
    db.save_global_markets(global_data)
    
    return global_data


if __name__ == "__main__":
    print("Testing Global Indices Scraper...")
    
    print("\n--- US Markets ---")
    us = get_us_markets_summary()
    print(f"S&P 500: {us.get('sp500')} ({us.get('sp500_change')}%)")
    print(f"NASDAQ: {us.get('nasdaq')} ({us.get('nasdaq_change')}%)")
    print(f"DOW: {us.get('dow')} ({us.get('dow_change')}%)")
    print(f"Sentiment: {us.get('sentiment')}")
    print(f"Impact: {us.get('impact')}")
    
    print("\n--- Asian Markets ---")
    asian = get_asian_markets_summary()
    print(f"Nikkei: {asian.get('nikkei')} ({asian.get('nikkei_change')}%)")
    print(f"Hang Seng: {asian.get('hang_seng')} ({asian.get('hang_seng_change')}%)")
    print(f"Shanghai: {asian.get('shanghai')} ({asian.get('shanghai_change')}%)")
    print(f"Sentiment: {asian.get('sentiment')}")
