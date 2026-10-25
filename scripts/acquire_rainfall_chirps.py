"""CHIRPS v2.0 monthly precipitation, 2000-2025 (global tiles; Wayanad window subset later)."""
import concurrent.futures as cf
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

OUT = pathlib.Path(r"C:\Major\data\raw\rainfall\chirps_v2_monthly")
BASE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/chirps-v2.0.{y}.{m:02d}.tif.gz"

jobs = [(y, m) for y in range(2000, 2026) for m in range(1, 13)]
print("months requested:", len(jobs))

ok, fail = [], []


def work(job):
    y, m = job
    url = BASE.format(y=y, m=m)
    dest = OUT / f"chirps-v2.0.{y}.{m:02d}.tif.gz"
    for attempt in range(3):
        try:
            download(url, dest, min_bytes=5_000_000, retries=1, log=False)
            return ("ok", y, m)
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    return ("fail", y, m)


with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for i, res in enumerate(ex.map(work, jobs), 1):
        (ok if res[0] == "ok" else fail).append(res)
        if i % 25 == 0:
            print(f"{i}/{len(jobs)} ok={len(ok)} fail={len(fail)}", flush=True)

print("FINAL ok", len(ok), "fail", len(fail))
print("failed:", [f"{y}-{m:02d}" for _, y, m in fail])
print("bytes:", sum(p.stat().st_size for p in OUT.glob("*.gz")) / 1e9, "GB")
