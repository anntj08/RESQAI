"""Locate the Global Fatal Landslide Database supplement and scan KSDMA for
Wayanad documents."""
import re

import requests

H = {"User-Agent": "Mozilla/5.0 (compatible; RESQAI-research/1.0; academic use)"}

print("=== NHESS 18/2161/2018 (Froude & Petley 2018) links ===")
r = requests.get("https://nhess.copernicus.org/articles/18/2161/2018/", headers=H, timeout=60)
print("status", r.status_code, "len", len(r.text))
links = set(re.findall(r'href="([^"]+)"', r.text))
for link in sorted(links):
    if re.search(r"supplement|suppl|\.xlsx|\.zip|\.csv", link, re.I):
        print("   ", link[:200])

print("\n=== KSDMA site: links mentioning landslide / Wayanad / disaster management plan ===")
r = requests.get("https://sdma.kerala.gov.in/", headers=H, timeout=60)
print("status", r.status_code, "len", len(r.text))
for link, text in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', r.text, re.S | re.I):
    t = re.sub(r"<[^>]+>", "", text).strip()
    if re.search(r"landslide|wayanad|plan|report|download", link + " " + t, re.I):
        print(f"   {t[:70]:70s} {link[:110]}")
