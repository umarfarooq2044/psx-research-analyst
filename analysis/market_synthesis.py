from datetime import datetime
from typing import Dict, List, Optional
import asyncio

class MarketSynthesizer:
    """
    The 'Analyst Brain' of the system.
    Synthesizes News, Technicals, and Macro data into a coherent narrative
    and actionable recommendations.
    """

    def __init__(self):
        pass

    async def generate_synthesis(self, 
                          news_data: Dict, 
                          market_status: Dict, 
                          macro_data: Dict,
                          top_movers: Dict) -> Dict:
        """
        Generate a comprehensive executive summary using Groq (Llama-3.3-70b).
        """
        from ai_engine.ai_decision import GroqBrain
        brain = GroqBrain()
        
        # Determine current loop: is this for the overall market or a specific ticker?
        # If we have many tickers, we might want a market-level synthesis.
        
        # 1. Prepare Context for AI
        # Flatten news for prompt
        all_headlines = []
        for cat in ['national', 'international', 'announcements']:
            for item in news_data.get(cat, [])[:5]:
                all_headlines.append(f"- [{cat.upper()}] {item['headline']}")
        
        market_stats = f"""
        USD/PKR: {macro_data.get('usd_pkr', 'N/A')}
        Oil: {macro_data.get('oil', 'N/A')}
        Sentiment Score: {news_data.get('overall_sentiment', 0)}
        """
        
        # 2. Ask AI (Market Level Context)
        print("🧠 Asking Groq (Llama-3.3-70b) for Hourly Synthesis...")
        
        # We'll use a slightly different approach for the general synthesis
        # since GroqBrain is tuned for per-ticker decisions by default.
        # But we can override the data to be a market summary.
        market_summary_data = {
            "Symbol": "KSE-100",
            "News_Summary": news_data.get('sentiment_label', 'Neutral'),
            "Macro": market_stats,
            "National_Headlines": all_headlines[:10]
        }
        
        # Use await instead of run_until_complete
        ai_response = await brain.get_decision(market_summary_data)
        
        # 3. Format Output
        # Groq returns: decision, confidence, smi_commentary, psx_risk_flag
        
        narrative = f"""
        <ul style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 8px;"><strong>⚠️ SMI Commentary:</strong> {ai_response.get('smi_commentary', 'N/A')}</li>
            <li style="margin-bottom: 8px;"><strong>🛡️ Risk Flag:</strong> {ai_response.get('psx_risk_flag', 'Safe')}</li>
            <li style="margin-bottom: 8px;"><strong>💎 Confidence:</strong> {ai_response.get('confidence', 0)}%</li>
        </ul>
        """
        
        summary = {
            'headline': f"SMI-v1 COGNITIVE SIGNAL: {ai_response.get('decision', 'HOLD')}",
            'narrative': narrative,
            'strategy': ai_response.get('decision', 'HOLD'),
            'score': ai_response.get('confidence', 50),
            'commentary': ai_response.get('smi_commentary', 'N/A'),
            'risk_flag': ai_response.get('psx_risk_flag', 'Safe'),
            'driver': "Groq Llama-3.3-70b"
        }
        
        return summary

    def get_html_summary(self, summary_data: Dict) -> str:
        """Format the summary as a beautiful HTML block"""
        
        color = '#00d26a' # Default green
        if 'Sell' in summary_data['strategy'] or 'Caution' in summary_data['strategy']:
            color = '#ff4757'
        elif 'Wait' in summary_data['strategy']:
            color = '#ffa502'
                
        return f"""
        <div style="background-color: #0d1117; border: 1px solid {color}; border-radius: 6px; padding: 20px; margin: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h2 style="color: {color}; margin: 0; font-size: 20px;">🦅 SMI-v1 COGNITIVE SIGNAL</h2>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 10px; color: #8b949e; margin-right: 8px;">POWERED BY GROQ (Llama-3.3-70b)</span>
                    <span style="background: {color}20; color: {color}; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid {color};">
                        {summary_data['strategy']}
                    </span>
                </div>
            </div>
            
            <div style="color: #e6edf3; font-size: 14px; line-height: 1.6;">
                {summary_data['narrative']}
            </div>
        </div>
        """

# Singleton
market_brain = MarketSynthesizer()
