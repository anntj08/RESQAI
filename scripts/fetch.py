"""Resumable downloader with validation for RESQAI acquisition."""
import hashlib
import pathlib
import sys
import time

import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use; final-year project)"}


def download(url, dest, min_bytes=1000, retries=4, log=True):
    dest = pathlib.Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size >= min_bytes:
        if log:
            print(f"SKIP exists {dest.name} ({dest.stat().st_size/1e6:.1f} MB)")
        return dest
    tmp = dest.with_suffix(dest.suffix + ".part")
    for attempt in range(1, retries + 1):
        try:
            with requests.get(url, headers=H, stream=True, timeout=180) as r:
                r.raise_for_status()
                total = int(r.headers.get("Content-Length") or 0)
                got = 0
                t0 = time.time()
                with open(tmp, "wb") as f:
                    for chunk in r.iter_content(1024 * 512):
                        f.write(chunk)
                        got += len(chunk)
                if total and got < total:
                    raise IOError(f"short read {got}/{total}")
            tmp.replace(dest)
            if log:
                print(f"OK {dest.name} {got/1e6:.1f} MB in {time.time()-t0:.0f}s")
            return dest
        except Exception as e:
            if tmp.exists():
                tmp.unlink()
            if log:
                print(f"attempt {attempt} failed {dest.name}: {type(e).__name__} {str(e)[:90]}")
            time.sleep(2 * attempt)
    raise RuntimeError(f"FAILED {url}")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


if __name__ == "__main__":
    download(sys.argv[1], sys.argv[2])
