"""
PSX Research Analyst - Peer & Sector Comparison
Analyzes stock performance relative to sector peers for valuation and strength.
"""
import pandas as pd
import os
import sys
from typing import Dict, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import db
from config import SECTORS

def get_sector_peers(symbol: str) -> List[str]:
    """Get list of peer symbols in the same sector"""
    for sector, stocks in SECTORS.items():
        if symbol in stocks:
            return stocks
    return []

def calculate_sector_averages() -> Dict[str, Dict]:
    """
    Calculate average metrics for each sector
    Returns: { 'Technology': {'avg_pe': 15.2, 'avg_yield': 2.5, ...}, ... }
    """
    sector_stats = {}
    
    all_tickers = db.get_all_tickers()
    ticker_sector_map = {t['symbol']: t.get('sector') for t in all_tickers} # Use DB sector if available
    
    # Fallback to config SECTORS if DB sector is empty
    for s_name, s_stocks in SECTORS.items():
        for stock in s_stocks:
            if stock not in ticker_sector_map or not ticker_sector_map[stock]:
                ticker_sector_map[stock] = s_name

    # Group data
    data_by_sector = {}
    
    for symbol, sector in ticker_sector_map.items():
        if not sector: continue
        
        fund = db.get_latest_fundamentals(symbol)
        if not fund: continue
        
        if sector not in data_by_sector:
            data_by_sector[sector] = {'pe': [], 'yield': [], 'margin': []}
            
        if fund.get('pe_ratio') and fund['pe_ratio'] > 0:
            data_by_sector[sector]['pe'].append(fund['pe_ratio'])
            
        if fund.get('dividend_yield'):
            data_by_sector[sector]['yield'].append(fund['dividend_yield'])
            
        if fund.get('net_margin'):
            data_by_sector[sector]['margin'].append(fund['net_margin'])
    
    # Calculate averages
    for sector, metrics in data_by_sector.items():
        stats = {
            'avg_pe': sum(metrics['pe']) / len(metrics['pe']) if metrics['pe'] else 0,
            'avg_yield': sum(metrics['yield']) / len(metrics['yield']) if metrics['yield'] else 0,
            'avg_margin': sum(metrics['margin']) / len(metrics['margin']) if metrics['margin'] else 0,
            'count': len(metrics['pe']) # Number of stocks with valid P/E
        }
        sector_stats[sector] = stats
        
    return sector_stats

def analyze_peer_comparison(symbol: str) -> Dict:
    """
    Compare a stock to its sector peers
    """
    fund = db.get_latest_fundamentals(symbol)
    if not fund:
        return {'status': 'No fundamental data'}
        
    # Determine sector
    sector = None
    all_tickers = db.get_all_tickers()
    for t in all_tickers:
        if t['symbol'] == symbol:
            sector = t.get('sector')
            break
            
    if not sector:
        # Fallback
        for s_name, s_stocks in SECTORS.items():
            if symbol in s_stocks:
                sector = s_name
                break
    
    if not sector:
        return {'status': 'Sector not found'}
        
    # Get averages (Optimized: In real app, cache this call)
    averages = calculate_sector_averages() 
    sector_avg = averages.get(sector, {})
    
    if not sector_avg.get('count'):
        return {'status': 'Insufficient peer data'}
        
    # Compare
    pe_ratio = fund.get('pe_ratio', 0)
    avg_pe = sector_avg.get('avg_pe', 0)
    
    div_yield = fund.get('dividend_yield', 0)
    avg_yield = sector_avg.get('avg_yield', 0)
    
    comparison = {
        'sector': sector,
        'pe_status': 'Undervalued' if 0 < pe_ratio < avg_pe else 'Overvalued',
        'pe_diff': round(((pe_ratio - avg_pe) / avg_pe) * 100, 1) if avg_pe else 0,
        'yield_status': 'Above Average' if div_yield > avg_yield else 'Below Average',
        'yield_diff': round(div_yield - avg_yield, 2),
        'margin_status': 'Leader' if fund.get('net_margin', 0) > sector_avg.get('avg_margin', 0) else 'Laggard'
    }
    
    return comparison

if __name__ == "__main__":
    # Test
    print("Testing Peer Analysis...")
    # Mock data might be needed if DB is empty, but we ran scraper for 5 stocks
    # Ensure those stocks have sectors in DB or Config
    res = analyze_peer_comparison("OGDC")
    print(res)
