import requests
import json
import sys

# Windows Unicode Fix
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def probe_endpoint(name, url):
    print(f"Probing {name}...")
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            try:
                data = resp.json()
                print(f"✅ SUCCESS: {name} returned Data")
                print(json.dumps(data, indent=2)[:500]) 
            except:
                print(f"⚠️ {name} returned 200 but not valid JSON")
        else:
            print(f"❌ {name} returned {resp.status_code}")
    except Exception as e:
        print(f"❌ {name} failed: {e}")

ticker = "OGDC"
base = "https://dps.psx.com.pk/webapi"

# Candidate endpoints
probe_endpoint("Sym", f"{base}/symbols/{ticker}")
probe_endpoint("Comp", f"{base}/companies/{ticker}")
probe_endpoint("Ratios", f"{base}/ratio/{ticker}")
probe_endpoint("Ratios2", f"{base}/ratios/{ticker}")
probe_endpoint("Financials", f"{base}/companies/{ticker}/financials") 
