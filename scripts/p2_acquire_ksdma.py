"""Download the KSDMA documents that carry Wayanad event records, and dump the
text of the per-year KSDMA pages (2019 in particular has no PDF of its own)."""
import pathlib
import re
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

H = {"User-Agent": "Mozilla/5.0 (compatible; RESQAI-research/1.0; academic use)"}
OUT = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\ksdma")
OUT.mkdir(parents=True, exist_ok=True)

DOCS = {
    "ksdma_meppadi_pdna_2024.pdf":
        "https://sdma.kerala.gov.in/wp-content/uploads/2025/10/Meppadi-Landslide-PDNA_final_new1-2_compressed-compressed.pdf",
    "ksdma_memorandum_17082024.pdf":
        "https://sdma.kerala.gov.in/wp-content/uploads/2025/07/Memorandum_17082024.pdf",
    "ksdma_event_report_october2021.pdf":
        "http://sdma.kerala.gov.in/wp-content/uploads/2022/05/Event-report_October-2021.pdf",
    "ksdma_go_ms6_dmd_gsi.pdf":
        "https://sdma.kerala.gov.in/wp-content/uploads/2026/03/G.O.Ms-No.-6-DMD-GSI.pdf",
}

for name, url in DOCS.items():
    try:
        download(url, OUT / name, min_bytes=20_000)
    except Exception as e:
        print(f"FAILED {name}: {type(e).__name__} {str(e)[:120]}")

print("\n--- KSDMA page bodies: any Wayanad/Puthumala event text without a PDF? ---")
for p in ("/landslides-2019/", "/landslides-2018/", "/landslides-2021/", "/landslides-2024/"):
    r = requests.get("https://sdma.kerala.gov.in" + p, headers=H, timeout=60)
    body = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S | re.I)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body)
    hits = [m.start() for m in re.finditer(r"(?i)wayanad|puthumala|meppadi|mundakkai", body)]
    print(f"\n{p}  len={len(body)}  keyword_hits={len(hits)}")
    for h in hits[:6]:
        print("   ...", body[max(0, h - 130):h + 200].strip()[:330])
