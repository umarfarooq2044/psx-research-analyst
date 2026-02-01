from typing import List, Dict

class MockGeminiAnalyst:
    """Mock AI for testing pipeline logic"""
    def analyze_market_batch(self, payload: str) -> List[Dict]:
        print("🤖 [MOCK AI] Analyzing payload...")
        return [
            {
                "ticker": "OGDC",
                "score": 85,
                "action": "BUY",
                "conviction": "High",
                "reasoning": "Strong oil prices and discovery news.",
                "catalyst": "Quarterly earnings next week"
            },
            {
                "ticker": "TRG",
                "score": -40,
                "action": "WAIT",
                "conviction": "Medium",
                "reasoning": "Tech sector global sell-off.",
                "catalyst": "None"
            }
        ]

if __name__ == "__main__":
    # Test Import
    pass
