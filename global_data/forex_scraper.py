"""
PSX Research Analyst - Forex Scraper
Fetches USD/PKR exchange rate and other currency data
"""
import requests
from datetime import datetime
from typing import Dict, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT
from database.db_manager import db


def fetch_usd_pkr() -> Optional[Dict]:
    """
    Fetch current USD/PKR exchange rate using free API
    Returns dict with rate and change data
    """
    try:
        # Using exchangerate-api.com (free tier)
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('result') == 'success':
            rates = data.get('rates', {})
            pkr_rate = rates.get('PKR')
            
            if pkr_rate:
                return {
                    'usd_pkr': pkr_rate,
                    'usd_pkr_change': 0,  # Will be calculated from previous day
                    'timestamp': datetime.now().isoformat(),
                    'source': 'exchangerate-api'
                }
        
        return None
        
    except requests.RequestException as e:
        print(f"Error fetching USD/PKR rate: {e}")
        return None
    except Exception as e:
        print(f"Error parsing forex data: {e}")
        return None


def fetch_multiple_currencies() -> Dict:
    """
    Fetch multiple currency rates against PKR
    Returns dict with various currency pairs
    """
    try:
        url = "https://open.er-api.com/v6/latest/USD"
        response = requests.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('result') == 'success':
            rates = data.get('rates', {})
            
            # Calculate PKR base rates
            pkr_rate = rates.get('PKR', 1)
            
            return {
                'usd_pkr': pkr_rate,
                'eur_pkr': (rates.get('PKR', 0) / rates.get('EUR', 1)) if rates.get('EUR') else None,
                'gbp_pkr': (rates.get('PKR', 0) / rates.get('GBP', 1)) if rates.get('GBP') else None,
                'aed_pkr': (rates.get('PKR', 0) / rates.get('AED', 1)) if rates.get('AED') else None,
                'sar_pkr': (rates.get('PKR', 0) / rates.get('SAR', 1)) if rates.get('SAR') else None,
                'cny_pkr': (rates.get('PKR', 0) / rates.get('CNY', 1)) if rates.get('CNY') else None,
                'timestamp': datetime.now().isoformat()
            }
        
        return {}
        
    except Exception as e:
        print(f"Error fetching currency rates: {e}")
        return {}


def get_forex_summary() -> Dict:
    """
    Get forex summary for market reports
    """
    forex_data = fetch_usd_pkr()
    
    if forex_data:
        return {
            'usd_pkr': forex_data.get('usd_pkr'),
            'trend': 'stable',  # Will be enhanced with historical comparison
            'impact': 'neutral'
        }
    
    return {
        'usd_pkr': None,
        'trend': 'unknown',
        'impact': 'unknown'
    }


if __name__ == "__main__":
    print("Testing Forex Scraper...")
    
    result = fetch_usd_pkr()
    if result:
        print(f"\nUSD/PKR Rate: {result['usd_pkr']:.2f}")
        print(f"Timestamp: {result['timestamp']}")
    else:
        print("Failed to fetch USD/PKR rate")
    
    print("\nFetching multiple currencies...")
    currencies = fetch_multiple_currencies()
    for pair, rate in currencies.items():
        if rate and pair != 'timestamp':
            print(f"  {pair.upper()}: {rate:.2f}")
