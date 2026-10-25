import hashlib, pathlib
import pandas as pd

ROOT = pathlib.Path(r"C:\Major")
rows = []
for p in sorted((ROOT / "data" / "raw").rglob("*")):
    if p.is_file():
        h = hashlib.sha256()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 22), b""):
                h.update(b)
        rows.append({
            "relative_path": str(p.relative_to(ROOT)),
            "filename": p.name,
            "size_bytes": p.stat().st_size,
            "size_mb": round(p.stat().st_size / 1e6, 3),
            "sha256": h.hexdigest(),
        })
    if len(rows) % 40 == 0 and rows:
        print("hashed", len(rows), flush=True)

df = pd.DataFrame(rows)
df.to_csv(ROOT / "data" / "file_inventory.csv", index=False)
print("raw files:", len(df), "total GB:", round(df.size_bytes.sum() / 1e9, 2))
print(df.groupby(df.relative_path.str.split("/").str[2]).size().to_string())
