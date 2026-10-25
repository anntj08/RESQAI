"""Resolve download endpoints for newly discovered candidate sources."""
import requests, re, json

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}


def probe(name, url, stream=False):
    try:
        r = requests.get(url, headers=H, timeout=45, allow_redirects=True, stream=stream)
        ct = r.headers.get("Content-Type", "")[:45]
        cl = r.headers.get("Content-Length")
        print(f"{name:34s} {r.status_code} len={cl} ct={ct}")
        if stream:
            r.close()
        return r
    except Exception as e:
        print(f"{name:34s} ERR {type(e).__name__}: {str(e)[:70]}")
        return None


# --- DANS 2018 Kerala inventory ---
r = probe("urn_resolver", "https://www.persistent-identifier.nl/urn:nbn:nl:ui:13-jw-q61d")
if r is not None and r.ok:
    print("  final url:", r.url)
    # look for download links
    for m in set(re.findall(r'href="([^"]*(?:download|file|\.zip)[^"]*)"', r.text, re.I)):
        print("   link:", m[:160])

probe("dans_doi", "https://doi.org/10.17026/dans-x6c-y7x2")

# --- Bhuvan open data archive + landslide WMS ---
probe("bhuvan_app3", "https://bhuvan-app3.nrsc.gov.in/data")
probe("bhuvan_wms_cap", "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/landslide.exe?service=WMS&request=GetCapabilities")
probe("bhuvan_wms2", "https://bhuvan-ras2.nrsc.gov.in/cgi-bin/disaster.exe?service=WMS&request=GetCapabilities")

# --- ISRO Landslide Atlas ---
probe("isro_atlas_page", "https://www.isro.gov.in/Landslide_Atlas_India.html")

# --- Kerala ILDM 2024 report ---
probe("ildm_report", "https://ildm.kerala.gov.in/wp-content/uploads/2025/04/Report-on-wayanad-landslide-1.pdf", stream=True)
