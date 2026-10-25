"""Quantify the coordinate evidence for the July 2024 Mundakkai-Chooralmala event.

The question this answers: is GSI's published coordinate (11deg27'46"N,
76deg08'03"E) a transcription error, or a plausible source-area location?

Evidence used
  GSI 2024 FIR          11.462778, 76.134167
  Sreekumar et al. 2025 11.466944, 76.135833   (independent publication)
  OSM Mundakkai village 11.470171, 76.150676   (settlement, not the scarp)
  OSM Chooralmala       11.499232, 76.159871   (settlement)
  KSDMA Memorandum      crown is "approximately 3 km from Mundakkai and 5 km
                        from Chooralmala villages respectively"
"""
import json
import pathlib

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

PTS = {
    "GSI_2024_FIR": (11.462778, 76.134167),
    "Sreekumar2025_Table1": (11.466944, 76.135833),
    "OSM_Mundakkai_village": (11.4701711, 76.1506761),
    "OSM_Chooralmala_village": (11.4992319, 76.1598711),
}

g = gpd.GeoSeries([Point(lon, lat) for lat, lon in PTS.values()], crs=4326,
                  index=list(PTS)).to_crs(32643)

print("pairwise separations (metres)")
rows = []
names = list(PTS)
for i in range(len(names)):
    for j in range(i + 1, len(names)):
        d = g.iloc[i].distance(g.iloc[j])
        rows.append({"a": names[i], "b": names[j], "metres": round(d, 1)})
        print(f"  {names[i]:24s} - {names[j]:24s} {d:9.1f}")

print("\nKSDMA statement check: crown distance to each settlement")
for settle in ("OSM_Mundakkai_village", "OSM_Chooralmala_village"):
    for src in ("GSI_2024_FIR", "Sreekumar2025_Table1"):
        d = g[src].distance(g[settle])
        print(f"  {src:22s} -> {settle:24s} {d/1000:6.2f} km")

OUT = pathlib.Path(r"C:\Major\data\processed\inventory\2024_corroboration.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"points": PTS, "pairwise_m": rows}, indent=1), encoding="utf-8")
pd.DataFrame(rows).to_csv(OUT.with_suffix(".csv"), index=False)
print("\nwrote", OUT)
