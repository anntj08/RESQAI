"""Query DANS Dataverse for the 2018 Kerala landslide inventory file list."""
import json

import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
BASE = "https://phys-techsciences.datastations.nl"

for pid in ["doi:10.17026/dans-x6c-y7x2", "doi:10.17026/DANS-X6C-Y7X2"]:
    r = requests.get(f"{BASE}/api/datasets/:persistentId/",
                     params={"persistentId": pid}, headers=H, timeout=60)
    print(pid, r.status_code, r.headers.get("Content-Type"))
    if r.ok:
        d = r.json()
        ver = d.get("data", {}).get("latestVersion", {})
        print("version:", ver.get("versionNumber"), ver.get("versionMinorNumber"))
        print("license:", ver.get("license"), "| terms:", str(ver.get("termsOfUse"))[:200])
        print("files:", ver.get("filesCount"))
        for f in ver.get("files", []):
            df = f.get("dataFile", {})
            print(f"  id={df.get('id')} name={df.get('filename')} "
                  f"size={df.get('filesize')} ct={df.get('contentType')}")
            print(f"     dir={f.get('directoryLabel')} restricted={f.get('restricted')}")
        break
    else:
        print(r.text[:300])
