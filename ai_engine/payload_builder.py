from typing import List, Dict
from database.db_manager import db
from datetime import datetime, timedelta

class PayloadBuilder:
    """
    Constructs the data context for the AI.
    """
    
    def build_market_payload(self) -> str:
        """
        Gather all relevant market data for the AI context window.
        """
        print("📦 Building AI Data Payload (Financials + News + Technicals)...")
        
        # 1. Get Active Tickers & Prices
        tickers = db.get_all_tickers()
        # Optimization: Take top 100 by volume for V1 to ensure speed
        # Or take all if we truly want unlimited. User said "process entire payload".
        # Let's try to get as much as possible.
        
        # 2. Get Fundamentals (P/E, EPS)
        # We need a way to get map of fundamentals. 
        # Assuming db has a method or we query directly.
        # For prototype, we'll fetch what we have.
        
        # 3. Get News (Last 48 hours for immediate context)
        # In a real vector system, we'd search per ticker.
        # Here we dump the 'Market Moving' news.
        
        payload_lines = []
        payload_lines.append(f"ANALYSIS DATE: {datetime.now().strftime('%Y-%m-%d')}")
        
        # A. GLOBAL MACRO
        payload_lines.append("\n=== GLOBAL MACRO CONTEXT ===")
        # (Fetch from DB or cache)
        payload_lines.append("- USD/PKR: Stable at 278") # Placeholder, should be dynamic
        payload_lines.append("- Interest Rate: 22%")
        
        # B. RECENT MARKET MOVING NEWS
        payload_lines.append("\n=== KEY NEWS HEADLINES (LAST 24 HOURS) ===")
        # TODO: Fetch from DB
        
        # C. COMPANY DATA
        payload_lines.append("\n=== COMPANY DATA (FINANCIALS + TECHNICALS) ===")
        
        # We need to construct a CSV-like or JSON-like block for tokens efficiency
        # Ticker | Price | Change | Vol | P/E | RSI | News_Sentiment
        header = "Symbol | Price | Change% | Volume | RSI | Sentiment | Sector"
        payload_lines.append(header)
        
        # Mocking or Fetching Real Data (Use DB)
        # For now, let's assume we have a list of dicts. 
        # Implementation Detail: This requires a JOIN query in DB.
        
        return "\n".join(payload_lines)

    def format_ticker_data(self, ticker: str, price_data: Dict, fund_data: Dict) -> str:
        return f"{ticker} | {price_data.get('close')} | ..."

payload_builder = PayloadBuilder()
