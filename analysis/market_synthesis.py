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
        Generate a comprehensive executive summary.
        
        Args:
            news_data: Output from comprehensive_news.py
            market_status: General market trend data (bullish/bearish/neutral)
            macro_data: USD, Oil, Global Markets
            top_movers: Gainers/Losers list
            
        Returns:
            Dict containing 'summary_text', 'strategy', 'mood_score', 'key_driver'
        """
        
        # 1. Analyze Components
        sentiment_score = news_data.get('overall_sentiment', 0)
        sentiment_label = news_data.get('sentiment_label', 'Neutral')
        
        # Determine Market Pulse (Synthetic Score -10 to 10)
        # Factor 1: News Sentiment (Weight 40%)
        pulse_score = sentiment_score * 40  # -0.5 to 0.5 -> -20 to 20? normalize to 10 scale
        # Normalize: sentiment is usually -0.5 to 0.5. * 20 = -10 to 10.
        
        # Factor 2: Macro Headwinds (Weight 30%)
        # If USD is rising, negative. If Oil is stable, neutral.
        macro_score = 0
        if macro_data.get('usd_change', 0) > 0.5: macro_score -= 2
        if macro_data.get('oil_change', 0) > 1.0: macro_score -= 2 # Bad for most sectors (except E&P)
        elif macro_data.get('oil_change', 0) < -1.0: macro_score += 1 # Good for circular debt?
        
        # Factor 3: Market Width/Breadth (Weight 30%)
        # In hourly, we approximate this by gainer/loser ratio in top movers or general trend
        gainers = len(top_movers.get('gainers', []))
        losers = len(top_movers.get('losers', []))
        breadth_score = (gainers - losers) # Simple diff
        
        total_score = (sentiment_score * 10) + macro_score + (breadth_score * 0.5)
        
        # 2. Determine Narrative
        narrative = []
        driver = "General Trading"
        
        # Case A: Divergence (Good News, Bad Price)
        if sentiment_score > 0.2 and breadth_score < -2:
            narrative.append("Market is ignoring positive news, indicating potential exhaustion or smart money booking profits.")
            driver = "Profit Taking / Technical Weakness"
            strategy = "CAUTION: Sell on Strength"
            
        # Case B: Panic (Bad News, Bad Price)
        elif sentiment_score < -0.2 and breadth_score < -2:
            narrative.append("Bearish sentiment is dominating due to negative headlines, leading to broad-based selling.")
            driver = "Panic Selling"
            strategy = "DEFENSIVE: Wait for Support"
            
        # Case C: Momentum (Good News, Good Price)
        elif sentiment_score > 0.1 and breadth_score > 2:
            narrative.append("Strong buying momentum supported by positive news flow.")
            driver = "Bullish Momentum"
            strategy = "AGGRESSIVE: Buy Breakouts"
            
        # Case D: Mixed/Choppy
        else:
            narrative.append("Market is range-bound with mixed signals.")
            driver = "Consolidation"
            strategy = "NEUTRAL: Focus on Stock-Specific Plays"
            
        # Add Macro Context
        if macro_data.get('usd_pkr', 0) > 285:
            narrative.append("Currency weakness remains a localized pressure point.")
        
        # 3. Construct Output
        summary = {
            'headline': f"{driver}: {strategy}",
            'narrative': " ".join(narrative),
            'strategy': strategy,
            'score': round(total_score, 1),
            'driver': driver
        }
        
        return summary

    def get_html_summary(self, summary_data: Dict) -> str:
        """Format the summary as a beautiful HTML block"""
        
        color = '#00d26a' if 'Buy' in summary_data['strategy'] else \
                '#ff4757' if 'Sell' in summary_data['strategy'] or 'Wait' in summary_data['strategy'] else \
                '#ffa502'
                
        return f"""
        <div style="background-color: #0d1117; border: 1px solid {color}; border-radius: 6px; padding: 20px; margin: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h2 style="color: {color}; margin: 0; font-size: 20px;">🚀 EXECUTIVE SUMMARY</h2>
                <span style="background: {color}20; color: {color}; padding: 4px 10px; border-radius: 12px; font-size: 12px; border: 1px solid {color};">
                    {summary_data['strategy']}
                </span>
            </div>
            
            <p style="color: #e6edf3; font-size: 14px; line-height: 1.6; margin: 0 0 15px 0;">
                {summary_data['narrative']}
            </p>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; border-top: 1px solid #30363d; padding-top: 15px;">
                <div>
                    <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Primary Driver</div>
                    <div style="color: #c9d1d9; font-weight: 600;">{summary_data['driver']}</div>
                </div>
                <div>
                    <div style="color: #8b949e; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px;">Market Pulse Score</div>
                    <div style="color: {color}; font-weight: 600;">{summary_data['score']}/10</div>
                </div>
            </div>
        </div>
        """

# Singleton
market_brain = MarketSynthesizer()
