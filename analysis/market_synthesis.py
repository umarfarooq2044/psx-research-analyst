from datetime import datetime
from typing import Dict, List, Optional

class MarketSynthesizer:
    """
    The 'Analyst Brain' of the system.
    Synthesizes News, Technicals, and Macro data into a coherent narrative
    and actionable recommendations.
    """

    def __init__(self):
        pass

    def generate_synthesis(self, 
                          news_data: Dict, 
                          market_status: Dict, 
                          macro_data: Dict,
                          top_movers: Dict) -> Dict:
        """
        Generate a comprehensive executive summary using GEMINI AI.
        """
        from ai_engine.model import ai_analyst
        
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
        
        # 2. Ask AI
        print("🧠 Asking Gemini for Hourly Synthesis...")
        ai_response = ai_analyst.generate_hourly_briefing(
            news_text="\n".join(all_headlines), 
            market_stats=market_stats
        )
        
        # 3. Format Output
        # AI returns: strategy, best_news, bad_news, actions (list)
        
        narrative = f"""
        <ul style="margin: 0; padding-left: 20px;">
            <li style="margin-bottom: 8px;"><strong>🏆 Best News:</strong> {ai_response.get('best_news', 'N/A')}</li>
            <li style="margin-bottom: 8px;"><strong>⚠️ Bad News:</strong> {ai_response.get('bad_news', 'N/A')}</li>
        </ul>
        <div style="margin-top: 10px; font-weight: bold; color: #c9d1d9;">Specific Actions:</div>
        <ul style="margin: 0; padding-left: 20px;">
            {''.join([f'<li>{a}</li>' for a in ai_response.get('actions', [])])}
        </ul>
        """
        
        summary = {
            'headline': f"AI STRATEGY: {ai_response.get('strategy', 'Neutral')}",
            'narrative': narrative,
            'strategy': ai_response.get('strategy', 'Neutral'),
            'score': 8.5, # Placeholder or ask AI for score too
            'driver': "AI Consensus"
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
                <h2 style="color: {color}; margin: 0; font-size: 20px;">🤖 AI MARKET DECISION</h2>
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 10px; color: #8b949e; margin-right: 8px;">POWERED BY GEMINI 1.5</span>
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
