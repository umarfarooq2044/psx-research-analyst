"""
SMI-v3 Ultra: Long-Term Institutional Wealth Engine
Institutional-Grade Decision Making for PSX - Focus on Wealth Generation

This module uses Groq's full capacity (Llama-3.3-70b) to identify perfect 
long-term compounders in the Pakistan Stock Exchange. It operates at ultra-speed
to analyze the entire market in seconds.
"""

import os
import json
import requests
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

# Load API Key from environment
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_BASE_URL = "https://api.groq.com/openai/v1/chat/completions"

# ============================================================================
# INSTITUTIONAL VALUE EXPERT PERSONA (25+ Years PSX Experience)
# ============================================================================
INSTITUTIONAL_ULTRA_PROMPT = """You are an institutional CIO with 25+ years of experience generating alpha in the Pakistan Stock Exchange. Your philosophy is rooted in Value Investing (Warren Buffett / Charlie Munger) but specialized for the high-volatility, high-inflation environment of Pakistan.

Your mission is to find "Tenbaggers" and "Forever Compounders". You ignore short-term noise and focus on:

1. **Economic Moat**: Does the company have a dominant market share (e.g., LUCK in cement, EFERT in fertilizer, SYS in tech)?
2. **Management Quality**: Are they shareholder-friendly? Look at their dividend consistency and payout ratios.
3. **ROE & ROIC**: You demand consistent Return on Equity above 20%. Capital efficiency is everything.
4. **Resilience to Devaluation**: Can the company pass on costs? Does it have export-based dollar earnings (like TRG or SYS)?
5. **Debt Discipline**: In a high-interest rate environment (20%+), a leveraged balance sheet is a death sentence. You prefer low-debt giants.
6. **Valuation**: You buy "Dollar Bills for 50 Cents". You compare P/E and P/B to 10-year historical averages.

Your goal is to provide a long-term institutional verdict. You MUST respond in the following JSON format ONLY:

{
    "action": "STRONG BUY | BUY | ACCUMULATE | HOLD | REDUCE | AVOID",
    "conviction": <0-100>,
    "value_score": <1-100 based on fundamental strength>,
    "target_price_1y": <PKR value>,
    "stop_loss_long": <PKR value (Margin of Safety level)>,
    "time_horizon": "1-3 Years (Wealth Generation)",
    "long_term_rational": "<Detailed 4-5 sentence report on why this is a wealth-generating asset or a trap>",
    "moat_rating": "Wide | Narrow | None",
    "risk_flag": "Safe | Moderate | High Risk",
    "key_investment_pillar": "<The single most important reason to own this stock for 3 years>"
}
"""

class DeepResearchEngine:
    """
    SMI-v3 Ultra: High-speed institutional engine for long-term wealth generation.
    """
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = GROQ_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
    def _call_groq(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ultra-low latency call to Groq."""
        if not self.api_key:
            return None

        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Perform institutional deep analysis on this asset:\n\n{json.dumps(data, indent=2)}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1 # Minimum variance for institutional consistency
        }
        
        try:
            # Short timeout because Groq is 100x faster than traditional LLMs
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                return None
        except Exception as e:
            print(f"SMI-v3 Ultra Error: {e}")
            return None

    def analyze_stock_ultra(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deep research for long-term wealth."""
        decision = self._call_groq(INSTITUTIONAL_ULTRA_PROMPT, stock_data)
        
        if decision:
            decision['symbol'] = stock_data.get('Symbol', 'N/A')
            decision['current_price'] = stock_data.get('Price', 0)
            return decision
        return None

    def find_wealth_generation_picks(self, market_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        SMI-v3 Ultra: Analyze the entire market at 100x speed.
        Returns the TOP 10 Long-Term High-Conviction Compounders.
        """
        print(f"🚀 [SMI-v3 Ultra] Booting Institutional Engine... Analyzing {len(market_data)} companies for Wealth Generation...")
        
        # Massive parallelization for 100x speed
        # Groq's high rate limits allow for extreme concurrency
        with ThreadPoolExecutor(max_workers=50) as executor:
            decisions = list(executor.map(self.analyze_stock_ultra, market_data))
        
        # Filter successes and high-conviction BUYs
        actionable = [d for d in decisions if d and d.get('action') in ['STRONG BUY', 'BUY']]
        
        # Institutional Ranking: Score = (Conviction * 0.4) + (ValueScore * 0.6)
        for pick in actionable:
            pick['institutional_score'] = (pick.get('conviction', 0) * 0.4) + (pick.get('value_score', 0) * 0.6)
            
        actionable.sort(key=lambda x: x.get('institutional_score', 0), reverse=True)
        
        top_picks = actionable[:10]
        print(f"✅ SMI-v3 Ultra Complete. Identified {len(top_picks)} High-Conviction Long-Term Assets.")
        
        return top_picks

if __name__ == "__main__":
    import sys
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    print("🔥 SMI-v3 ULTRA LIVE TEST")
    engine = DeepResearchEngine()
    
    # Mock Blue-Chip Data
    test_data = [
        {
            "Symbol": "SYS",
            "Price": 450.00,
            "Fundamentals": {"ROE": 25.5, "PE": 18, "DY": 2.5, "Debt": "Low", "Export_Revenue": "90%"},
            "Moat": "Dominant IT Exporter, Scale Advantage",
            "News": ["New $50M contract signed in KSA", "Record quarterly profit"]
        },
        {
            "Symbol": "EFERT",
            "Price": 165.00,
            "Fundamentals": {"ROE": 35.0, "PE": 7.5, "DY": 12.0, "Debt": "Low", "Cash_Flow": "Strong"},
            "Moat": "Oligopoly in Fertilizer, Critical National Asset",
            "News": ["Gas price subsidy extended", "Higher urea demand expected"]
        }
    ]
    
    results = engine.find_wealth_generation_picks(test_data)
    print(json.dumps(results, indent=2))
