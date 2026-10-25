import pathlib, re, sys
import requests
sys.path.insert(0, r"C:\Major\scripts")
from fetch import download

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
RAW = pathlib.Path(r"C:\Major\data\raw")

download("https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv",
         RAW / "landslide_inventory" / "nasa_glc" / "Global_Landslide_Catalog_Export_rows.csv", min_bytes=100_000)

# inspect bhusanket page for data endpoints
r = requests.get("https://bhusanket.gsi.gov.in/statewiseLandslideReport.html", headers=H, timeout=60)
print("--- scripts ---")
for s in re.findall(r'<script[^>]*src=["\']([^"\']+)', r.text):
    print(s)
print("--- inline js/json hints ---")
for m in re.findall(r'(?:fetch|ajax|url)\s*[:(]\s*["\']([^"\']+)', r.text):
    print(m)
print("--- body sample ---")
print(re.sub(r"\s+", " ", r.text)[:900])

# GLiM gdb size probe
try:
    rr = requests.get("https://www.dropbox.com/s/9vuowtebp9f1iud/LiMW_GIS%202015.gdb.zip?dl=1",
                      headers=H, timeout=60, stream=True, allow_redirects=True)
    print("GLiM status", rr.status_code, "len", rr.headers.get("Content-Length"),
          "ct", rr.headers.get("Content-Type"))
    rr.close()
except Exception as e:
    print("GLiM ERR", type(e).__name__, str(e)[:100])
