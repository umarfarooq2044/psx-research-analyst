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
    ROLE: Defensive Fundamental Analyst. 
    FOCUS: Value, Dividends, Sector Beta, and Fair Value.
    CRITERIA: If PE > 15 and ROE < 10, be extremely cautious. Look for 'Value Traps'.
    """,
    "QUANT_SNIPER": """
    ROLE: High-Frequency Technical Sniper.
    FOCUS: RSI, MACD, Bollinger position, OBV (Volume Quality), and ATR (Volatility).
    CRITERIA: Only signal Buy if OBV is rising and price > 200DMA. Identify 'Momentum Ignition'.
    """,
    "SETTLEMENT_WATCHER": """
    ROLE: Risk & Settlement Officer (NCCPL Expert).
    FOCUS: MTS (Leverage) and Futures Open Interest (OI).
    CRITERIA: If MTS (Leverage) is high, signal SELL/REDUCE regardless of technicals. Danger of Margin Calls.
    """,
    "MACRO_GENERAL": """
    ROLE: Sovereign & Geopolitical Strategist.
    FOCUS: IMF news, USD/PKR, Oil, and Political stability.
    CRITERIA: If IMF status is 'Uncertain', override all bullish signals. Market risk is systemic.
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
        self.semaphore = asyncio.Semaphore(2) # Conservative for 429 prevention

    async def get_agent_opinion(self, persona: str, data: Dict[str, Any], session: aiohttp.ClientSession) -> str:
        """Get the opinion of a single specialized agent."""
        async with self.semaphore:
            payload = {
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": AGENT_PROMPTS[persona]},
                    {"role": "user", "content": f"Analyze this ticker context and provide a brief expert opinion: {json.dumps(data)}"}
                ],
                "temperature": 0.3
            }
            try:
                # Use the passed session for task context stability
                async with session.post(self.base_url, headers=self.headers, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        result = await response.json()
                        await asyncio.sleep(0.5) # Jitter/Throttling
                        content = result['choices'][0]['message']['content']
                        return content
                    elif response.status == 429:
                        await asyncio.sleep(2) # Backoff
                        return "Rate Limited (Backing off)"
            except Exception as e:
                return f"Neutral/No Opinion ({str(e)})"
            return "No Data"


    async def get_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        SMI-v2: Chorus of Agents Synthesis.
        1. Queries specialists in parallel.
        2. Synthesizes via Moderator.
        """
        async with aiohttp.ClientSession() as session:
            # Step 1: Gather Opinions from the Chorus
            print(f"🧐 [Chorus] Consulting specialists for {data.get('Symbol')}...")
            
            # Wrap in Tasks to ensure proper context for Timeout managers
            tasks = [asyncio.create_task(self.get_agent_opinion(persona, data, session)) 
                    for persona in AGENT_PROMPTS.keys()]
            opinions = await asyncio.gather(*tasks)
            
            chorus_content = {
                "Fundamental": opinions[0],
                "Technical": opinions[1],
                "Settlement": opinions[2],
                "Macro": opinions[3]
            }
            
            # Step 2: Final Synthesis via Moderator
            async with self.semaphore:
                payload = {
                    "model": GROQ_MODEL,
                    "messages": [
                        {"role": "system", "content": MODERATOR_PROMPT},
                        {"role": "user", "content": f"Here is the expert chorus analysis for {data.get('Symbol')}: {json.dumps(chorus_content)}. Context: {json.dumps(data)}"}
                    ],
                    "response_format": {"type": "json_object"},
                    "temperature": 0.1
                }

                # SMI-v2 Alpha Engine (Chorus of Agents)
                timeout = aiohttp.ClientTimeout(total=25)
                try:
                    async with session.post(self.base_url, headers=self.headers, json=payload, timeout=timeout) as response:
                        if response.status == 200:
                            result = await response.json()
                            content = result['choices'][0]['message']['content']
                            return json.loads(content)
                        else:
                            print(f"Moderator Error: {response.status}")
                except Exception as e:
                    print(f"Chorus Circuit Breaker Active: {e}")

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
