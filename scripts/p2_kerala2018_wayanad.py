"""Wayanad subset of the 2018 Kerala inventory + full GSI Kerala report triage."""
import json
import pathlib
import re

import geopandas as gpd
import pandas as pd

RAW = pathlib.Path(r"C:\Major\data\raw")
INT = pathlib.Path(r"C:\Major\data\interim")

# ---------- 2018 Kerala inventory -> Wayanad ----------
g = gpd.read_file(RAW / "landslide_inventory" / "kerala_2018_dans" / "Kerela landslide.shp")
print("statewide:", len(g))
print(g.District.value_counts().to_string())

wy = g[g.District.astype(str).str.strip().str.lower() == "wayanad"].copy()
print(f"\nWayanad 2018 records: {len(wy)}")
print(wy.Type_of_sl.value_counts().to_string())
print("source flags:  NRSC Y:", (wy.NRSC == "Y").sum(), "| GSI Y:", (wy.GSI == "Y").sum(),
      "| New Y:", (wy.New == "Y").sum())
print("area m2: min %.1f median %.1f max %.1f total %.0f" % (
    wy.Area.min(), wy.Area.median(), wy.Area.max(), wy.Area.sum()))
print("bounds:", tuple(round(v, 4) for v in wy.total_bounds))

out = INT / "inventory_extracts" / "inventory_kerala2018_wayanad.csv"
wy_out = wy.drop(columns="geometry").copy()
wy_out["longitude_dd"] = wy.geometry.x.values
wy_out["latitude_dd"] = wy.geometry.y.values
wy_out["coord_precision_deg"] = 0.00001
wy_out["date_of_event"] = "2018-06-01/2018-08-26 (monsoon season; per-event dates not recorded)"
wy_out["source_report"] = "Hao et al. 2020 ESSD / van Westen DANS doi:10.17026/dans-x6c-y7x2"
wy_out["source_file"] = "Kerela landslide.shp"
wy_out.to_csv(out, index=False)
print("wrote", out, len(wy_out), "rows")

# ---------- GSI Bhusanket: all Kerala reports ----------
txt = (RAW / "landslide_inventory" / "gsi_bhusanket" / "LandslideReport.json").read_text(
    encoding="utf-8", errors="replace")
body = txt.split("=", 1)[1]
body = re.sub(r"^\s*LandslideReportData.*$", "", body, flags=re.M)
body = re.sub(r"//[^\n]*", "", body)
body = re.sub(r",(\s*[}\]])", r"\1", body)
recs = json.loads(body)
print(f"\nGSI reports total: {len(recs)}")

ker = [r for r in recs if str(r.get("State", "")).strip().lower() == "kerala"]
print(f"Kerala reports: {len(ker)}")
ker.sort(key=lambda r: str(r.get("Field Season", "")))
for r in ker:
    print(f"  {str(r.get('Field Season')):10s} {str(r.get('Type of project'))[:26]:26s} "
          f"acc={str(r.get('Acc. No.'))[:22]:22s} {str(r.get('Title of the project'))[:95]}")
