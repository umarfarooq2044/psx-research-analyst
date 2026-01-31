"""
PSX Research Analyst - Sentiment Analysis
Analyzes news headlines and announcements for sentiment
"""
import re
from typing import List, Dict, Optional
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import POSITIVE_KEYWORDS, NEGATIVE_KEYWORDS, KEYWORD_BOOST, KEYWORD_PENALTY
from database.db_manager import db

# Try to import NLTK VADER
try:
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    
    # Download VADER lexicon if not present
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        print("Downloading VADER lexicon...")
        nltk.download('vader_lexicon', quiet=True)
    
    VADER_AVAILABLE = True
    sia = SentimentIntensityAnalyzer()
except ImportError:
    print("NLTK not available. Using keyword-based sentiment analysis.")
    VADER_AVAILABLE = False
    sia = None


def clean_text(text: str) -> str:
    """
    Clean and normalize text for sentiment analysis
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+', '', text)
    
    # Remove special characters but keep spaces
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text


def analyze_sentiment_vader(text: str) -> float:
    """
    Analyze sentiment using VADER
    Returns compound score (-1 to 1)
    """
    if not VADER_AVAILABLE or not sia:
        return analyze_sentiment_keywords(text)
    
    cleaned = clean_text(text)
    if not cleaned:
        return 0.0
    
    scores = sia.polarity_scores(cleaned)
    return scores['compound']


def analyze_sentiment_keywords(text: str) -> float:
    """
    Simple keyword-based sentiment analysis
    Returns score (-1 to 1)
    """
    cleaned = clean_text(text)
    if not cleaned:
        return 0.0
    
    words = cleaned.split()
    
    positive_count = sum(1 for word in words if word in POSITIVE_KEYWORDS)
    negative_count = sum(1 for word in words if word in NEGATIVE_KEYWORDS)
    
    total = positive_count + negative_count
    if total == 0:
        return 0.0
    
    # Calculate score
    score = (positive_count - negative_count) / total
    return score


def apply_keyword_boost(text: str, base_score: float) -> float:
    """
    Apply boost/penalty for financial keywords
    """
    cleaned = clean_text(text)
    
    # Check for positive keywords
    positive_found = any(kw in cleaned for kw in POSITIVE_KEYWORDS)
    negative_found = any(kw in cleaned for kw in NEGATIVE_KEYWORDS)
    
    boosted_score = base_score
    
    if positive_found:
        boosted_score += KEYWORD_BOOST
    if negative_found:
        boosted_score += KEYWORD_PENALTY
    
    # Clamp to -1 to 1 range
    return max(-1, min(1, boosted_score))


def analyze_sentiment(text: str) -> float:
    """
    Main sentiment analysis function
    Returns score from -1 (very negative) to 1 (very positive)
    """
    if not text:
        return 0.0
    
    # Get base VADER score
    base_score = analyze_sentiment_vader(text)
    
    # Apply keyword boost for financial terms
    final_score = apply_keyword_boost(text, base_score)
    
    return round(final_score, 3)


def analyze_announcements_sentiment(symbol: str = None) -> List[Dict]:
    """
    Analyze sentiment for all unprocessed announcements
    Optionally filter by symbol
    """
    announcements = db.get_unprocessed_announcements()
    
    if symbol:
        announcements = [a for a in announcements if a['symbol'] == symbol]
    
    results = []
    
    for ann in announcements:
        # Combine headline and content for analysis
        text = ann.get('headline', '')
        if ann.get('content'):
            text += ' ' + ann['content']
        
        sentiment = analyze_sentiment(text)
        
        # Update database
        db.update_announcement_sentiment(ann['id'], sentiment)
        
        results.append({
            'id': ann['id'],
            'symbol': ann['symbol'],
            'headline': ann['headline'],
            'sentiment': sentiment
        })
    
    return results


def analyze_all_announcements() -> List[Dict]:
    """
    Analyze sentiment for all unprocessed announcements
    Wrapper function for use by scheduler
    """
    return analyze_announcements_sentiment(symbol=None)


def get_ticker_sentiment(symbol: str, days: int = 7) -> Dict:
    """
    Get aggregated sentiment for a ticker based on recent announcements
    """
    announcements = db.get_recent_announcements(symbol=symbol, days=days)
    
    if not announcements:
        return {
            'symbol': symbol,
            'sentiment_score': 0,
            'announcement_count': 0,
            'positive_count': 0,
            'negative_count': 0,
            'neutral_count': 0,
            'latest_headlines': []
        }
    
    sentiments = []
    positive = 0
    negative = 0
    neutral = 0
    headlines = []
    
    for ann in announcements:
        score = ann.get('sentiment_score')
        
        # If not processed, analyze now
        if score is None:
            text = ann.get('headline', '')
            score = analyze_sentiment(text)
            db.update_announcement_sentiment(ann['id'], score)
        
        sentiments.append(score)
        headlines.append({
            'headline': ann['headline'],
            'sentiment': score,
            'date': ann.get('announcement_date')
        })
        
        if score > 0.1:
            positive += 1
        elif score < -0.1:
            negative += 1
        else:
            neutral += 1
    
    # Calculate weighted average (more recent = higher weight)
    if sentiments:
        # Weight formula: most recent gets weight = n, oldest gets weight = 1
        weights = list(range(len(sentiments), 0, -1))
        weighted_sum = sum(s * w for s, w in zip(sentiments, weights))
        avg_sentiment = weighted_sum / sum(weights)
    else:
        avg_sentiment = 0
    
    return {
        'symbol': symbol,
        'sentiment_score': round(avg_sentiment, 3),
        'announcement_count': len(announcements),
        'positive_count': positive,
        'negative_count': negative,
        'neutral_count': neutral,
        'latest_headlines': headlines[:5]  # Top 5 most recent
    }


def get_sentiment_score_component(sentiment_data: Dict) -> int:
    """
    Convert sentiment data to a score (0-5)
    """
    score = sentiment_data.get('sentiment_score', 0)
    
    if score > 0.5:
        return 5  # Very positive
    elif score > 0.2:
        return 4  # Positive
    elif score > -0.2:
        return 3  # Neutral
    elif score > -0.5:
        return 2  # Negative
    else:
        return 1  # Very negative


def interpret_sentiment(score: float) -> str:
    """
    Convert sentiment score to human-readable interpretation
    """
    if score > 0.5:
        return "Very Positive"
    elif score > 0.2:
        return "Positive"
    elif score > -0.2:
        return "Neutral"
    elif score > -0.5:
        return "Negative"
    else:
        return "Very Negative"


if __name__ == "__main__":
    # Test sentiment analysis
    test_headlines = [
        "Company announces 25% cash dividend and bonus shares",
        "Quarterly profits increase by 50% year over year",
        "Company faces investigation by regulatory authority",
        "Board of directors meeting scheduled for next week",
        "Record oil discovery in new exploration block",
        "Company defaults on loan payments, faces bankruptcy"
    ]
    
    print("Testing sentiment analysis:\n")
    for headline in test_headlines:
        score = analyze_sentiment(headline)
        interpretation = interpret_sentiment(score)
        print(f"  '{headline[:50]}...'")
        print(f"    Score: {score:.3f} ({interpretation})\n")
