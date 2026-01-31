from news.comprehensive_news import get_market_moving_news
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

print("🚀 Starting Deep News Analysis Test...")

try:
    print("calling get_market_moving_news()...")
    items = get_market_moving_news()
    
    print(f"\n✅ Found {len(items)} market moving items.")
    for item in items[:3]:
        print(f"\n📰 [Headline]: {item['headline']}")
        print(f"   [Sentiment]: {item['sentiment']}")
        print(f"   [Tags]: {item.get('tickers', [])}")
        body_prev = item.get('body', '')[:100].replace('\n', ' ')
        print(f"   [Body Preview]: {body_prev}...")

    print("\nTest Complete.")
except Exception as e:
    print(f"\n❌ CONSOLE ERROR: {e}")
    import traceback
    traceback.print_exc()
