import urllib.request
import urllib.parse
import json
import os
import time
from datetime import datetime, timedelta, timezone

CACHE_PATH = os.path.join(os.path.dirname(__file__), "portwatch_cache.json")
CACHE_TTL = 3600

PORT_ID = "port1265"
PORT_NAME = "Tanger Med"

BASE_URL = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Ports_Data/FeatureServer/0/query"


def fetch_portwatch_data(days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    cutoff_str = cutoff.strftime("%Y-%m-%d")

    params = {
        "where": f"portid = '{PORT_ID}' AND date >= DATE '{cutoff_str}'",
        "outFields": "portid,portname,date,portcalls,portcalls_container,import,export,import_container,export_container",
        "orderByFields": "date DESC",
        "resultRecordCount": 50,
        "f": "json",
    }

    url = BASE_URL + "?" + urllib.parse.urlencode(params)

    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://portwatch.imf.org/",
            }
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8")
            data = json.loads(raw)

        if "error" in data:
            print(f"  API error: {data['error']}")
            return None

        features = data.get("features", [])
        if not features:
            print(f"  No features returned for {PORT_ID}")
            return None

        records = []
        for f in features:
            attr = f.get("attributes", {})
            date_val = attr.get("date", "")
            if isinstance(date_val, (int, float)):
                date_str = datetime.fromtimestamp(date_val / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
            else:
                date_str = str(date_val) if date_val else "Unknown"
            records.append({
                "date": date_str,
                "calls": int(attr.get("portcalls", 0) or 0),
                "calls_container": int(attr.get("portcalls_container", 0) or 0),
                "import_tons": round(float(attr.get("import", 0) or 0)),
                "export_tons": round(float(attr.get("export", 0) or 0)),
                "import_container_tons": round(float(attr.get("import_container", 0) or 0)),
                "export_container_tons": round(float(attr.get("export_container", 0) or 0)),
            })

        return records

    except Exception as e:
        print(f"  PortWatch fetch error: {e}")
        return None


def load_cache():
    if not os.path.exists(CACHE_PATH):
        return None
    try:
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)
        age = time.time() - cache.get("timestamp", 0)
        if age < CACHE_TTL:
            print(f"  Using cached PortWatch data ({int(age/60)} min old)")
            return cache
        print(f"  Cache expired, refreshing...")
        return None
    except Exception:
        return None


def save_cache(data):
    data["timestamp"] = time.time()
    data["fetched_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_summary(records):
    if not records:
        return {}
    total_calls = sum(r["calls"] for r in records)
    avg_calls = round(total_calls / len(records), 1)
    total_import = sum(r["import_tons"] for r in records)
    total_export = sum(r["export_tons"] for r in records)
    max_calls = max(r["calls"] for r in records)
    recent = records[0] if records else {}
    return {
        "days_covered": len(records),
        "total_calls": total_calls,
        "avg_daily_calls": avg_calls,
        "total_import_tons": total_import,
        "total_export_tons": total_export,
        "max_daily_calls": max_calls,
        "latest_date": recent.get("date", ""),
        "latest_calls": recent.get("calls", 0),
        "latest_calls_container": recent.get("calls_container", 0),
        "latest_import_tons": recent.get("import_tons", 0),
        "latest_export_tons": recent.get("export_tons", 0),
    }


def run_portwatch(force_refresh=False):
    print("=" * 60)
    print("MAROLOGIX PORTWATCH CONNECTOR")
    print(f"Port: {PORT_NAME} ({PORT_ID})")
    print(f"Source: IMF PortWatch (portwatch.imf.org)")
    print("=" * 60)

    if not force_refresh:
        cached = load_cache()
        if cached:
            return cached

    print("Fetching live data from IMF PortWatch API...")
    records = fetch_portwatch_data(days=30)

    if not records:
        print("  Live fetch failed.")
        return {
            "records": [], "summary": {},
            "source": "IMF PortWatch", "port": PORT_NAME, "error": True
        }

    summary = build_summary(records)
    result = {
        "records": records,
        "summary": summary,
        "source": "IMF PortWatch - AIS satellite data (UN Global Platform)",
        "port": PORT_NAME,
        "port_id": PORT_ID,
        "error": False,
    }

    save_cache(result)

    print(f"  Fetched {len(records)} days of data")
    print(f"  Latest date: {summary.get('latest_date', 'N/A')}")
    print(f"  Avg daily calls (30d): {summary.get('avg_daily_calls', 0)}")
    print(f"  Total import (30d): {summary.get('total_import_tons', 0):,} tons")
    print(f"  Total export (30d): {summary.get('total_export_tons', 0):,} tons")
    print("=" * 60)

    return result


if __name__ == "__main__":
    result = run_portwatch(force_refresh=True)
    if not result.get("error"):
        print("\nRECENT PORT CALLS (Tanger Med):")
        print(f"  {'Date':<12} {'Calls':>6} {'Container':>10} {'Import (t)':>14} {'Export (t)':>14}")
        print("  " + "-" * 62)
        for r in result["records"][:15]:
            print(
                f"  {r['date']:<12} {r['calls']:>6} "
                f"{r['calls_container']:>10} "
                f"{r['import_tons']:>14,} {r['export_tons']:>14,}"
            )
        s = result.get("summary", {})
        print(f"\n  30-day average: {s.get('avg_daily_calls', 0)} vessel calls/day")
        print(f"  Data source: {result.get('source', '')}")
    else:
        print("  No data retrieved.")