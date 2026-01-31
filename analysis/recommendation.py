"""
PSX Research Analyst - Recommendation Engine
Combines technical and sentiment analysis to generate buy/sell recommendations
"""
from typing import List, Dict, Optional
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import (
    STRONG_BUY_THRESHOLD, MODERATE_BUY_THRESHOLD, SELL_THRESHOLD,
    RSI_OVERSOLD, RSI_OVERBOUGHT, VOLUME_SPIKE_MULTIPLIER,
    WATCHLIST
)
from database.db_manager import db
from analysis.technical import analyze_ticker_technical, get_technical_score
from analysis.sentiment import get_ticker_sentiment, get_sentiment_score_component


def calculate_buy_score(technical: Dict, sentiment: Dict) -> int:
    """
    Calculate overall Buy Score (1-10)
    
    Scoring Logic:
    - Technical Score: 0-5 points
    - Sentiment Score: 0-5 points
    - Total: 1-10 scale
    
    STRONG BUY (8-10): Positive News + Volume Spike + RSI < 40
    MODERATE BUY (5-7): Neutral/Positive + Normal volume
    SELL/AVOID (1-4): Negative News + RSI > 70 + Below Support
    """
    if not technical:
        technical = {}
    if not sentiment:
        sentiment = {}
    
    # Base scores
    tech_score = get_technical_score(technical)  # 0-5
    sent_score = get_sentiment_score_component(sentiment)  # 0-5
    
    # Start with sum of components
    base_score = tech_score + sent_score  # 0-10
    
    # Apply bonuses and penalties
    bonus = 0
    penalty = 0
    
    # === STRONG BUY CONDITIONS ===
    
    # Condition 1: Positive sentiment + Volume spike + RSI oversold
    rsi = technical.get('rsi')
    volume_spike = technical.get('volume_spike', False)
    sent_value = sentiment.get('sentiment_score', 0)
    
    if (sent_value > 0.2 and  # Positive news
        volume_spike and  # Volume spike
        rsi and rsi < RSI_OVERSOLD):  # Oversold
        bonus += 2  # Strong signal
    
    # Condition 2: Very positive news (dividend, bonus announcement)
    if sent_value > 0.5:
        bonus += 1
    
    # Condition 3: Near 52W low but holding support
    sr = technical.get('support_resistance', {})
    if sr.get('near_support') and not sr.get('below_support'):
        bonus += 1
    
    # === SELL/AVOID CONDITIONS ===
    
    # Condition 1: Negative news + RSI overbought
    if (sent_value < -0.2 and  # Negative news
        rsi and rsi > RSI_OVERBOUGHT):  # Overbought
        penalty += 2
    
    # Condition 2: Broke 52W support
    if sr.get('below_support'):
        penalty += 2
    
    # Condition 3: Very negative news
    if sent_value < -0.5:
        penalty += 1
    
    # Calculate final score
    final_score = base_score + bonus - penalty
    
    # Clamp to 1-10 range
    return max(1, min(10, final_score))


def get_recommendation(buy_score: int) -> str:
    """
    Convert buy score to recommendation text
    """
    if buy_score >= STRONG_BUY_THRESHOLD:
        return "STRONG BUY"
    elif buy_score >= MODERATE_BUY_THRESHOLD:
        return "BUY"
    elif buy_score >= SELL_THRESHOLD:
        return "HOLD"
    else:
        return "SELL/AVOID"


def get_recommendation_color(recommendation: str) -> str:
    """
    Get color code for recommendation
    """
    colors = {
        "STRONG BUY": "#00C851",  # Green
        "BUY": "#33b5e5",  # Blue
        "HOLD": "#ffbb33",  # Orange
        "SELL/AVOID": "#ff4444"  # Red
    }
    return colors.get(recommendation, "#666666")


def generate_analysis_notes(technical: Dict, sentiment: Dict, buy_score: int) -> str:
    """
    Generate human-readable notes explaining the recommendation
    """
    notes = []
    
    if not technical:
        notes.append("Limited technical data available.")
        return " ".join(notes)
    
    rsi = technical.get('rsi')
    volume_spike = technical.get('volume_spike')
    sr = technical.get('support_resistance', {})
    sent_score = sentiment.get('sentiment_score', 0)
    ann_count = sentiment.get('announcement_count', 0)
    
    # Technical notes
    if rsi:
        if rsi < 30:
            notes.append(f"Deeply oversold (RSI {rsi:.1f}).")
        elif rsi < RSI_OVERSOLD:
            notes.append(f"Oversold territory (RSI {rsi:.1f}).")
        elif rsi > 80:
            notes.append(f"Extremely overbought (RSI {rsi:.1f}).")
        elif rsi > RSI_OVERBOUGHT:
            notes.append(f"Overbought territory (RSI {rsi:.1f}).")
    
    if volume_spike:
        ratio = technical.get('volume_ratio', 0)
        notes.append(f"Volume spike detected ({ratio:.1f}x average).")
    
    if sr.get('below_support'):
        notes.append("⚠️ Price broke below 52-week support!")
    elif sr.get('near_support'):
        notes.append("Near 52-week low support level.")
    elif sr.get('near_resistance'):
        notes.append("Approaching 52-week high resistance.")
    
    # Sentiment notes
    if ann_count > 0:
        if sent_score > 0.3:
            notes.append(f"Positive news flow ({ann_count} recent announcements).")
        elif sent_score < -0.3:
            notes.append(f"Negative news sentiment ({ann_count} recent announcements).")
    else:
        notes.append("No recent company announcements.")
    
    # Overall recommendation note
    if buy_score >= 9:
        notes.append("Multiple bullish signals align. Strong opportunity.")
    elif buy_score >= 7:
        notes.append("Favorable conditions for entry.")
    elif buy_score <= 3:
        notes.append("Caution advised. Consider reducing exposure.")
    
    return " ".join(notes)


def analyze_ticker(symbol: str) -> Optional[Dict]:
    """
    Perform complete analysis for a single ticker
    """
    # Get technical analysis
    technical = analyze_ticker_technical(symbol)
    
    # Get sentiment analysis
    sentiment = get_ticker_sentiment(symbol, days=7)
    
    # Calculate buy score
    buy_score = calculate_buy_score(technical, sentiment)
    
    # Get recommendation
    recommendation = get_recommendation(buy_score)
    
    # Generate notes
    notes = generate_analysis_notes(technical, sentiment, buy_score)
    
    # Get ticker info
    ticker_info = db.get_ticker(symbol)
    
    result = {
        'symbol': symbol,
        'name': ticker_info.get('name', symbol) if ticker_info else symbol,
        'buy_score': buy_score,
        'recommendation': recommendation,
        'recommendation_color': get_recommendation_color(recommendation),
        'notes': notes,
        'technical': technical or {},
        'sentiment': sentiment,
        'analyzed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Save to database
    today = datetime.now().strftime('%Y-%m-%d')
    db.save_analysis(
        symbol=symbol,
        date=today,
        rsi=technical.get('rsi') if technical else None,
        volume_spike=technical.get('volume_spike', False) if technical else False,
        sentiment_score=sentiment.get('sentiment_score'),
        buy_score=buy_score,
        recommendation=recommendation,
        notes=notes
    )
    
    return result


def analyze_all_tickers(symbols: List[str], show_progress: bool = True) -> List[Dict]:
    """
    Analyze all given tickers
    """
    from tqdm import tqdm
    
    results = []
    iterator = tqdm(symbols, desc="Analyzing tickers") if show_progress else symbols
    
    for symbol in iterator:
        try:
            result = analyze_ticker(symbol)
            if result:
                results.append(result)
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
    
    # Sort by buy score descending
    results.sort(key=lambda x: x['buy_score'], reverse=True)
    
    return results


def get_top_opportunities(limit: int = 5) -> List[Dict]:
    """
    Get top buy opportunities from today's analysis
    """
    return db.get_top_opportunities(limit=limit)


def get_red_alerts(threshold: int = SELL_THRESHOLD) -> List[Dict]:
    """
    Get stocks with sell signals
    """
    return db.get_red_alerts(threshold=threshold)


def get_watchlist_status() -> List[Dict]:
    """
    Get analysis status for watchlist stocks
    """
    results = []
    
    for symbol in WATCHLIST:
        analysis = analyze_ticker(symbol)
        if analysis:
            results.append(analysis)
    
    return results


if __name__ == "__main__":
    # Test recommendation engine
    print("Testing Recommendation Engine\n")
    
    # Test with sample scenarios
    test_cases = [
        {
            'name': 'Strong Buy Scenario',
            'technical': {'rsi': 35, 'volume_spike': True, 'volume_ratio': 3.0,
                         'support_resistance': {'near_support': True, 'below_support': False}},
            'sentiment': {'sentiment_score': 0.6, 'announcement_count': 3}
        },
        {
            'name': 'Sell Scenario',
            'technical': {'rsi': 78, 'volume_spike': False, 'volume_ratio': 0.8,
                         'support_resistance': {'below_support': True}},
            'sentiment': {'sentiment_score': -0.4, 'announcement_count': 2}
        },
        {
            'name': 'Neutral Scenario',
            'technical': {'rsi': 52, 'volume_spike': False, 'volume_ratio': 1.1,
                         'support_resistance': {}},
            'sentiment': {'sentiment_score': 0.1, 'announcement_count': 1}
        }
    ]
    
    for case in test_cases:
        score = calculate_buy_score(case['technical'], case['sentiment'])
        rec = get_recommendation(score)
        notes = generate_analysis_notes(case['technical'], case['sentiment'], score)
        
        print(f"{case['name']}:")
        print(f"  Buy Score: {score}/10")
        print(f"  Recommendation: {rec}")
        print(f"  Notes: {notes}\n")
