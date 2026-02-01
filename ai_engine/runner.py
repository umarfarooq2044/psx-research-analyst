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
    2. Query Gemini (Intelligence).
    3. Save Decisions (Memory).
    """
    print("🧠 Starting Cognitive Decision Engine...")
    
    # 1. Build Payload
    payload = payload_builder.build_market_payload()
    if not payload:
        print("❌ Failed to build payload.")
        return
        
    # 2. Get Analysis
    print("⏳ Waiting for Gemini 1.5 Pro Analysis...")
    decisions = ai_analyst.analyze_market_batch(payload)
    
    if not decisions:
        print("⚠️ No decisions returned from AI.")
        return
        
    print(f"✅ Received {len(decisions)} strategic decisions.")
    
    # 3. Save to DB
    print("💾 Saving decisions to database...")
    db.save_ai_decisions(decisions)
    print("✓ AI Knowledge Stored.")
    
    return decisions

if __name__ == "__main__":
    run_cognitive_engine()
