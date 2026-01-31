"""
PSX Research Analyst - News Scraper
Scrapes financial news from Pakistani news sources
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
import re
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import REQUEST_TIMEOUT, NEWS_SOURCES
from database.db_manager import db
from analysis.sentiment import analyze_sentiment


def scrape_dawn_business() -> List[Dict]:
    """
    Scrape business news from DAWN
    """
    headlines = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            "https://www.dawn.com/business",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article headlines
        articles = soup.find_all('article', limit=20)
        
        for article in articles:
            title_elem = article.find(['h2', 'h3'])
            link_elem = article.find('a', href=True)
            
            if title_elem:
                headline = title_elem.get_text(strip=True)
                url = link_elem['href'] if link_elem else None
                
                if headline:
                    headlines.append({
                        'headline': headline,
                        'url': url if url and url.startswith('http') else f"https://www.dawn.com{url}" if url else None,
                        'source': 'DAWN',
                        'category': 'business'
                    })
        
    except Exception as e:
        print(f"Error scraping DAWN: {e}")
    
    return headlines


def scrape_business_recorder() -> List[Dict]:
    """
    Scrape news from Business Recorder
    """
    headlines = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            "https://www.brecorder.com/",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find headlines
        headline_elems = soup.find_all(['h2', 'h3', 'h4'], class_=re.compile(r'title|headline', re.I), limit=20)
        
        for elem in headline_elems:
            link = elem.find('a', href=True)
            headline = elem.get_text(strip=True)
            
            if headline and len(headline) > 20:
                url = link['href'] if link else None
                headlines.append({
                    'headline': headline,
                    'url': url if url and url.startswith('http') else f"https://www.brecorder.com{url}" if url else None,
                    'source': 'Business Recorder',
                    'category': 'business'
                })
        
    except Exception as e:
        print(f"Error scraping Business Recorder: {e}")
    
    return headlines


def scrape_tribune_business() -> List[Dict]:
    """
    Scrape business news from Express Tribune
    """
    headlines = []
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(
            "https://tribune.com.pk/business",
            headers=headers,
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find article headlines
        articles = soup.find_all('article', limit=20)
        
        for article in articles:
            title_elem = article.find(['h2', 'h3', 'h4'])
            link_elem = article.find('a', href=True)
            
            if title_elem:
                headline = title_elem.get_text(strip=True)
                url = link_elem['href'] if link_elem else None
                
                if headline:
                    headlines.append({
                        'headline': headline,
                        'url': url,
                        'source': 'Express Tribune',
                        'category': 'business'
                    })
        
    except Exception as e:
        print(f"Error scraping Tribune: {e}")
    
    return headlines


def scrape_all_news() -> List[Dict]:
    """
    Scrape news from all sources
    """
    all_headlines = []
    
    print("Scraping DAWN Business...")
    all_headlines.extend(scrape_dawn_business())
    
    print("Scraping Business Recorder...")
    all_headlines.extend(scrape_business_recorder())
    
    print("Scraping Express Tribune...")
    all_headlines.extend(scrape_tribune_business())
    
    # Remove duplicates based on headline
    seen = set()
    unique_headlines = []
    for h in all_headlines:
        if h['headline'] not in seen:
            seen.add(h['headline'])
            unique_headlines.append(h)
    
    return unique_headlines


def analyze_and_save_news(headlines: List[Dict]):
    """
    Analyze sentiment and save news to database
    """
    analyzed = []
    
    for news in headlines:
        # Analyze sentiment
        sentiment = analyze_sentiment(news['headline'])
        
        # Determine impact level based on keywords
        headline_lower = news['headline'].lower()
        
        if any(kw in headline_lower for kw in ['crisis', 'crash', 'plunge', 'surge', 'record', 'breakthrough']):
            impact = 'high'
        elif any(kw in headline_lower for kw in ['rise', 'fall', 'increase', 'decrease', 'profit', 'loss']):
            impact = 'medium'
        else:
            impact = 'low'
        
        # Find related stock symbols
        related_symbols = extract_stock_mentions(news['headline'])
        
        # Save to database
        db.save_news(
            headline=news['headline'],
            source=news['source'],
            url=news.get('url'),
            category=news.get('category'),
            sentiment_score=sentiment,
            impact_level=impact,
            related_symbols=related_symbols
        )
        
        news['sentiment'] = sentiment
        news['impact'] = impact
        news['related_symbols'] = related_symbols
        analyzed.append(news)
    
    return analyzed


def extract_stock_mentions(text: str) -> List[str]:
    """
    Extract mentioned stock symbols from text
    """
    # Common company names to symbols mapping
    company_map = {
        'ogdc': 'OGDC', 'ppl': 'PPL', 'pso': 'PSO',
        'hbl': 'HBL', 'mcb': 'MCB', 'ubl': 'UBL', 'nbp': 'NBP',
        'engro': 'ENGRO', 'luck': 'LUCK', 'ffc': 'FFC',
        'pakistan state oil': 'PSO',
        'habib bank': 'HBL',
        'muslim commercial': 'MCB',
        'oil and gas': 'OGDC',
        'pakistan petroleum': 'PPL',
        'lucky cement': 'LUCK',
        'fauji fertilizer': 'FFC',
        'k-electric': 'KEL',
        'hub power': 'HUBC',
        'nestle': 'NESTLE',
        'unilever': 'UNILEVER',
        'pak suzuki': 'PSMC',
        'honda atlas': 'HCAR',
        'indus motor': 'INDU',
        'systems limited': 'SYS',
        'glaxo': 'GLAXO',
        'searle': 'SEARL'
    }
    
    text_lower = text.lower()
    found_symbols = []
    
    for keyword, symbol in company_map.items():
        if keyword in text_lower and symbol not in found_symbols:
            found_symbols.append(symbol)
    
    return found_symbols


def get_market_news_summary(limit: int = 10) -> Dict:
    """
    Get summarized news for market reports
    """
    headlines = scrape_all_news()
    analyzed = analyze_and_save_news(headlines)
    
    # Categorize by sentiment
    positive = [h for h in analyzed if h.get('sentiment', 0) > 0.1]
    negative = [h for h in analyzed if h.get('sentiment', 0) < -0.1]
    neutral = [h for h in analyzed if -0.1 <= h.get('sentiment', 0) <= 0.1]
    
    # Get high impact news
    high_impact = [h for h in analyzed if h.get('impact') == 'high']
    
    # Overall sentiment
    if len(positive) > len(negative) * 1.5:
        overall_sentiment = 'bullish'
    elif len(negative) > len(positive) * 1.5:
        overall_sentiment = 'bearish'
    else:
        overall_sentiment = 'mixed'
    
    return {
        'total_headlines': len(analyzed),
        'positive_count': len(positive),
        'negative_count': len(negative),
        'neutral_count': len(neutral),
        'high_impact_news': high_impact[:5],
        'latest_headlines': analyzed[:limit],
        'overall_sentiment': overall_sentiment
    }


if __name__ == "__main__":
    print("Testing News Scraper...")
    
    summary = get_market_news_summary(limit=10)
    
    print(f"\nTotal Headlines: {summary['total_headlines']}")
    print(f"Positive: {summary['positive_count']}")
    print(f"Negative: {summary['negative_count']}")
    print(f"Neutral: {summary['neutral_count']}")
    print(f"Overall Sentiment: {summary['overall_sentiment']}")
    
    print("\n--- High Impact News ---")
    for news in summary['high_impact_news']:
        print(f"  [{news['source']}] {news['headline'][:60]}...")
    
    print("\n--- Latest Headlines ---")
    for news in summary['latest_headlines'][:5]:
        sentiment_str = "+" if news.get('sentiment', 0) > 0 else "-" if news.get('sentiment', 0) < 0 else "~"
        print(f"  {sentiment_str} [{news['source']}] {news['headline'][:60]}...")
