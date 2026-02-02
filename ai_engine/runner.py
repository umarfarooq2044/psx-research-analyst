import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import db
import json
import asyncio

async def async_run_cognitive_engine():
    """
    Main entry point for the AI Decision Loop (Asynchronous).
    """
    print("🧠 Starting Groq Cognitive Decision Engine (SMI-v2 Chorus of Agents)...")
    
    from ai_engine.ai_decision import GroqBrain
    brain = GroqBrain()
    
    from database.db_manager import db
    # Analyze top 15 symbols based on volume/interest for high-conviction
    all_tickers = db.get_all_tickers()
    tickers = all_tickers[:15] 
    
    tasks = []
    for t in tickers:
        sym = t['symbol']
        price = db.get_latest_price(sym)
        tech = db.get_technical_indicators(sym) or {}
        lev = db.get_latest_leverage(sym) or {}
        news = db.get_recent_news_for_ticker(sym, days=7)
        
        # SMI-v2 High Fidelity Context
        context = {
            "Symbol": sym,
            "Price_Data": {
                "Close": price['close_price'] if price else 0,
                "Volume": price['volume'] if price else 0
            },
            "Technical_Indicators": {
                "RSI": tech.get('rsi'),
                "OBV": tech.get('obv'),
                "AD": tech.get('ad'),
                "ATR": tech.get('atr'),
                "Volume_Accel": tech.get('volume_accel'),
                "Trend": tech.get('trend')
            },
            "Settlement_Data": {
                "MTS_Volume": lev.get('mts_volume'),
                "Futures_OI": lev.get('futures_oi'),
                "Risk_Level": lev.get('risk_level')
            },
            "Narrative_Context": news[:5]
        }
        tasks.append(brain.get_decision(context))
    
    results = await asyncio.gather(*tasks)
    
    formatted = []
    for i, res in enumerate(results):
        formatted.append({
            "ticker": tickers[i]['symbol'],
            "signal": res['decision'],
            "conviction": f"{res['confidence']}%",
            "score": res.get('confidence', 0),
            "reasoning": res['smi_commentary'],
            "future_path": f"ATR-Adjusted Exit: {res.get('suggested_exit_atr', 0)}",
            "black_swan": res['psx_risk_flag'],
            "catalyst": json.dumps(res.get('expert_consensus', {}))
        })
    
    if formatted:
        print(f"✅ Received {len(formatted)} strategic decisions from SMI-v2.")
        print("💾 Saving decisions to database...")
        db.save_ai_decisions(formatted)
        print("✓ AI Knowledge Stored.")
    
    return formatted

def run_cognitive_engine():
    """Synchronous wrapper for run_cognitive_engine"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            return asyncio.ensure_future(async_run_cognitive_engine())
        else:
            return loop.run_until_complete(async_run_cognitive_engine())
    except RuntimeError:
        return asyncio.run(async_run_cognitive_engine())

if __name__ == "__main__":
    run_cognitive_engine()

if __name__ == "__main__":
    run_cognitive_engine()
