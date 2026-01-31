import requests
from bs4 import BeautifulSoup
import sys

# Windows Unicode Fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

url = "https://dps.psx.com.pk/company/MARI" # Using MARI as another test
print(f"Fetching {url}...")

try:
    resp = requests.get(url, timeout=10)
    soup = BeautifulSoup(resp.content, "html.parser")
    
    tables = soup.find_all('table')
    
    for i, table in enumerate(tables):
        print(f"\n--- Table {i} ---")
        rows = table.find_all('tr')
        for row in rows:
            cols = row.find_all(['th', 'td'])
            data = [c.text.strip() for c in cols]
            print(data)

except Exception as e:
    print(e)
