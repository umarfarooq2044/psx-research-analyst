import requests
from bs4 import BeautifulSoup
import re
import json
import sys

# Windows Unicode Fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

url = "https://dps.psx.com.pk/company/OGDC"
print(f"Fetching {url}...")

try:
    resp = requests.get(url, timeout=10)
    if resp.status_code == 200:
        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Look for script tags with JSON
        scripts = soup.find_all('script')
        print(f"Found {len(scripts)} scripts")
        
        found_data = False
        for i, script in enumerate(scripts):
            if script.string:
                # Common patterns
                if "val:" in script.string or "price" in script.string or "eps" in script.string.lower():
                    print(f"--- Script {i} Match ---")
                    print(script.string[:500])
                    found_data = True
        
        # Look for table data
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        for i, table in enumerate(tables):
            rows = table.find_all('tr')
            if len(rows) > 0:
                print(f"Table {i} - {len(rows)} rows: {rows[0].text.strip()[:50]}")

    else:
        print(f"Failed: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
