"""
PSX Research Analyst - Oil Prices Scraper
Fetches WTI and Brent crude oil prices
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT


def fetch_oil_prices() -> Optional[Dict]:
    """
    Fetch current WTI and Brent crude oil prices
    Scrapes from public sources
    """
    try:
        # Using Yahoo Finance for oil prices
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        result = {
            'wti_oil': None,
            'wti_change': None,
            'brent_oil': None,
            'brent_change': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Fetch WTI (CL=F)
        wti_data = _fetch_yahoo_quote('CL=F')
        if wti_data:
            result['wti_oil'] = wti_data.get('price')
            result['wti_change'] = wti_data.get('change_percent')
        
        # Fetch Brent (BZ=F)
        brent_data = _fetch_yahoo_quote('BZ=F')
        if brent_data:
            result['brent_oil'] = brent_data.get('price')
            result['brent_change'] = brent_data.get('change_percent')
        
        return result
        
    except Exception as e:
        print(f"Error fetching oil prices: {e}")
        return None


def _fetch_yahoo_quote(symbol: str) -> Optional[Dict]:
    """
    Fetch a quote from Yahoo Finance
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
        
        # Try to find price in the page
        price_elem = soup.find('fin-streamer', {'data-field': 'regularMarketPrice'})
        change_elem = soup.find('fin-streamer', {'data-field': 'regularMarketChangePercent'})
        
        if price_elem:
            price_text = price_elem.get('data-value') or price_elem.text
            try:
                price = float(price_text.replace(',', ''))
            except:
                price = None
        else:
            price = None
        
        if change_elem:
            change_text = change_elem.get('data-value') or change_elem.text
            try:
                change = float(change_text.replace('%', '').replace(',', ''))
            except:
                change = None
        else:
            change = None
        
        return {
            'price': price,
            'change_percent': change
        }
        
    except Exception as e:
        print(f"Error fetching {symbol}: {e}")
        return None


def get_oil_summary() -> Dict:
    """
    Get oil price summary for market reports
    """
    oil_data = fetch_oil_prices()
    
    if oil_data and oil_data.get('wti_oil'):
        wti_change = oil_data.get('wti_change', 0) or 0
        
        if wti_change > 2:
            impact = 'positive for energy stocks'
            trend = 'rising'
        elif wti_change < -2:
            impact = 'negative for energy stocks'
            trend = 'falling'
        else:
            impact = 'neutral'
            trend = 'stable'
        
        return {
            'wti_oil': oil_data.get('wti_oil'),
            'wti_change': wti_change,
            'brent_oil': oil_data.get('brent_oil'),
            'brent_change': oil_data.get('brent_change'),
            'trend': trend,
            'impact': impact
        }
    
    return {
        'wti_oil': None,
        'brent_oil': None,
        'trend': 'unknown',
        'impact': 'unknown'
    }


if __name__ == "__main__":
    print("Testing Oil Prices Scraper...")
    
    result = fetch_oil_prices()
    
    if result:
        print(f"\nWTI Crude: ${result.get('wti_oil', 'N/A')}")
        print(f"WTI Change: {result.get('wti_change', 'N/A')}%")
        print(f"\nBrent Crude: ${result.get('brent_oil', 'N/A')}")
        print(f"Brent Change: {result.get('brent_change', 'N/A')}%")
        print(f"\nTimestamp: {result.get('timestamp')}")
    else:
        print("Failed to fetch oil prices")
    
    print("\nOil Summary:")
    summary = get_oil_summary()
    print(f"  Trend: {summary.get('trend')}")
    print(f"  Impact: {summary.get('impact')}")
