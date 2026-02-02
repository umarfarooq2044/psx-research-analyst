import asyncio
import json
import os
import sys

# Add root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.runner import run_cognitive_engine
from scheduler.orchestrator import orchestrator
from database.db_manager import db

async def verify_alpha_engine():
    print("🚀 [VERIFY] Starting SMI-v2 Alpha Engine Verification...")
    
    # 1. Test Leverage Radar
    from analysis.leverage_radar import leverage_radar
    print("🔍 [1/3] Testing Leverage Radar...")
    leverage_radar.run_leverage_audit()
    
    # 2. Test Macro Observer
    from analysis.macro_observer import macro_observer
    print("🌍 [2/3] Testing Macro Observer...")
    packet = macro_observer.get_full_macro_packet()
    print(f"   → Macro Packet: {packet}")
    
    # 3. Running Cognitive Engine (Chorus of Agents)
    print("🧠 [3/3] Testing Chorus of Agents (Top 5 Tickers)...")
    from ai_engine.runner import async_run_cognitive_engine
    decisions = await async_run_cognitive_engine()
    
    if decisions:
        print(f"✅ [SUCCESS] Chorus of Agents returned {len(decisions)} deterministic signals.")
        for d in decisions[:2]:
            print(f"   → {d['ticker']}: {d['signal']} | {d['reasoning']}")
    else:
        print("❌ [FAILURE] Cognitive engine returned no decisions.")

if __name__ == "__main__":
    asyncio.run(verify_alpha_engine())
