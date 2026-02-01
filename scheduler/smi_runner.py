import time
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db
from scraper.price_scraper import fetch_all_prices
from news.comprehensive_news import get_market_moving_news
from ai_engine.payload_builder import build_market_payload
from ai_engine.model import ai_analyst
from utils.resilience import safe_execute

def smi_reasoning_cycle():
    """
    The High-Frequency 'SMI-v1' Reasoning Loop.
    Simulation -> Triangulation -> Action.
    """
    print(f"\n🦅 [SMI-v1] STARTING COGNITIVE FREQUENCY LOOP - {datetime.now().strftime('%H:%M:%S')}")
    print("-" * 60)
    
    # 1. Gather 'Senses' (Limit to Top Tier for 100x Speed)
    # We pull Top 50 tickers by volume/liquidity
    print("[1/4] GATHERING SENSES (Tick Data + Macro)...")
    tickers = db.get_all_tickers()[:50] 
    symbols = [t['symbol'] for t in tickers]
    
    # Rapid Price Fetch
    fetch_all_prices(symbols)
    
    # Fresh News
    news = get_market_moving_news()
    
    # 2. Build Neuro-Payload (Sovereign Context + Future Map included automatically)
    print("[2/4] TRIGGERING FUTURE-MAPPING SIMULATIONS...")
    prices = [db.get_latest_price(s) for s in symbols if db.get_latest_price(s)]
    payload = build_market_payload(prices, news)
    
    # 3. Feed the Cortex (Gemini)
    print("[3/4] CORTICAL PROCESSING (Recursive AI Logic)...")
    decisions = ai_analyst.analyze_market_batch(payload)
    
    # 4. Trigger Reflex (Save & Act)
    print(f"[4/4] REFLEX TRIGGERED: Generated {len(decisions)} SMI Signals.")
    db.save_ai_decisions(decisions)
    
    for d in decisions[:5]:
        print(f"   ➤ {d['ticker']}: {d['signal']} ({d['conviction']}) | Target Range: {d['future_path']}")

@safe_execute()
def run_smi_engine(loop_seconds: int = 300):
    """
    Continuous operation. 
    User requested 60s, but we use 300s (5m) as safe default for cloud stability.
    """
    print("🚀 SOVEREIGN MARKET INTELLIGENCE (SMI-v1) ONLINE")
    print("Neuro-Architecture: Senses -> Memory -> Cortex -> Reflex")
    
    while True:
        try:
            smi_reasoning_cycle()
        except KeyboardInterrupt:
            print("\nShutting down SMI Brain...")
            break
        except Exception as e:
            print(f"CRITICAL BRAIN FAILURE: {e}. Attempting self-healing in 30s...")
            time.sleep(30)
            continue
            
        print(f"\nSleeping for {loop_seconds}s (Frequency Cycle)...")
        time.sleep(loop_seconds)

if __name__ == "__main__":
    # If run directly, start the high-frequency engine
    run_smi_engine(loop_seconds=60) # 60 seconds as per user request
