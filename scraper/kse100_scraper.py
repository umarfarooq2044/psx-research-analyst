"""
PSX Research Analyst - KSE-100 Index Scraper
Fetches KSE-100 index data and market summary from PSX
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, Optional
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import PSX_BASE_URL, REQUEST_TIMEOUT
from database.db_manager import db


def fetch_kse100_data() -> Optional[Dict]:
    """
    Fetch KSE-100 index data from PSX
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Try PSX market watch page
        url = f"{PSX_BASE_URL}/market-watch"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        result = {
            'open_value': None,
            'high_value': None,
            'low_value': None,
            'close_value': None,
            'change_value': None,
            'change_percent': None,
            'volume': None,
            'value_traded': None,
            'advancing': None,
            'declining': None,
            'unchanged': None,
            'timestamp': datetime.now().isoformat()
        }
        
        # Parse index data from page
        # Note: Actual parsing depends on PSX page structure
        # This is a template that may need adjustment
        
        # Try to find KSE-100 data
        index_tables = soup.find_all('table')
        for table in index_tables:
            text = table.get_text()
            if 'KSE-100' in text or 'KSE100' in text:
                # Extract numbers from the table
                numbers = re.findall(r'[\d,]+\.?\d*', text)
                if len(numbers) >= 3:
                    try:
                        result['close_value'] = float(numbers[0].replace(',', ''))
                        result['change_value'] = float(numbers[1].replace(',', ''))
                        result['change_percent'] = float(numbers[2].replace(',', ''))
                    except:
                        pass
        
        # Try alternate method - look for specific elements
        kse_elem = soup.find(string=re.compile(r'KSE[\s-]?100', re.I))
        if kse_elem:
            parent = kse_elem.find_parent(['tr', 'div'])
            if parent:
                numbers = re.findall(r'[\d,]+\.?\d*', parent.get_text())
                if numbers:
                    try:
                        result['close_value'] = float(numbers[0].replace(',', ''))
                    except:
                        pass
        
        return result
        
    except Exception as e:
        print(f"Error fetching KSE-100: {e}")
        return None


def fetch_market_breadth() -> Dict:
    """
    Fetch market breadth (advancing/declining/unchanged)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        url = f"{PSX_BASE_URL}/market-watch"
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return {}
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look for advancing/declining data
        text = soup.get_text()
        
        result = {
            'advancing': None,
            'declining': None,
            'unchanged': None
        }
        
        # Try to extract breadth data
        adv_match = re.search(r'advanc\w*[:\s]+(\d+)', text, re.I)
        dec_match = re.search(r'declin\w*[:\s]+(\d+)', text, re.I)
        unc_match = re.search(r'unchang\w*[:\s]+(\d+)', text, re.I)
        
        if adv_match:
            result['advancing'] = int(adv_match.group(1))
        if dec_match:
            result['declining'] = int(dec_match.group(1))
        if unc_match:
            result['unchanged'] = int(unc_match.group(1))
        
        return result
        
    except Exception as e:
        print(f"Error fetching market breadth: {e}")
        return {}


def get_kse100_summary() -> Dict:
    """
    Get comprehensive KSE-100 summary for reports
    """
    kse_data = fetch_kse100_data() or {}
    breadth = fetch_market_breadth()
    
    # Combine data
    kse_data.update(breadth)
    
    # Determine market sentiment based on change
    change_pct = kse_data.get('change_percent', 0) or 0
    
    if change_pct > 1:
        sentiment = 'bullish'
        bias = 'strong upward momentum'
    elif change_pct > 0:
        sentiment = 'slightly bullish'
        bias = 'mild upward movement'
    elif change_pct < -1:
        sentiment = 'bearish'
        bias = 'strong downward pressure'
    elif change_pct < 0:
        sentiment = 'slightly bearish'
        bias = 'mild downward movement'
    else:
        sentiment = 'neutral'
        bias = 'flat trading'
    
    kse_data['sentiment'] = sentiment
    kse_data['bias'] = bias
    
    # Calculate breadth ratio if available
    adv = kse_data.get('advancing', 0) or 0
    dec = kse_data.get('declining', 0) or 0
    
    if adv + dec > 0:
        kse_data['breadth_ratio'] = adv / (adv + dec)
        kse_data['breadth_sentiment'] = 'positive' if kse_data['breadth_ratio'] > 0.5 else 'negative'
    else:
        kse_data['breadth_ratio'] = None
        kse_data['breadth_sentiment'] = 'unknown'
    
    return kse_data


def save_kse100_data():
    """
    Fetch and save KSE-100 data to database
    """
    data = get_kse100_summary()
    
    if data and data.get('close_value'):
        db.save_kse100_index(data)
        return data
    
    return None


def get_kse100_support_resistance() -> Dict:
    """
    Calculate support and resistance levels for KSE-100
    Based on historical data
    """
    history = db.get_kse100_history(days=30)
    
    if not history or len(history) < 5:
        return {
            'support_1': None,
            'support_2': None,
            'resistance_1': None,
            'resistance_2': None
        }
    
    # Get high/low values
    highs = [h['high_value'] for h in history if h.get('high_value')]
    lows = [h['low_value'] for h in history if h.get('low_value')]
    closes = [h['close_value'] for h in history if h.get('close_value')]
    
    if not closes:
        return {}
    
    current = closes[0] if closes else 0
    
    # Calculate levels
    recent_high = max(highs[:5]) if highs else current
    recent_low = min(lows[:5]) if lows else current
    
    # Support levels
    support_1 = recent_low
    support_2 = min(lows[:10]) if len(lows) >= 10 else support_1 * 0.98
    
    # Resistance levels
    resistance_1 = recent_high
    resistance_2 = max(highs[:10]) if len(highs) >= 10 else resistance_1 * 1.02
    
    return {
        'current': current,
        'support_1': round(support_1, 0),
        'support_2': round(support_2, 0),
        'resistance_1': round(resistance_1, 0),
        'resistance_2': round(resistance_2, 0),
        '52_week_high': max(highs) if highs else None,
        '52_week_low': min(lows) if lows else None
    }


if __name__ == "__main__":
    print("Testing KSE-100 Scraper...")
    
    summary = get_kse100_summary()
    
    print(f"\nKSE-100 Index:")
    print(f"  Close: {summary.get('close_value')}")
    print(f"  Change: {summary.get('change_value')} ({summary.get('change_percent')}%)")
    print(f"  Sentiment: {summary.get('sentiment')}")
    print(f"  Bias: {summary.get('bias')}")
    
    print(f"\nMarket Breadth:")
    print(f"  Advancing: {summary.get('advancing')}")
    print(f"  Declining: {summary.get('declining')}")
    print(f"  Unchanged: {summary.get('unchanged')}")
    print(f"  Breadth Sentiment: {summary.get('breadth_sentiment')}")
