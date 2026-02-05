import sys
import httpx
from datetime import datetime

def test_api(url):
    print(f"🔍 Testing API at: {url}")
    
    # 1. Test Health
    try:
        r = httpx.get(f"{url}/health", timeout=10)
        if r.status_code == 200:
            print(f"✅ Health Check: OK ({r.json()})")
        else:
            print(f"❌ Health Check Failed: Status {r.status_code}")
    except Exception as e:
        print(f"❌ Health Check Failed: {e}")

    # 2. Test Holidays for current year
    year = datetime.now().year
    print(f"📅 Fetching holidays for {year}...")
    try:
        r = httpx.get(f"{url}/v1/holidays?year={year}", timeout=10)
        if r.status_code == 200:
            data = r.json()
            holidays = data.get("holidays", [])
            print(f"✅ Found {len(holidays)} holidays.")
            for h in holidays[:3]: # Show first 3
                print(f"   - {h['date']}: {h['name']} ({h['type']})")
            if len(holidays) > 3:
                print(f"   - ... and {len(holidays)-3} more")
        else:
            print(f"❌ Get Holidays Failed: Status {r.status_code}")
            print(f"   Response: {r.text}")
    except Exception as e:
        print(f"❌ Get Holidays Failed: {e}")

if __name__ == "__main__":
    target_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
    if target_url.endswith("/"):
        target_url = target_url[:-1]
    test_api(target_url)
