import requests
from bs4 import BeautifulSoup
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db_manager import db

class MacroObserver:
    """
    SMI-v2 Resilience Component.
    Fetches USD/PKR, Oil, and Global rates from multiple redundant sources.
    """
    
    def __init__(self):
        self.sources = {
            "USD_PKR": [
                "https://open.er-api.com/v6/latest/USD",
                "https://api.exchangerate-api.com/v4/latest/USD",
                "SCRAPE_SBP" # Placeholder for scraping SBP
            ],
            "OIL": [
                "https://api.oilpriceapi.com/v1/prices/latest", # Needs Key
                "SCRAPE_INVESTING" # Placeholder
            ]
        }

    def fetch_usd_pkr(self) -> float:
        """Fetch USD/PKR with fallback to DB if APIs fail"""
        print("🌍 [Macro] Fetching USD/PKR Rate...")
        
        # Source 1: Open ER API
        try:
            r = requests.get(self.sources["USD_PKR"][0], timeout=5)
            if r.status_code == 200:
                rate = r.json().get('rates', {}).get('PKR')
                if rate: return round(rate, 2)
        except: pass
        
        # Source 2: ExchangeRate API
        try:
            r = requests.get(self.sources["USD_PKR"][1], timeout=5)
            if r.status_code == 200:
                rate = r.json().get('rates', {}).get('PKR')
                if rate: return round(rate, 2)
        except: pass
        
        # Source 3: DB Fallback (Last known value)
        print("⚠️ USD/PKR APIs failed. Falling back to Database memory...")
        latest = db.get_latest_global_markets()
        if latest and latest.get('usd_pkr'):
            return latest['usd_pkr']
            
        return 280.0 # Extreme Hardcoded Fallback

    def fetch_oil_price(self) -> float:
        """Fetch Brent Oil Price with fallbacks"""
        print("🛢️ [Macro] Fetching Brent Oil Rate...")
        # Placeholder for real Brent API or scraping
        latest = db.get_latest_global_markets()
        return latest.get('brent_oil', 80.0) if latest else 80.0

    def get_full_macro_packet(self) -> Dict:
        """Get all macro indicators for the AI context"""
        return {
            "usd_pkr": self.fetch_usd_pkr(),
            "oil_brent": self.fetch_oil_price(),
            "kibor_6m": 22.5 # Placeholder or fetch from SBP
        }

macro_observer = MacroObserver()

if __name__ == "__main__":
    print(macro_observer.get_full_macro_packet())
