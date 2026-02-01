import os
import google.generativeai as genai
import json
from typing import List, Dict, Optional
import time
from ai_engine.feedback_loop import alpha_loop
from utils.resilience import retry_with_backoff

class GeminiAnalyst:
    """
    The Cognitive Decision Engine powered by Gemini 1.5 Pro.
    Self-Correcting via AlphaLoop.
    """
    
    BASE_INSTRUCTION = """
    You are the "Cognitive Decision Engine" for an advanced algorithmic trading system focused on the Pakistan Stock Exchange (PSX). 
    You have 20+ years of institutional experience.
    
    YOUR TASK:
    Perform a "Synthesized Decision Wrap." Do not just repeat numbers. You must "think" like a human expert.
    
    1. The Nuance Filter: If a stock has a low P/E but the news shows a looming tax hike (e.g., 'Super Tax'), downgrade the signal.
    2. The Volume Context: Correlate news sentiment spikes with price volume. Is the news driving the move, or is it noise?
    3. The PSX Reality: Factor in Pakistan risks: FX volatility, circular debt, and T-Bill auction results.
    
    OUTPUT FORMAT:
    Return a pure JSON list of objects. Do not use Markdown backticks.
    [
        {
            "ticker": "SYMBOL",
            "score": -100 to +100,
            "action": "BUY | SELL | WAIT | AVOID",
            "conviction": "High | Medium | Low",
            "reasoning": "A 2-sentence expert justification.",
            "catalyst": "Specific event in next 7 days"
        }
    ]
    """

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found. AI features will be disabled.")
            self.model = None
            return
            
        genai.configure(api_key=api_key)
        
        # Load Institutional Wisdom (In-Context Learning)
        lessons = alpha_loop.load_lessons()
        system_prompt = f"{self.BASE_INSTRUCTION}\n\nINSTITUTIONAL MEMORY & LESSONS LEARNED:\n{lessons}"
        
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        
    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def analyze_market_batch(self, payload: str) -> List[Dict]:
        """
        Send a massive batch of financial/news data to Gemini.
        """
        if not self.model:
            return []
            
        try:
            print("🧠 sending payload to Gemini Cognitive Engine...")
            response = self.model.generate_content(payload)
            
            # Parse JSON
            try:
                decisions = json.loads(response.text)
                return decisions
            except json.JSONDecodeError:
                # Retry or cleanup
                clean_text = response.text.replace('```json', '').replace('```', '')
                return json.loads(clean_text)
                
        except Exception as e:
            print(f"❌ AI Analysis Failed: {e}")
            raise # Let retry logic handle it

# Singleton
ai_analyst = GeminiAnalyst()
