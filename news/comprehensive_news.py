"""
PSX Research Analyst - Comprehensive Real-Time News Scraper
============================================================
Scrapes news from multiple Pakistani and international sources
that can affect the Pakistan Stock Exchange.

Sources:
- Pakistani: DAWN, Business Recorder, Express Tribune, The News, Geo News
- International: Reuters, MarketWatch, Investing.com
- Central Banks: SBP, Fed (via news)
- Commodities: Oil, Gold, Currency (USD/PKR)
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import time

# Initialize sentiment analyzer
sentiment_analyzer = SentimentIntensityAnalyzer()


class ComprehensiveNewsScraper:
    """
    Multi-source news scraper for PSX market intelligence.
    Covers national, international, and sector-specific news.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    # =========================================================================
    # PAKISTANI NEWS SOURCES
    # =========================================================================
    
    def scrape_dawn_business(self) -> List[Dict]:
        """Scrape DAWN Business news"""
        news = []
        try:
            url = "https://www.dawn.com/business"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('article', limit=15)
            for article in articles:
                title_elem = article.find('h2') or article.find('h3')
                if title_elem:
                    link = title_elem.find('a')
                    title = title_elem.get_text(strip=True)
                    url = link.get('href', '') if link else ''
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'DAWN Business',
                        'url': url if url.startswith('http') else f"https://www.dawn.com{url}",
                        'sentiment': sentiment['compound'],
                        'category': 'national',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"DAWN error: {e}")
        return news
    
    def scrape_business_recorder(self) -> List[Dict]:
        """Scrape Business Recorder - Pakistan's financial daily"""
        news = []
        try:
            url = "https://www.brecorder.com/business-finance"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all(['h2', 'h3', 'h4'], class_=re.compile('title|heading'), limit=15)
            for article in articles:
                link = article.find('a') or article.find_parent('a')
                if link:
                    title = article.get_text(strip=True)
                    href = link.get('href', '')
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'Business Recorder',
                        'url': href if href.startswith('http') else f"https://www.brecorder.com{href}",
                        'sentiment': sentiment['compound'],
                        'category': 'national',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Business Recorder error: {e}")
        return news
    
    def scrape_express_tribune(self) -> List[Dict]:
        """Scrape Express Tribune Business"""
        news = []
        try:
            url = "https://tribune.com.pk/business"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('h2', limit=15)
            for article in articles:
                link = article.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'Express Tribune',
                        'url': href if href.startswith('http') else f"https://tribune.com.pk{href}",
                        'sentiment': sentiment['compound'],
                        'category': 'national',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Express Tribune error: {e}")
        return news
    
    def scrape_the_news(self) -> List[Dict]:
        """Scrape The News International Business"""
        news = []
        try:
            url = "https://www.thenews.com.pk/latest/category/business"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('h2', limit=15)
            for article in articles:
                link = article.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'The News',
                        'url': href,
                        'sentiment': sentiment['compound'],
                        'category': 'national',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"The News error: {e}")
        return news
    
    # =========================================================================
    # INTERNATIONAL NEWS SOURCES
    # =========================================================================
    
    def scrape_reuters_markets(self) -> List[Dict]:
        """Scrape Reuters Markets news"""
        news = []
        try:
            url = "https://www.reuters.com/markets/"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('h3', limit=10)
            for article in articles:
                link = article.find('a') or article.find_parent('a')
                if link:
                    title = article.get_text(strip=True)
                    href = link.get('href', '')
                    
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
        """Scrape MarketWatch for global market news"""
        news = []
        try:
            url = "https://www.marketwatch.com/latest-news"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('h3', class_=re.compile('article'), limit=10)
            for article in articles:
                link = article.find('a')
                if link:
                    title = link.get_text(strip=True)
                    href = link.get('href', '')
                    
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'MarketWatch',
                        'url': href,
                        'sentiment': sentiment['compound'],
                        'category': 'international',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"MarketWatch error: {e}")
        return news
    
    def scrape_investing_com(self) -> List[Dict]:
        """Scrape Investing.com for emerging markets news"""
        news = []
        try:
            url = "https://www.investing.com/news/stock-market-news"
            response = self.session.get(url, timeout=15)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = soup.find_all('a', class_=re.compile('title'), limit=10)
            for article in articles:
                title = article.get_text(strip=True)
                href = article.get('href', '')
                
                if title and len(title) > 20:
                    sentiment = sentiment_analyzer.polarity_scores(title)
                    news.append({
                        'headline': title,
                        'source': 'Investing.com',
                        'url': f"https://www.investing.com{href}" if not href.startswith('http') else href,
                        'sentiment': sentiment['compound'],
                        'category': 'international',
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"Investing.com error: {e}")
        return news
    
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
                    notice_type = cols[1].get_text(strip=True) if len(cols) > 1 else ''
                    subject = cols[2].get_text(strip=True) if len(cols) > 2 else ''
                    
                    headline = f"{company}: {subject}"
                    sentiment = sentiment_analyzer.polarity_scores(headline)
                    
                    news.append({
                        'headline': headline,
                        'source': 'PSX Official',
                        'url': 'https://www.psx.com.pk',
                        'sentiment': sentiment['compound'],
                        'category': 'announcement',
                        'company': company,
                        'notice_type': notice_type,
                        'timestamp': datetime.now().isoformat()
                    })
        except Exception as e:
            print(f"PSX Notices error: {e}")
        return news
    
    # =========================================================================
    # GLOBAL MARKET DATA
    # =========================================================================
    
    def get_global_indices(self) -> Dict:
        """Get global market indices status"""
        indices = {}
        try:
            # Try to get data from various sources
            # This is a simplified version - in production use proper APIs
            indices = {
                'dow_jones': {'name': 'Dow Jones', 'region': 'US'},
                'sp500': {'name': 'S&P 500', 'region': 'US'},
                'nasdaq': {'name': 'NASDAQ', 'region': 'US'},
                'ftse100': {'name': 'FTSE 100', 'region': 'UK'},
                'nikkei': {'name': 'Nikkei 225', 'region': 'Japan'},
                'shanghai': {'name': 'Shanghai Composite', 'region': 'China'},
                'sensex': {'name': 'BSE Sensex', 'region': 'India'},
            }
        except Exception as e:
            print(f"Global indices error: {e}")
        return indices
    
    def get_commodities(self) -> Dict:
        """Get key commodity prices affecting Pakistan market"""
        commodities = {}
        try:
            # Oil prices (critical for Pakistan)
            # Gold prices
            # USD/PKR exchange rate
            commodities = {
                'oil': {'name': 'Brent Crude', 'impact': 'Energy, Transport, Fertilizer sectors'},
                'gold': {'name': 'Gold', 'impact': 'Banking, Investment sentiment'},
                'usd_pkr': {'name': 'USD/PKR', 'impact': 'Importers, Exporters, Overall market'}
            }
        except Exception as e:
            print(f"Commodities error: {e}")
        return commodities
    
    # =========================================================================
    # MAIN COLLECTION FUNCTION
    # =========================================================================
    
    def collect_all_news(self) -> Dict:
        """Collect news from all sources"""
        print("📰 Collecting news from all sources...")
        
        all_news = {
            'national': [],
            'international': [],
            'announcements': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Pakistani sources
        print("  → DAWN Business...")
        all_news['national'].extend(self.scrape_dawn_business())
        time.sleep(1)
        
        print("  → Business Recorder...")
        all_news['national'].extend(self.scrape_business_recorder())
        time.sleep(1)
        
        print("  → Express Tribune...")
        all_news['national'].extend(self.scrape_express_tribune())
        time.sleep(1)
        
        print("  → The News...")
        all_news['national'].extend(self.scrape_the_news())
        time.sleep(1)
        
        # International sources
        print("  → Reuters Markets...")
        all_news['international'].extend(self.scrape_reuters_markets())
        time.sleep(1)
        
        print("  → MarketWatch...")
        all_news['international'].extend(self.scrape_marketwatch())
        time.sleep(1)
        
        print("  → Investing.com...")
        all_news['international'].extend(self.scrape_investing_com())
        time.sleep(1)
        
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
            'merger', 'acquisition', 'investment', 'foreign', 'fdi'
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
    """Get all news from all sources"""
    return news_scraper.collect_all_news()


def get_market_moving_news() -> List[Dict]:
    """Get market-moving news only"""
    return news_scraper.get_market_moving_news()


if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE NEWS SCRAPER TEST")
    print("=" * 60)
    
    news = get_all_news()
    
    print(f"\n📰 National News: {len(news['national'])} headlines")
    for item in news['national'][:5]:
        print(f"  • [{item['source']}] {item['headline'][:60]}...")
    
    print(f"\n🌍 International News: {len(news['international'])} headlines")
    for item in news['international'][:5]:
        print(f"  • [{item['source']}] {item['headline'][:60]}...")
    
    print(f"\n📢 PSX Announcements: {len(news['announcements'])} notices")
    for item in news['announcements'][:5]:
        print(f"  • {item['headline'][:60]}...")
    
    print(f"\n📊 Overall Sentiment: {news.get('sentiment_label', 'N/A')}")
