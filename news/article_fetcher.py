import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import re

class ArticleFetcher:
    """
    Asynchronously fetches and extracts main content from news URLs.
    Designed to read the 'Full Story' like a human analyst.
    """
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.semaphore = asyncio.Semaphore(10) # Limit concurrent connections

    async def fetch_text(self, session, url: str) -> Optional[str]:
        """Fetch single url and extract text"""
        if not url or not url.startswith('http'):
            return None
            
        async with self.semaphore:
            try:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        html = await response.text()
                        return self._extract_content(html, url)
            except Exception as e:
                # Silently fail for individual URLs to keep flow moving
                return None
        return None

    def _extract_content(self, html: str, url: str) -> str:
        """Heuristic-based content extraction"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove junk
            for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                script.decompose()

            # Target common article bodies based on source hints or generic tags
            text_blocks = []
            
            # Priority: <article> tag
            article = soup.find('article')
            if article:
                paragraphs = article.find_all('p')
            else:
                # Generic fallback: find all p tags with sufficient text
                paragraphs = soup.find_all('p')

            for p in paragraphs:
                text = p.get_text(strip=True)
                # Filter out short captions or menu items
                if len(text) > 40:
                    text_blocks.append(text)
            
            # Join top paragraphs (limit to ~2000 chars to avoid noise)
            full_text = " ".join(text_blocks)
            return full_text if len(full_text) > 100 else ""
            
        except Exception:
            return ""

    async def fetch_all(self, urls: List[str]) -> Dict[str, str]:
        """Fetch multiple URLs concurrently"""
        results = {}
        async with aiohttp.ClientSession(headers=self.headers) as session:
            tasks = [self.fetch_text(session, url) for url in urls]
            contents = await asyncio.gather(*tasks)
            
            for url, content in zip(urls, contents):
                if content:
                    results[url] = content
                    
        return results

# Helper wrapper for synchronous calls
def fetch_articles_sync(urls: List[str]) -> Dict[str, str]:
    try:
        # Check if loop is already running (e.g. inside another async process)
        # For simplicity in this project structure, we use a fresh loop or run_until_complete
        # If specific environment has loop issues, we handle here.
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        fetcher = ArticleFetcher()
        return loop.run_until_complete(fetcher.fetch_all(urls))
        
    except Exception as e:
        print(f"Async fetch error: {e}")
        return {}

if __name__ == "__main__":
    # Test
    test_urls = [
        "https://www.dawn.com", # Main page (might fail content heuristic but test connection)
        "https://profit.pakistantoday.com.pk"
    ]
    print("Testing Article Fetcher...")
    content = fetch_articles_sync(test_urls)
    print(f"Fetched {len(content)} pages.")
