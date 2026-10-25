"""Inspect the Global Fatal Landslide Database tables and extract any Wayanad /
Kerala records."""
import pathlib

import pandas as pd

GF = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gfld")

for p in sorted(GF.glob("*.xlsx")):
    x = pd.ExcelFile(p)
    print(f"\n===== {p.name}  sheets={x.sheet_names}")
    for sh in x.sheet_names:
        d = x.parse(sh, header=None)
        print(f"  -- sheet '{sh}' shape={d.shape}")
        print("     first 4 rows:")
        for i in range(min(4, len(d))):
            print("       ", [str(v)[:38] for v in d.iloc[i].tolist()[:8]])
