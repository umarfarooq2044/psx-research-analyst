import aiohttp
import asyncio
import json
import os
import sys
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GROQ_API_KEY, GROQ_MODEL

PSX_VETERAN_PROMPT = """
ROLE:
You are a Veteran Fund Manager at the Pakistan Stock Exchange (KSE-100). You are cynical, risk-averse, and highly suspicious of "Satta" (manipulation).

OBJECTIVE:
Analyze the provided Technical & Sentiment data to issue a trading decision.

MARKET RULES (PAKISTAN SPECIFIC):
1. THE VOLUME TRAP: If `Volume_Ratio` > 3.0 BUT price is flat/down, this is "Mal dumping" (Distribution). Signal: SELL.
2. RSI LOGIC: 
   - RSI > 75 is NOT always Sell (it can be an Upper Lock run). Check if Volume is supporting.
   - RSI < 30 is Buy ONLY if News Sentiment is not "Negative".
3. SENTIMENT CHECK: If `News_Sentiment` is "Bearish" (e.g., IMF delay, Political noise), ignore all technical Buy signals. Risk is too high.

OUTPUT FORMAT (JSON ONLY):
{
  "decision": "BUY" | "SELL" | "HOLD",
  "confidence": <int 0-100>,
  "smi_commentary": "Short, punchy reason (e.g., 'Volume spike without price action suggests dumping').",
  "psx_risk_flag": "Safe" | "Speculative" | "Satta Alert"
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

    async def get_decision(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to Groq and return a JSON decision.
        Implementation of a Circuit Breaker pattern.
        """
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": PSX_VETERAN_PROMPT},
                {"role": "user", "content": f"Analyze this ticker data: {json.dumps(data)}"}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, headers=self.headers, json=payload, timeout=15) as response:
                    if response.status == 200:
                        result = await response.json()
                        content = result['choices'][0]['message']['content']
                        return json.loads(content)
                    else:
                        error_text = await response.text()
                        print(f"Groq API Error: {response.status} - {error_text}")
        except Exception as e:
            print(f"Groq Circuit Breaker Triggered: {e}")

        # Default Neutral Signal (Circuit Breaker)
        return {
            "decision": "HOLD",
            "confidence": 0,
            "smi_commentary": "Signal unavailable (Groq Circuit Breaker Active).",
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
