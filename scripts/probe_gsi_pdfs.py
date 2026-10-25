import urllib.parse
import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
base = "https://bhusanket.gsi.gov.in/Output/LandslideReport/"
tests = [
    ("Kerala", "Macro scale studies", "14337"),
    ("Kerala", "Macro scale studies", "14767"),
    ("Kerala", "Macro scale studies", "14768"),
    ("Kerala", "Macro scale studies", "14999"),
    ("Kerala", "Post Disaster Studies", "ADDL. ITEM(LANDSLIDES OCCURRED IN JUNE 2018 AT WAYANAD DISTRICT, KERALA)"),
    ("Kerala", "Site Specific Studies", "14253"),
    ("Kerala", "Site Specific Studies", "14252"),
    ("Kerala", "Site Specific Studies", "15990"),
]
for st, pt, acc in tests:
    url = base + "/".join(urllib.parse.quote(x, safe="") for x in (st, pt, acc)) + ".pdf"
    try:
        r = requests.get(url, headers=H, timeout=60, stream=True)
        print(f"{r.status_code} {r.headers.get('Content-Type','')[:24]:24s} {r.headers.get('Content-Length')} {url.split('/Output/')[1][:95]}")
        r.close()
    except Exception as e:
        print("ERR", type(e).__name__, str(e)[:80], url)
