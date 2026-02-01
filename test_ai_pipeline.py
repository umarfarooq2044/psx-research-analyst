import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai_engine.mock_model import MockGeminiAnalyst
from database.db_manager import db
from datetime import datetime

def test_ai_pipeline():
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        
    print("🧪 Testing AI Pipeline with Mock Model...")
    
    # 1. Mock Analysis
    mock_ai = MockGeminiAnalyst()
    decisions = mock_ai.analyze_market_batch("dummy payload")
    
    # 2. Save to DB
    print(f"💾 Saving {len(decisions)} mock decisions...")
    try:
        db.save_ai_decisions(decisions)
        print("✅ Save successful!")
    except Exception as e:
        print(f"❌ DB Save Failed: {e}")
        return

    # 3. Verify Read
    print("🔍 Verifying data in DB...")
    # Direct SQL check or using session
    try:
        from database.models import get_db_session, AIDecision
        with get_db_session() as session:
            saved = session.query(AIDecision).filter_by(date=datetime.now().date()).all()
            print(f"✅ Found {len(saved)} decisions in DB.")
            for s in saved:
                print(f"   - {s.symbol}: {s.action} ({s.reasoning})")
    except Exception as e:
        print(f"❌ Verification Failed: {e}")

if __name__ == "__main__":
    test_ai_pipeline()
