"""Show exactly how rainfall_validation.json changed after the warning-handling edit.

Expectation: only additive keys (all_nan_window_cells / _pct / _note) plus the
volatile elapsed_s. If anything else moved, the arithmetic changed and that would
contradict the byte-identical rasters.

Run: python data/interim/p3/diff_rainfall_json.py
"""
import json
import pathlib

ROOT = pathlib.Path(r"C:\Major")
a = json.loads((ROOT / "data/interim/p3/rebuild_backup/rainfall/rainfall_validation.json").read_text(encoding="utf-8"))
b = json.loads((ROOT / "data/processed/rainfall/rainfall_validation.json").read_text(encoding="utf-8"))


def flat(d, p=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flat(v, f"{p}.{k}" if p else k))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(flat(v, f"{p}[{i}]"))
    else:
        out[p] = d
    return out


fa, fb = flat(a), flat(b)
added = sorted(set(fb) - set(fa))
removed = sorted(set(fa) - set(fb))
changed = sorted(k for k in set(fa) & set(fb) if fa[k] != fb[k])

print(f"added   ({len(added)}):")
for k in added:
    print(f"  {k} = {fb[k]!r}")
print(f"removed ({len(removed)}):")
for k in removed:
    print(f"  {k} = {fa[k]!r}")
print(f"changed ({len(changed)}):")
for k in changed:
    print(f"  {k}: {fa[k]!r} -> {fb[k]!r}")
