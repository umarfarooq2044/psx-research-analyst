import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduler.orchestrator import ScheduleOrchestrator
from report.csv_generator import report_generator

async def test_groq_reports():
    print("🚀 Testing Final Groq-Powered Reporting Pipeline...")
    
    # 1. Test CSV Generation with Mock Decisions
    print("\n[1/3] Testing AI Decision CSV Generation...")
    mock_decisions = [
        {'symbol': 'OGDC', 'decision': 'BUY', 'confidence': 90, 'smi_commentary': 'High conviction buy', 'psx_risk_flag': 'Safe'},
        {'symbol': 'HBL', 'decision': 'HOLD', 'confidence': 50, 'smi_commentary': 'Wait for breakout', 'psx_risk_flag': 'Speculative'}
    ]
    csv_path = report_generator.generate_ai_decisions_csv(mock_decisions)
    if os.path.exists(csv_path):
        print(f"✅ AI Decision CSV generated: {csv_path}")
    else:
        print("❌ AI Decision CSV generation failed.")

    # 2. Test Market Synthesis
    print("\n[2/3] Testing Groq Synthesis...")
    try:
        from analysis.market_synthesis import market_brain
        # We'll use a mock news_data to avoid the async_collect_all_news issue in this test
        mock_news = {
            'national': [{'headline': 'SBP maintains rates', 'sentiment': 0.1, 'source': 'DAWN'}],
            'international': [],
            'announcements': [],
            'sentiment_label': 'Neutral'
        }
        synthesis = await market_brain.generate_synthesis(
            news_data=mock_news,
            market_status={'close_value': 90000},
            macro_data={'usd_pkr': 280},
            top_movers={}
        )
        print(f"✅ Groq Synthesis Successful: {synthesis['strategy']}")
        print(f"   Commentary: {synthesis.get('commentary', 'N/A')}")
        print(f"   Risk Flag: {synthesis.get('risk_flag', 'N/A')}")
    except Exception as e:
        print(f"❌ Groq Synthesis Failed: {e}")

    print("\n✨ Verification Complete.")

if __name__ == "__main__":
    asyncio.run(test_groq_reports())
