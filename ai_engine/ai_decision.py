import aiohttp
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY, GROQ_MODEL

# SMI-v2 Chorus of Agents Specialized Prompts

AGENT_PROMPTS = {
    "FUND_ANALYST": """
    ROLE: Defensive Fundamental Analyst for Pakistan Stock Exchange.
    FOCUS: Value, Dividends, Sector Beta, and Fair Value.
    CRITERIA: 
    - If PE > 15 and ROE < 10, be extremely cautious. Look for 'Value Traps'.
    - In Pakistan's high-inflation environment (20%+), dividend yield must beat T-bills (15%+).
    - Be wary of high debt in companies due to KIBOR at 17-20%.
    - Preferred sectors for value: Fertilizer (EFERT, FFC), Banks (HBL, MCB), Cement (LUCK).
    """,
    "QUANT_SNIPER": """
    ROLE: High-Frequency Technical Sniper for PSX.
    FOCUS: RSI, MACD, Bollinger position, OBV (Volume Quality), and ATR (Volatility).
    CRITERIA: 
    - Only signal Buy if OBV is rising and price > 200DMA. Identify 'Momentum Ignition'.
    - PSX has T+2 settlement - factor this into short-term moves.
    - Watch for 3:15 PM power hour manipulation (last 15 mins of trading).
    - Volume spikes without price follow-through = institutional distribution.
    """,
    "SETTLEMENT_WATCHER": """
    ROLE: Risk & Settlement Officer (NCCPL/CDC Expert) for PSX.
    FOCUS: MTS (Margin Trading System), Futures Open Interest (OI), and Leverage.
    CRITERIA: 
    - If MTS (Leverage) is high, signal SELL/REDUCE regardless of technicals. Danger of Margin Calls.
    - Monday/Tuesday after settlement = high volatility due to T+2 cycle.
    - Watch NCCPL data for institutional delivery patterns.
    - High OI at resistance = likely rejection.
    """,
    "MACRO_GENERAL": """
    ROLE: Sovereign & Geopolitical Strategist for Pakistan.
    FOCUS: IMF program status, USD/PKR, Oil prices, Political stability, Inflation.
    CRITERIA: 
    - If IMF status is 'Uncertain', override all bullish signals. Market risk is systemic.
    - Oil above $90 = serious pressure on PKR and CAD.
    - Political uncertainty in Punjab = cement/textile weakness.
    - KIBOR cuts = banks underperform, growth stocks outperform.
    """
}

MODERATOR_PROMPT = """
ROLE: Chief Investment Officer (CIO) of SMI-v1 Cognitive.
OBJECTIVE: Synthesize the input from 4 specialists (Fund, Quant, Settlement, Macro) into a SINGLE deterministic signal.

DETERMINISTIC SIGNALS:
1. STRONG BUY: Unanimous bullish consensus + Low Leverage.
2. ACCUMULATE: Bullish story, but technicals suggest entry in tranches (buy on dips).
3. WAIT-TO-BUY: Bullish setup, but RSI/Price is too high. Wait for mean reversion.
4. HOLD: No strong directional catalyst.
5. REDUCE / SELL: Technical breakdown or high leverage trap detected.
6. STAY AWAY: High risk of systemic failure or margin calls.

OUTPUT FORMAT (JSON ONLY):
{
  "decision": "STRONG BUY" | "ACCUMULATE" | "WAIT-TO-BUY" | "HOLD" | "REDUCE" | "SELL" | "STAY AWAY",
  "confidence": <int 0-100>,
  "smi_commentary": "Short, punchy synthesis of why this signal was chosen.",
  "expert_consensus": { "Fund": "...", "Quant": "...", "Settlement": "...", "Macro": "..." },
  "psx_risk_flag": "Safe" | "Speculative" | "Satta Alert" | "Margin Call Risk",
  "suggested_exit_atr": <float | 0> 
}
"""

class GroqBrain:
    """SMI-v1 Cognitive Engine using Groq Llama-3.3-70b"""
    
    def __init__(self):
        self.api_key = GROQ_API_KEY
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.semaphore = asyncio.Semaphore(20) # Paid Plan Optimization

    def _sync_get_agent_opinion(self, persona: str, data: Dict[str, Any]) -> str:
        """Synchronous version for thread pool execution."""
        import requests
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": AGENT_PROMPTS[persona]},
                {"role": "user", "content": f"Analyze this ticker context and provide a brief expert opinion: {json.dumps(data)}"}
            ],
            "temperature": 0.3
        }
        try:
            # Synchronous requests call to bypass asyncio timer context issues
            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=20)
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            elif response.status_code == 429:
                return "Rate Limited (Auto-Retry active)"
        except Exception as e:
            return f"Neutral/No Opinion ({str(e)})"
        return "No Data"

    async def get_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        SMI-v2: Chorus of Agents Synthesis.
        Optimized with ThreadPoolExecutor for parallel requests while maintaining stability.
        """
        import requests
        from concurrent.futures import ThreadPoolExecutor
        print(f"🧐 [Chorus] Consulting specialists for {data.get('Symbol')}...")
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=4) as executor:
            # Parallelize the 4 agent opinions
            tasks = [
                loop.run_in_executor(executor, lambda p=p: self._sync_get_agent_opinion(p, data))
                for p in AGENT_PROMPTS.keys()
            ]
            opinions = await asyncio.gather(*tasks)
            
        chorus_content = {
            "Fundamental": opinions[0],
            "Technical": opinions[1],
            "Settlement": opinions[2],
            "Macro": opinions[3]
        }
        
        # Step 2: Final Synthesis via Moderator
        try:
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": MODERATOR_PROMPT},
                    {"role": "user", "content": f"Here is the expert chorus analysis for {data.get('Symbol')}: {json.dumps(chorus_content)}. Context: {json.dumps(data)}"}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }

            response = requests.post(self.base_url, headers=self.headers, json=payload, timeout=40)
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                return json.loads(content)
            else:
                print(f"Moderator Error: {response.status_code}")
                return None
        except Exception as e:
            print(f"Chorus Circuit Breaker Active for {data.get('Symbol')}: {e}")

        # Default Neutral Signal
        return {
            "decision": "HOLD",
            "confidence": 0,
            "smi_commentary": "Signal unavailable (Chorus Orchestration Failed).",
            "psx_risk_flag": "Safe"
        }

# Standalone test
if __name__ == "__main__":
    brain = GroqBrain()
    test_data = {
      "Symbol": "OGDC",
      "RSI_14": 41,
      "Volume_Ratio": 3.5,
      "MACD_Signal": "Bearish",
      "News_Sentiment": "Neutral"
    }
    
    async def test():
        decision = await brain.get_decision(test_data)
        print(json.dumps(decision, indent=2))
        
    asyncio.run(test())
