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
import asyncio
import aiohttp
import re
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
        # Simple cache to prevent redundant scraping (5 min duration)
        self._cache = None
        self._cache_time = 0
        self._cache_duration = 300 
    
    def _parse_feed(self, url: str, source: str, category: str = 'national', limit: int = 100) -> List[Dict]:
        """Helper to parse RSS feeds"""
        news = []
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries: # Iterate all, limit applied by logic if needed, but we want ALL
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
                    'timestamp': datetime.now().isoformat(),
                    'tickers': [] # Will be populated later
                })
        except Exception as e:
            print(f"RSS Error ({source}): {e}")
        return news[:limit]

    async def _async_parse_feed(self, session: aiohttp.ClientSession, url: str, source: str, category: str = 'national', limit: int = 100) -> List[Dict]:
        """Helper to parse RSS feeds asynchronously"""
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    text = await response.text()
                    feed = feedparser.parse(text)
                    news = []
                    for entry in feed.entries:
                        title = getattr(entry, 'title', '')
                        link = getattr(entry, 'link', '')
                        if not title: continue
                        
                        sentiment = sentiment_analyzer.polarity_scores(title)
                        news.append({
                            'headline': title,
                            'source': source,
                            'url': link,
                            'sentiment': sentiment['compound'],
                            'category': category,
                            'timestamp': datetime.now().isoformat(),
                            'tickers': []
                        })
                    return news[:limit]
        except Exception as e:
            print(f"Async RSS Error ({source}): {e}")
        return []

    async def _async_scrape_reuters(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Async version of Reuters scraping"""
        url = "https://www.reuters.com/markets/"
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    articles = soup.select('h3[data-testid="Heading"], h3 a') 
                    news = []
                    for article in articles[:50]:
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
                    return news
        except Exception as e:
            print(f"Async Reuters error: {e}")
        return []

    async def _async_scrape_psx_notices(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Async version of PSX notices scraping"""
        url = "https://www.psx.com.pk/psx/exchange/market/company-notices"
        try:
            async with session.get(url, timeout=15) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    rows = soup.find_all('tr', limit=20)
                    news = []
                    for row in rows[1:]:
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
                    return news
        except Exception as e:
            print(f"Async PSX Notices error: {e}")
        return []

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

    def scrape_profit_pk(self) -> List[Dict]:
        """Scrape Profit (Pakistan Today)"""
        return self._parse_feed("https://profit.pakistantoday.com.pk/feed/", "Profit PK")

    def scrape_mettis_global(self) -> List[Dict]:
        """Scrape Mettis Global (Main Feed)"""
        # Mettis might not have a public RSS, trying generic scrape or specific feed if known.
        # Often WordPress sites have /feed/
        return self._parse_feed("https://mettisglobal.news/feed/", "Mettis Global")
    
    # =========================================================================
    # INTERNATIONAL NEWS SOURCES (RSS/Scraping)
    # =========================================================================
    
    def scrape_reuters_markets(self) -> List[Dict]:
        """Scrape Reuters Markets (Scraping as RSS is limited)"""
        news = []
        try:
            url = "https://www.reuters.com/markets/"
            response = self.session.get(url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                # Try generic selectors for Reuters structure
                articles = soup.select('h3[data-testid="Heading"], h3 a') 
                
                for article in articles[:50]: # Increased from 10 to 50
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
            response = self.session.get(url, timeout=30)
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

    # Method collect_all_news is now defined above to include mapping logic.
    # This block is just to ensure clean file state if needed.
    pass
    
    async def async_get_market_moving_news(self, pre_collected_news: Optional[Dict] = None) -> List[Dict]:
        """
        Filter news that's likely to move the market.
        Asynchronously fetches full text and analyzes impact.
        """
        from news.article_fetcher import ArticleFetcher
        fetcher = ArticleFetcher()
        
        all_news = pre_collected_news if pre_collected_news else await self.async_collect_all_news()
        
        market_moving = []
        keywords = [
            'interest rate', 'sbp', 'imf', 'budget', 'tax', 'energy', 'oil',
            'gas', 'electricity', 'rupee', 'dollar', 'inflation', 'gdp',
            'export', 'import', 'trade deficit', 'remittances', 'privatization',
            'ipo', 'dividend', 'profit', 'loss', 'result', 'quarterly',
            'merger', 'acquisition', 'investment', 'foreign', 'fdi',
            'political', 'election', 'court', 'circular debt', 'capacity payment'
        ]
        
        candidates = []
        for category in ['national', 'international', 'announcements']:
            for item in all_news.get(category, []):
                headline = item.get('headline', '').lower()
                if any(kw in headline for kw in keywords) or abs(item.get('sentiment', 0)) > 0.2:
                    candidates.append(item)
        
        if not candidates:
            return []

        print(f"\n🧠 Async Deep Learning: Reading full text of {len(candidates)} potential market movers...")
        
        urls = [c['url'] for c in candidates if c.get('url')]
        contents = await fetcher.fetch_all(urls)
        
        for item in candidates:
            url = item.get('url')
            full_text = contents.get(url, "")
            
            if full_text:
                item['body'] = full_text
                deep_sent = sentiment_analyzer.polarity_scores(full_text[:2000])
                item['sentiment'] = deep_sent['compound']
                self._map_tickers_in_text(item, full_text)
                
            is_high_impact = False
            if abs(item.get('sentiment', 0)) > 0.4:
                is_high_impact = True
            if item.get('tickers') and abs(item.get('sentiment', 0)) > 0.2:
                is_high_impact = True
                
            if is_high_impact:
                item['market_impact'] = 'high' if abs(item.get('sentiment', 0)) > 0.5 else 'medium'
                market_moving.append(item)
        
        return sorted(market_moving, key=lambda x: abs(x.get('sentiment', 0)), reverse=True)

    def get_market_moving_news(self) -> List[Dict]:
        """
        Filter news that's likely to move the market.
        Now performs DEEP ANALYSIS by reading the full article text.
        """
        from news.article_fetcher import fetch_articles_sync
        
        all_news = self.collect_all_news()
        
        market_moving = []
        # Initial broad keyword filter
        keywords = [
            'interest rate', 'sbp', 'imf', 'budget', 'tax', 'energy', 'oil',
            'gas', 'electricity', 'rupee', 'dollar', 'inflation', 'gdp',
            'export', 'import', 'trade deficit', 'remittances', 'privatization',
            'ipo', 'dividend', 'profit', 'loss', 'result', 'quarterly',
            'merger', 'acquisition', 'investment', 'foreign', 'fdi',
            'political', 'election', 'court', 'circular debt', 'capacity payment'
        ]
        
        candidates = []
        for category in ['national', 'international', 'announcements']:
            for item in all_news.get(category, []):
                headline = item.get('headline', '').lower()
                # If high sentiment or keyword match, it's a candidate for deep reading
                if any(kw in headline for kw in keywords) or abs(item.get('sentiment', 0)) > 0.2:
                    candidates.append(item)
        
        print(f"\n🧠 Deep Learning: Reading full text of {len(candidates)} potential market movers...")
        
        # Batch fetch content
        urls = [c['url'] for c in candidates if c.get('url')]
        contents = fetch_articles_sync(urls)
        
        for item in candidates:
            url = item.get('url')
            full_text = contents.get(url, "")
            
            if full_text:
                item['body'] = full_text
                # Re-analyze sentiment on full TEXT (more accurate)
                # We limit text to 1000 chars for VADER to stay relevant
                deep_sent = sentiment_analyzer.polarity_scores(full_text[:2000])
                item['sentiment'] = deep_sent['compound']
                
                # Check tickers in BODY
                self._map_tickers_in_text(item, full_text)
                
            # Determine Market Impact based on Deep Analysis
            is_high_impact = False
            
            # Rule 1: High sentiment polarity
            if abs(item.get('sentiment', 0)) > 0.4:
                is_high_impact = True
                
            # Rule 2: Specific Ticker Mentioned + Significant Sentiment
            if item.get('tickers') and abs(item.get('sentiment', 0)) > 0.2:
                is_high_impact = True
                
            if is_high_impact:
                item['market_impact'] = 'high' if abs(item.get('sentiment', 0)) > 0.5 else 'medium'
                market_moving.append(item)
        
        # Sort by sentiment magnitude
        return sorted(market_moving, key=lambda x: abs(x.get('sentiment', 0)), reverse=True)

    def _map_tickers_in_text(self, item: Dict, text: str):
        """Helper to find tickers in full text"""
        try:
            from database.db_manager import db
            # This is expensive if run many times, optimization: cache tickers in init?
            # For now, we trust the DB response is fast or cached by OS
            all_tickers = db.get_all_tickers()
            symbol_map = {t['symbol']: t['symbol'] for t in all_tickers}
            
            found_tickers = set(item.get('tickers', [])) # Start with headline matches
            
            text_upper = text.upper()
            
            # Optimization: Only check for tickers if their first letter appears?
            # Or just check top 100 volume stocks? 
            # Checking 500 tickers against 2000 chars is 1M comparisons.. fast enough in Python?
            # It's okay for 20-30 articles.
            
            import re
            for symbol in symbol_map:
                if re.search(r'\b' + re.escape(symbol) + r'\b', text_upper):
                    found_tickers.add(symbol)
                    
            item['tickers'] = list(found_tickers)
            
        except Exception:
            pass


    def map_tickers_to_news(self, news_items: List[Dict]) -> List[Dict]:
        """
        Map news headlines to company tickers.
        E.g. "OGDC discovers oil" -> tickers=['OGDC']
        OPTIMIZED: Uses pre-compiled regex for all symbols.
        """
        if not news_items:
            return []
            
        try:
            # Import here to avoid circular dependencies
            from database.db_manager import db
            all_tickers = db.get_all_tickers()
            
            if not all_tickers:
                return news_items
                
            # Create a single pre-compiled regex pattern for all symbols
            # We sort symbols by length descending to match longest possible string first (e.g. HUBC vs HUB)
            symbols = sorted([t['symbol'] for t in all_tickers], key=len, reverse=True)
            pattern = re.compile(r'\b(' + '|'.join(re.escape(s) for s in symbols) + r')\b', re.IGNORECASE)
            
            for item in news_items:
                headline = item.get('headline', '')
                # Find all unique matches in the headline
                matches = set(pattern.findall(headline.upper()))
                item['tickers'] = list(matches)
                
        except Exception as e:
            print(f"Ticker mapping error: {e}")
            
        return news_items

    def collect_all_news(self) -> Dict:
        """Synchronous wrapper for collect_all_news"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # This is tricky if already in a loop. For orchestrator this is fine.
                import nest_asyncio
                nest_asyncio.apply()
            return loop.run_until_complete(self.async_collect_all_news())
        except Exception:
            # Fallback to simple run if loop issues
            return asyncio.run(self.async_collect_all_news())

    async def async_collect_all_news(self) -> Dict:
        """Collect news from all sources asynchronously parallel"""
        now = time.time()
        if self._cache and (now - self._cache_time < self._cache_duration):
            print("🕒 Using cached news data")
            return self._cache

        print("📰 Collecting news from RSS & Scrapers (Async)...")
        
        sources = [
            ("https://www.dawn.com/feeds/business", "DAWN Business", "national"),
            ("https://www.brecorder.com/feeds/business-economy", "Business Recorder", "national"),
            ("https://tribune.com.pk/feed/business", "Express Tribune", "national"),
            ("https://www.thenews.com.pk/rss/1/10", "The News", "national"),
            ("https://profit.pakistantoday.com.pk/feed/", "Profit PK", "national"),
            ("https://mettisglobal.news/feed/", "Mettis Global", "national"),
            ("http://feeds.marketwatch.com/marketwatch/topstories/", "MarketWatch", "international"),
            ("https://www.investing.com/rss/news.rss", "Investing.com", "international")
        ]
        
        async with aiohttp.ClientSession(headers=self.headers) as session:
            # Parallel tasks for RSS
            rss_tasks = [self._async_parse_feed(session, url, name, cat) for url, name, cat in sources]
            
            # Additional Scraping tasks
            scraping_tasks = [
                self._async_scrape_reuters(session),
                self._async_scrape_psx_notices(session)
            ]
            
            all_results = await asyncio.gather(*(rss_tasks + scraping_tasks))
            
            all_news = {
                'national': [],
                'international': [],
                'announcements': [],
                'timestamp': datetime.now().isoformat()
            }
            
            # Categorize results
            # First 6 are national RSS
            for i in range(6):
                all_news['national'].extend(all_results[i])
            
            # Next 2 are international RSS
            for i in range(6, 8):
                all_news['international'].extend(all_results[i])
            
            # Next is Reuters (International)
            all_news['international'].extend(all_results[8])
            
            # Last is PSX notices
            all_news['announcements'].extend(all_results[9])
            
            # MAP TICKERS (Optimized)
            print("  🔗 Mapping news to tickers (Optimized)...")
            all_news['national'] = self.map_tickers_to_news(all_news['national'])
            all_news['announcements'] = self.map_tickers_to_news(all_news['announcements'])
            
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
            
            self._cache = all_news
            self._cache_time = time.time()
            return all_news

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
