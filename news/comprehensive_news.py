"""
PSX Research Analyst - Comprehensive Real-Time News Scraper
============================================================
Scrapes news from multiple Pakistani and international sources
that can affect the Pakistan Stock Exchange.

Uses RSS Feeds for reliability where available.

Sources:
- Pakistani: DAWN, Business Recorder, Express Tribune, The News (via RSS)
- International: Reuters, MarketWatch, Investing.com (via RSS/Scraping)
- PSX: Official Notices (via Scraping)
"""

import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict
import feedparser
import time
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Fix Windows console encoding for emoji support
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Initialize sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()


class ComprehensiveNewsScraper:
    """
    Multi-source news scraper for PSX market intelligence.
    Uses RSS feeds for stability and speed.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def _parse_feed(self, url: str, source: str, category: str = 'national', limit: int = 10) -> List[Dict]:
        """Helper to parse RSS feeds"""
        news = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:limit]:
                title = entry.title
                link = entry.link
                
                # Calculate sentiment
                sentiment = sentiment_analyzer.polarity_scores(title)
                
                news.append({
                    'headline': title,
                    'source': source,
                    'url': link,
                    'sentiment': sentiment['compound'],
                    'category': category,
                    'timestamp': datetime.now().isoformat()
                })
        except Exception as e:
            print(f"RSS Error ({source}): {e}")
        return news

    # =========================================================================
    # PAKISTANI NEWS SOURCES (RSS)
    # =========================================================================
    
    def scrape_dawn_business(self) -> List[Dict]:
        return self._parse_feed("https://www.dawn.com/feeds/business", "DAWN Business")
    
    def scrape_business_recorder(self) -> List[Dict]:
        return self._parse_feed("https://www.brecorder.com/feeds/business-economy", "Business Recorder")
    
    def scrape_express_tribune(self) -> List[Dict]:
        return self._parse_feed("https://tribune.com.pk/feed/business", "Express Tribune")
    
    def scrape_the_news(self) -> List[Dict]:
        return self._parse_feed("https://www.thenews.com.pk/rss/1/10", "The News")
    
    # =========================================================================
    # INTERNATIONAL NEWS SOURCES (RSS/Scraping)
    # =========================================================================
    
    def scrape_reuters_markets(self) -> List[Dict]:
        """Scrape Reuters Markets (Scraping as RSS is limited)"""
        news = []
        try:
            url = "https://www.reuters.com/markets/"
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Try generic selectors for Reuters structure
                articles = soup.select('h3[data-testid="Heading"], h3 a') 
                
                for article in articles[:10]:
                    title = article.get_text(strip=True)
                    if not title: continue
                    
                    if article.name == 'a':
                        href = article.get('href', '')
                    else:
                        link = article.find_parent('a')
                        href = link.get('href', '') if link else ''
                    
                    if not href: continue
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'Reuters',
                        'url': f"https://www.reuters.com{href}" if not href.startswith('http') else href,
                        'sentiment': sentiment['compound'],
                        'category': 'international',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Reuters error: {e}")
        return news
    
    def scrape_marketwatch(self) -> List[Dict]:
        return self._parse_feed("http://feeds.marketwatch.com/marketwatch/topstories/", "MarketWatch", "international")
    
    def scrape_investing_com(self) -> List[Dict]:
        return self._parse_feed("https://www.investing.com/rss/news.rss", "Investing.com", "international")
    
    # =========================================================================
    # PSX OFFICIAL ANNOUNCEMENTS
    # =========================================================================
    
    def scrape_psx_notices(self) -> List[Dict]:
        """Scrape PSX official company notices"""
        news = []
        try:
            url = "https://www.psx.com.pk/psx/exchange/market/company-notices"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            rows = soup.find_all('tr', limit=20)
            for row in rows[1:]:  # Skip header
                cols = row.find_all('td')
                if len(cols) >= 3:
                    company = cols[0].get_text(strip=True)
                    subject = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                    headline = f"{company}: {subject}"
                    sentiment = sentiment_analyzer.polarity_scores(headline)
                    
                    news.append({
                        'headline': headline,
                        'source': 'PSX Official',
                        'url': 'https://www.psx.com.pk/psx/exchange/market/company-notices',
                        'sentiment': sentiment['compound'],
                        'category': 'announcement',
                        'company': company,
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"PSX Notices error: {e}")
        return news

    def collect_all_news(self) -> Dict:
        """Collect news from all sources"""
        print("📰 Collecting news from RSS & Scrapers...")
        
        all_news = {
            'national': [],
            'international': [],
            'announcements': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Pakistani sources
        print("  → DAWN Business...")
        all_news['national'].extend(self.scrape_dawn_business())
        
        print("  → Business Recorder...")
        all_news['national'].extend(self.scrape_business_recorder())
        
        print("  → Express Tribune...")
        all_news['national'].extend(self.scrape_express_tribune())
        
        print("  → The News...")
        all_news['national'].extend(self.scrape_the_news())
        
        # International sources
        print("  → Reuters Markets...")
        all_news['international'].extend(self.scrape_reuters_markets())
        
        print("  → MarketWatch...")
        all_news['international'].extend(self.scrape_marketwatch())
        
        print("  → Investing.com...")
        all_news['international'].extend(self.scrape_investing_com())
        
        # PSX Official
        print("  → PSX Official Notices...")
        all_news['announcements'].extend(self.scrape_psx_notices())
        
        # Calculate sentiment summary
        all_headlines = all_news['national'] + all_news['international']
        if all_headlines:
            avg_sentiment = sum(h['sentiment'] for h in all_headlines) / len(all_headlines)
            all_news['overall_sentiment'] = avg_sentiment
            all_news['sentiment_label'] = (
                'Bullish' if avg_sentiment > 0.1 else
                'Bearish' if avg_sentiment < -0.1 else
                'Neutral'
            )
        
        print(f"✓ Collected {len(all_news['national'])} national + {len(all_news['international'])} international news")
        return all_news
    
    def get_market_moving_news(self) -> List[Dict]:
        """Filter news that's likely to move the market"""
        all_news = self.collect_all_news()
        
        market_moving = []
        keywords = [
            'interest rate', 'sbp', 'imf', 'budget', 'tax', 'energy', 'oil',
            'gas', 'electricity', 'rupee', 'dollar', 'inflation', 'gdp',
            'export', 'import', 'trade deficit', 'remittances', 'privatization',
            'ipo', 'dividend', 'profit', 'loss', 'result', 'quarterly',
            'merger', 'acquisition', 'investment', 'foreign', 'fdi',
            'political', 'election', 'court'
        ]
        
        for category in ['national', 'international', 'announcements']:
            for item in all_news.get(category, []):
                headline = item.get('headline', '').lower()
                if any(kw in headline for kw in keywords) or abs(item.get('sentiment', 0)) > 0.3:
                    item['market_impact'] = 'high' if abs(item.get('sentiment', 0)) > 0.5 else 'medium'
                    market_moving.append(item)
        
        return sorted(market_moving, key=lambda x: abs(x.get('sentiment', 0)), reverse=True)


# Singleton instance
news_scraper = ComprehensiveNewsScraper()


def get_all_news() -> Dict:
    return news_scraper.collect_all_news()


def get_market_moving_news() -> List[Dict]:
    return news_scraper.get_market_moving_news()


if __name__ == "__main__":
    print("=" * 60)
    print("RSS FEED NEWS TEST")
    print("=" * 60)
    
    news = get_all_news()
    
    print(f"\n📰 National News: {len(news['national'])} headlines")
    for item in news['national'][:3]:
        print(f"  • [{item['source']}] {item['headline']} ({item['sentiment']})")
    
    print(f"\n🌍 International News: {len(news['international'])} headlines")
    for item in news['international'][:3]:
        print(f"  • [{item['source']}] {item['headline']} ({item['sentiment']})")
    
    print(f"\n📢 PSX Announcements: {len(news['announcements'])} notices")
    for item in news['announcements'][:3]:
        print(f"  • {item['headline']}...")
    
    print(f"\n📊 Overall Sentiment: {news.get('sentiment_label', 'N/A')}")
