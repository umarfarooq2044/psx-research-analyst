import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.model import ai_analyst
from ai_engine.payload_builder import payload_builder
from database.db_manager import db
import json

def run_cognitive_engine():
    """
    Main entry point for the AI Decision Loop.
    1. Build Payload (Data).
    2. Query Groq (Intelligence).
    3. Save Decisions (Memory).
    """
    print("🧠 Starting Groq Cognitive Decision Engine (SMI-v1)...")
    
    from ai_engine.ai_decision import GroqBrain
    brain = GroqBrain()
    
    # 1. Build Payload
    from ai_engine.payload_builder import payload_builder
    payload_data = payload_builder.build_market_payload() # This likely returns a Dict or we can parse it
    if not payload_data:
        print("❌ Failed to build payload.")
        return
        
    # 2. Get Analysis
    print("⏳ Waiting for Groq (Llama-3.3-70b) Strategic Analysis...")
    
    async def get_all_decisions():
        # If payload_builder returns a string (prompt), we might need to adjust.
        # Assuming we can iterate through tickers in the payload.
        # For simplicity in this refactor, we'll analyze the top 20 tickers.
        from database.db_manager import db
        tickers = db.get_all_tickers()[:20] 
        tasks = []
        for t in tickers:
            # Mocking context from DB for batch
            price = db.get_latest_price(t['symbol'])
            context = {
                "Symbol": t['symbol'],
                "Close_Price": price['close_price'] if price else 0,
                "RSI_14": 50,
                "Volume_Ratio": 1.0,
                "News_Sentiment": "Neutral"
            }
            tasks.append(brain.get_decision(context))
        
        results = await asyncio.gather(*tasks)
        # Map back to the expected format for db.save_ai_decisions
        formatted = []
        for i, res in enumerate(results):
            formatted.append({
                "ticker": tickers[i]['symbol'],
                "signal": res['decision'],
                "conviction": f"{res['confidence']}%",
                "future_path": "T+7 Projection via SMI-v1",
                "black_swan": res['psx_risk_flag'],
                "reasoning": res['smi_commentary']
            })
        return formatted

    import asyncio
    decisions = asyncio.run(get_all_decisions())
    
    if not decisions:
        print("⚠️ No decisions returned from AI.")
        return
        
    print(f"✅ Received {len(decisions)} strategic decisions from SMI-v1.")
    
    # 3. Save to DB
    print("💾 Saving decisions to database...")
    db.save_ai_decisions(decisions)
    print("✓ AI Knowledge Stored.")
    
    return decisions

if __name__ == "__main__":
    run_cognitive_engine()
