import urllib.request
import urllib.parse
import json

BASE_URL = "https://services9.arcgis.com/weJ1QsnbMYJlCHdG/ArcGIS/rest/services/Daily_Ports_Data/FeatureServer/0/query"

params = {
    "where": "portid = 'port1265'",
    "outFields": "portid,portname,date,portcalls,import,export",
    "orderByFields": "date DESC",
    "resultRecordCount": 3,
    "f": "json",
}

url = BASE_URL + "?" + urllib.parse.urlencode(params)
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://portwatch.imf.org/"})
with urllib.request.urlopen(req, timeout=15) as r:
    data = json.loads(r.read().decode("utf-8"))

print(json.dumps(data.get("features", [])[:2], indent=2))