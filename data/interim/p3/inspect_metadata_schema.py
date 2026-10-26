"""Inspect the schema of the raw-input metadata snapshots before comparing them.

Stage 7 requires knowing what identity fields actually exist before asserting equality.
Prints top-level structure, how each input is described, and whether SHA-256 / size /
mtime are present.

Run: python data/interim/p3/inspect_metadata_schema.py
"""
import json
import pathlib

ROOT = pathlib.Path(r"C:\Major")
before = json.loads((ROOT / "data/interim/p3/rebuild_backup/inputs_metadata_before.json").read_text(encoding="utf-8"))
after = json.loads((ROOT / "data/interim/p3/inputs_metadata.json").read_text(encoding="utf-8"))


def describe(d, label):
    print(f"=== {label} ===")
    print("top-level keys:", list(d.keys()))
    for k, v in d.items():
        if isinstance(v, dict):
            print(f"  {k}: dict with {len(v)} entries; sample keys: {list(v)[:3]}")
            if v:
                sample = v[list(v)[0]]
                if isinstance(sample, dict):
                    print(f"    per-entry fields: {sorted(sample.keys())}")
        elif isinstance(v, list):
            print(f"  {k}: list of {len(v)}")
        else:
            print(f"  {k}: {type(v).__name__} = {v!r}")
    print()


describe(before, "before (pre-recovery baseline)")
describe(after, "after (current)")

# Does every per-file record carry a content hash?
def hashes(d):
    out = {}
    for k, v in d.items():
        if isinstance(v, dict):
            for name, rec in v.items():
                if isinstance(rec, dict):
                    h = rec.get("sha256") or rec.get("hash") or rec.get("md5")
                    size = rec.get("size_bytes") or rec.get("bytes")
                    if h or size:
                        out[f"{k}/{name}"] = (h, size)
    return out


hb, ha = hashes(before), hashes(after)
print(f"records carrying a hash or size: before={len(hb)} after={len(ha)}")
if hb:
    k = next(iter(hb))
    print(f"example: {k} -> {hb[k]}")
else:
    print("NO CONTENT HASHES RECORDED -> immutability cannot be proven from these files alone")
