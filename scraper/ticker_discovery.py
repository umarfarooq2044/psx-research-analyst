"""
PSX Research Analyst - Ticker Discovery
Scrapes the PSX eligible scrips XML to get all active tickers
"""
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ELIGIBLE_SCRIPS_URL, REQUEST_TIMEOUT
from database.db_manager import db


def fetch_eligible_scrips() -> List[Dict]:
    """
    Fetch all eligible scrips from PSX XML endpoint
    Returns list of dicts with 'symbol' and 'name' keys
    """
    print("Fetching eligible scrips from PSX...")
    
    try:
        response = requests.get(ELIGIBLE_SCRIPS_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Parse XML
        root = ET.fromstring(response.content)
        
        tickers = []
        # Navigate to data elements
        for data_elem in root.findall('.//data/data'):
            symbol_code = data_elem.find('symbol_code')
            symbol_name = data_elem.find('symbol_name')
            
            if symbol_code is not None and symbol_name is not None:
                symbol = symbol_code.text.strip() if symbol_code.text else None
                name = symbol_name.text.strip() if symbol_name.text else None
                
                if symbol:
                    tickers.append({
                        'symbol': symbol,
                        'name': name or symbol
                    })
        
        print(f"Found {len(tickers)} tickers")
        return tickers
        
    except requests.RequestException as e:
        print(f"Error fetching eligible scrips: {e}")
        return []
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return []


def filter_equity_tickers(tickers: List[Dict]) -> List[Dict]:
    """
    Filter out non-equity tickers (ETFs, preference shares, rights, etc.)
    These typically have specific suffixes or patterns
    """
    excluded_suffixes = ['ETF', 'PS', 'R', 'R2', 'R3', 'NV', 'CPS', 'NCPS']
    excluded_prefixes = ['GEM']
    
    filtered = []
    for ticker in tickers:
        symbol = ticker['symbol']
        
        # Check for excluded suffixes
        skip = False
        for suffix in excluded_suffixes:
            if symbol.endswith(suffix) and len(symbol) > len(suffix):
                # Make sure it's actually a suffix, not part of the name
                base = symbol[:-len(suffix)]
                if base and (base.isupper() or base[-1].isalpha()):
                    skip = True
                    break
        
        # Check for excluded prefixes
        for prefix in excluded_prefixes:
            if symbol.startswith(prefix):
                skip = True
                break
        
        if not skip:
            filtered.append(ticker)
    
    return filtered


def discover_and_save_tickers(filter_non_equity: bool = False) -> List[Dict]:
    """
    Main function to discover all tickers and save to database
    
    Args:
        filter_non_equity: If True, filter out ETFs, preference shares, etc.
    
    Returns:
        List of ticker dictionaries
    """
    tickers = fetch_eligible_scrips()
    
    if not tickers:
        print("No tickers found, using cached data from database")
        return db.get_all_tickers()
    
    if filter_non_equity:
        original_count = len(tickers)
        tickers = filter_equity_tickers(tickers)
        print(f"Filtered to {len(tickers)} equity tickers (removed {original_count - len(tickers)} non-equity)")
    
    # Save to database
    db.bulk_upsert_tickers(tickers)
    print(f"Saved {len(tickers)} tickers to database")
    
    return tickers


def get_ticker_symbols(filter_non_equity: bool = False) -> List[str]:
    """
    Get just the list of ticker symbols
    """
    tickers = discover_and_save_tickers(filter_non_equity)
    return [t['symbol'] for t in tickers]


if __name__ == "__main__":
    # Test ticker discovery
    tickers = discover_and_save_tickers(filter_non_equity=False)
    print(f"\nTotal tickers: {len(tickers)}")
    print(f"Sample tickers: {[t['symbol'] for t in tickers[:10]]}")
