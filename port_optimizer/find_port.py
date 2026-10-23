import urllib.request
import urllib.parse
import json

BASE_URL = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Ports_Data/FeatureServer/0/query"

params = {
    "where": "country = 'Morocco'",
    "outFields": "portid,portname,country",
    "returnDistinctValues": "true",
    "resultRecordCount": 50,
    "f": "json",
}

url = BASE_URL + "?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://portwatch.imf.org/"})
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read().decode("utf-8"))

if "error" in data:
    print(f"Error: {data['error']}")
else:
    features = data.get("features", [])
    print(f"Found {len(features)} Moroccan ports:")
    for f in features:
        attr = f.get("attributes", {})
        print(f"  portid={attr.get('portid','?')}  portname={attr.get('portname','?')}")