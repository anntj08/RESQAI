"""Probe phase-2 candidate sources that were still unresolved.

Each line records what was actually returned so the discovery report can state
the blocker with evidence rather than assumption.
"""
import requests

H = {"User-Agent": "Mozilla/5.0 (compatible; RESQAI-research/1.0; academic use)",
     "Accept": "*/*"}


def probe(name, url, stream=False, allow_redirects=True):
    try:
        r = requests.get(url, headers=H, timeout=40, stream=stream,
                         allow_redirects=allow_redirects, verify=True)
        ct = r.headers.get("Content-Type", "")[:40]
        cl = r.headers.get("Content-Length")
        print(f"{name:30s} {r.status_code} len={str(cl):>12s} ct={ct}")
        if stream:
            r.close()
        else:
            print(f"   final={r.url[:110]}")
        return r
    except Exception as e:
        print(f"{name:30s} ERR {type(e).__name__}: {str(e)[:90]}")
        return None


print("--- Global Fatal Landslide Database (Froude & Petley 2018, NHESS) ---")
probe("nhess_supplement", "https://nhess.copernicus.org/articles/18/2161/2018/nhess-18-2161-2018-supplement.zip", stream=True)
probe("nhess_article", "https://nhess.copernicus.org/articles/18/2161/2018/", stream=True)

print("\n--- Kerala ILDM 2024 Wayanad landslide report ---")
probe("ildm_https", "https://ildm.kerala.gov.in/wp-content/uploads/2025/04/Report-on-wayanad-landslide-1.pdf", stream=True)
probe("ildm_http", "http://ildm.kerala.gov.in/wp-content/uploads/2025/04/Report-on-wayanad-landslide-1.pdf", stream=True)
probe("ildm_root", "https://ildm.kerala.gov.in/", stream=True)

print("\n--- Kerala disaster management / SEOC ---")
probe("ksdma", "https://sdma.kerala.gov.in/", stream=True)
probe("revenue_kerala", "https://revenue.kerala.gov.in/", stream=True)

print("\n--- GSI Bhukosh (previously TCP timeout) ---")
probe("bhukosh", "https://bhukosh.gsi.gov.in/Bhukosh/", stream=True)
probe("bhukosh_ip", "https://bhukosh.gsi.gov.in/", stream=True)

print("\n--- Bare-earth DEM alternatives ---")
probe("fabdem_bris", "https://data.bris.ac.uk/data/dataset/25wfy0f9ukoge2gs7a5mqpq2j7", stream=True)
probe("glo30_vrt", "https://copernicus-dem-30m.s3.amazonaws.com/", stream=True)

print("\n--- Soil / geology regional ---")
probe("usgs_southasia", "https://pubs.usgs.gov/of/1997/ofr-97-470/OF97-470K/", stream=True)
probe("macrostrat_api", "https://macrostrat.org/api/v2/geologic_units/map?lat=11.6&lng=76.1", stream=True)

print("\n--- ISRO Bhuvan landslide inventory WMS ---")
probe("bhuvan_wms3", "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/wms.cgi?service=WMS&request=GetCapabilities", stream=True)
probe("bhuvan_landslide_layer", "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=landslide", stream=True)
