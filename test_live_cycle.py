"""
PSX Research Analyst - Full Market Cycle Simulation (SMI-v2)
Verifies Pre-Market -> Hourly -> Post-Market flow
"""
import os
import sys
import asyncio
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.db_manager import db
from scheduler.orchestrator import run_now
from report.hourly_update import run_hourly_update
from analysis.leverage_radar import leverage_radar
from analysis.macro_observer import macro_observer

import nest_asyncio
nest_asyncio.apply()

def simulate_cycle():
    print("🚀 STARTING SMI-v2 FULL CYCLE SIMULATION\n")
    
    # 0. Setup & Seeding
    print("🛠️ [0/4] Seeding Mock Data for Stability...")
    tickers = ['SYS', 'OGDC', 'LUCK', 'ENGRO', 'HUBC']
    for sym in tickers:
        db.upsert_ticker(sym, f"{sym} Corporation", "Technology")
        
        # Seed Technicals
        db.save_technical_indicators(sym, {
            'rsi': 45.5,
            'obv': 1200000,
            'ad': 850000,
            'atr': 2.5,
            'volume_accel': 1.2,
            'trend': 'Bullish'
        })
        
        # Seed Leverage
        db.save_leverage_data(sym, {
            'mts_volume': 500000,
            'futures_oi': 1000000,
            'risk_level': 'Low'
        })

    # 1. Pre-Market Simulation
    print("\n🌅 [1/4] Simulating Pre-Market Briefing (6:00 AM)...")
    try:
        run_now('pre_market')
        print("✅ Pre-Market Successful.")
    except Exception as e:
        print(f"❌ Pre-Market Failed: {e}")

    # 2. Hourly Update Simulation
    print("\n⏰ [2/4] Simulating Hourly Surveillance (Mid-Day)...")
    try:
        run_hourly_update()
        print("✅ Hourly Update Successful.")
    except Exception as e:
        print(f"❌ Hourly Update Failed: {e}")

    # 3. Post-Market Simulation
    print("\n🌗 [3/4] Simulating Post-Market Deep Analysis (4:30 PM)...")
    try:
        run_now('post_market')
        print("✅ Post-Market Successful.")
    except Exception as e:
        print(f"❌ Post-Market Failed: {e}")

    print("\n🏁 [4/4] CYCLE SIMULATION COMPLETE.")

if __name__ == "__main__":
    simulate_cycle()
