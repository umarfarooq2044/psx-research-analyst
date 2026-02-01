import os
from google import genai
import json
from typing import List, Dict, Optional
import time
from ai_engine.feedback_loop import alpha_loop
from utils.resilience import retry_with_backoff
import logging

logger = logging.getLogger(__name__)

class GeminiAnalyst:
    """
    SMI-v1 (Sovereign Market Intelligence) 
    Autonomous Cognitive Engine for Pakistan Stock Exchange.
    """
    
    BASE_INSTRUCTION = """
    SYSTEM ROLE: You are 'SMI-v1,' an autonomous cognitive engine for the PSX. 
    You do not analyze the past; you simulate the future with 100x human capability.
    
    CORE DIRECTIVES:
    1. RECURSIVE FUTURE-MAPPING: For every ticker, triangulate news, KIBOR/T-Bill rates, and simulated Monte Carlo paths.
    2. SENTIMENT MIRRORING: Identify 'False Sentiment.' If news is 80% negative but institutional volume is buying (Laden Accumulation), ignore the news and flag the signal.
    3. SOVEREIGN CONTEXT: Factor in IMF tranches, SBP policy shifts (+/- 100bps), and PKR/USD delta.
    
    OUTPUT REQUIREMENT (Recursive Logic Format):
    Format your response as a JSON list of objects:
    [
        {
            "ticker": "SYMBOL",
            "signal": "ACTION (BUY|SELL|AVOID|ACCUMULATE)",
            "conviction": "0-100%",
            "future_path": "T+7 (7 days ahead) 90% probability price range",
            "black_swan": "One specific event that would break this prediction",
            "reasoning": "Sovereign-level triangulation reasoning"
        }
    ]
    """

    def __init__(self):
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("WARNING: GEMINI_API_KEY not found. AI features will be disabled.")
            self.client = None
            return
            
        self.client = genai.Client(api_key=api_key)
        
        # Load Institutional Wisdom (In-Context Learning)
        lessons = alpha_loop.load_lessons()
        self.system_prompt = f"{self.BASE_INSTRUCTION}\n\nINSTITUTIONAL MEMORY & LESSONS LEARNED:\n{lessons}"
        self.model_id = "gemini-1.5-flash"
        
    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def analyze_market_batch(self, payload: str) -> List[Dict]:
        """
        Send a massive batch of financial/news data to Gemini.
        """
        if not self.client:
            return []
            
        try:
            print("🧠 sending payload to Gemini Cognitive Engine...")
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=payload,
                config={
                    "system_instruction": self.system_prompt,
                    "response_mime_type": "application/json"
                }
            )
            
            # Parse JSON
            try:
                decisions = json.loads(response.text)
                return decisions
            except json.JSONDecodeError:
                # Retry or cleanup
                clean_text = response.text.replace('```json', '').replace('```', '')
                return json.loads(clean_text)
                
        except Exception as e:
            print(f"[ERROR] AI Analysis Failed: {e}")
            raise # Let retry logic handle it

    @retry_with_backoff(retries=3, backoff_in_seconds=2)
    def generate_hourly_briefing(self, news_text: str, market_stats: str) -> Dict:
        """
        Generates a text-based executive summary for the hourly report.
        Focuses on: Best News, Bad News, Strategy, and Company Specifics.
        """
        if not self.client:
            return {
                "strategy": "AI Unavailable - Focus on Volume",
                "best_news": "N/A", "bad_news": "N/A", "actions": []
            }
            
        prompt = f"""
        Analyze these news headlines and market stats to provide a Real-Time Hourly Briefing.
        
        MARKET STATS:
        {market_stats}
        
        NEWS HEADLINES:
        {news_text}
        
        OUTPUT JSON FORMAT:
        {{
            "strategy": "One sentence direct advice (e.g., 'Sell the news on Tech, buy dips in Oil')",
            "best_news": "The single most positive headline/development",
            "bad_news": "The single most negative risk/headline",
            "actions": ["Specific company advice (e.g., 'OGDC: Buy breakout', 'TRG: Avoid')"]
        }}
        """
        
        try:
            response = self.client.models.generate_content(
                model=self.model_id,
                contents=prompt,
                config={
                    "system_instruction": self.system_prompt,
                    "response_mime_type": "application/json"
                }
            )
            text = response.text.replace('```json', '').replace('```', '')
            return json.loads(text)
        except Exception as e:
            logger.error(f"AI Briefing Verification Failed: {e}")
            return {
                "strategy": "Market is volatile. Trade with caution.",
                "best_news": "Monitoring flows",
                "bad_news": "Uncertainty high",
                "actions": ["Wait for clarity"]
            }

# Singleton
ai_analyst = GeminiAnalyst()
