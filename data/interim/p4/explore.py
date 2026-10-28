"""Phase 4 exploration: measure the structure the sampling design must respect.

Read-only. Answers, with numbers from the files on disk, the questions that the
target/background/validation decisions depend on:

  1. How many records are usable at each level, and how do the three roles (dated
     event / undated site / pre-2000) divide up?
  2. What positional uncertainty do the usable labels actually carry, and what
     exclusion radius would therefore be justified rather than arbitrary?
  3. How much of the district remains eligible as background at each radius?
  4. How do the positives distribute across candidate spatial block sizes?
  5. How clustered are the positives, and at what scale does clustering collapse?

Writes data/interim/p4/explore.json and prints a readable report.

Run:  python data/interim/p4/explore.py
"""
from __future__ import annotations

import json
import pathlib

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = pathlib.Path(__file__).resolve().parents[3]
INV = ROOT / "data" / "processed" / "inventory"
GRID = ROOT / "data" / "processed" / "grid"
OUT = ROOT / "data" / "interim" / "p4"
OUT.mkdir(parents=True, exist_ok=True)
CRS = "EPSG:32643"

rep: dict = {}


def section(title: str) -> None:
    print("\n" + "=" * 78)
    print(title)
    print("=" * 78)


# ------------------------------------------------------------------ 1. roles --
section("1. Inventory roles and eligibility levels")
df = pd.read_csv(INV / "inventory_spatial_suitability.csv")
print(f"records: {len(df)}")
print("\nlabel_role x spatial_suitability_use:")
print(pd.crosstab(df["label_role"], df["spatial_suitability_use"]).to_string())

usable = df[df["spatial_suitability_use"] == "point_label_ok"]
in_window = usable[usable["label_role"] == "EVENT_POINT_IN_WINDOW"]
print(f"\npoint_label_ok                 : {len(usable)}")
print(f"  of which in-window events    : {len(in_window)}")
print(f"  of which undated site        : "
      f"{(usable['label_role'] == 'SITE_EVIDENCE_UNDATED').sum()}")
print(f"  of which pre-2000            : "
      f"{(usable['label_role'] == 'HISTORICAL_PRE_2000').sum()}")

# Records superseded by a better-coordinate record from the same physical site.
sup = df["superseded_by"].fillna("").astype(str).str.strip()
print(f"\nrecords marked superseded_by   : {(sup != '').sum()}")
print(f"  of those, still point_label_ok: "
      f"{((sup != '') & (df['spatial_suitability_use'] == 'point_label_ok')).sum()}")

rep["roles"] = {
    "records": int(len(df)),
    "point_label_ok": int(len(usable)),
    "in_window_point_labels": int(len(in_window)),
    "undated_site_labels": int((usable["label_role"] == "SITE_EVIDENCE_UNDATED").sum()),
    "pre2000_labels": int((usable["label_role"] == "HISTORICAL_PRE_2000").sum()),
    "superseded_records": int((sup != "").sum()),
    "superseded_still_usable": int(
        ((sup != "") & (df["spatial_suitability_use"] == "point_label_ok")).sum()),
}

# ------------------------------------------------------- 2. event group view --
section("2. Event groups (the modelling unit)")
grp = in_window.groupby("event_group_id")
print(f"in-window usable records : {len(in_window)}")
print(f"distinct event groups    : {grp.ngroups}")
sizes = grp.size()
print(f"records per group        : {sizes.value_counts().sort_index().to_dict()}")

g2018 = in_window[in_window["event_year"] == 2018]
print(f"groups dated 2018        : {g2018['event_group_id'].nunique()}")
print(f"groups dated otherwise   : "
      f"{in_window[in_window['event_year'] != 2018]['event_group_id'].nunique()}")
print(f"records dated 2018       : {len(g2018)}")
print("\nrecords per year:")
print(in_window["event_year"].value_counts().sort_index().to_string())

rep["event_groups"] = {
    "in_window_records": int(len(in_window)),
    "groups": int(grp.ngroups),
    "records_per_group": {str(k): int(v) for k, v in sizes.value_counts().sort_index().items()},
    "groups_2018": int(g2018["event_group_id"].nunique()),
    "groups_non_2018": int(
        in_window[in_window["event_year"] != 2018]["event_group_id"].nunique()),
    "records_by_year": {str(k): int(v) for k, v in
                        in_window["event_year"].value_counts().sort_index().items()},
}

# ----------------------------------------------------------- 3. uncertainty --
section("3. Positional uncertainty of the usable in-window labels")
u = in_window["positional_uncertainty_m"].astype(float)
qs = {q: float(np.percentile(u, q)) for q in (50, 75, 90, 95, 99, 100)}
print(f"n={len(u)}  min={u.min():.1f}  max={u.max():.1f}")
for q, v in qs.items():
    print(f"  p{q:<3} {v:7.1f} m")
print("\nby source:")
print(in_window.groupby("source_id")["positional_uncertainty_m"]
      .agg(["count", "median", "max"]).round(1).to_string())

rep["uncertainty_m"] = {"n": int(len(u)), "percentiles": qs,
                        "min": float(u.min()), "max": float(u.max())}

# ----------------------------------------------------- 4. eligible background --
section("4. Background domain: district area left after excluding around positives")

# One point per event group: the most precise record of that group, ties broken by
# source_record_id so the choice is deterministic.
pos = (in_window.sort_values(["positional_uncertainty_m", "source_record_id"])
       .drop_duplicates("event_group_id", keep="first"))
pts = gpd.GeoDataFrame(
    pos[["event_group_id", "event_year", "source_id", "positional_uncertainty_m"]].copy(),
    geometry=gpd.points_from_xy(pos["lon_original"], pos["lat_original"]),
    crs="EPSG:4326").to_crs(CRS)
print(f"group-level positive points: {len(pts)}")

with rasterio.open(GRID / "district_mask_30m.tif") as ds:
    mask = ds.read(1) == 1
    tf = ds.transform
    cell = abs(tf.a)
print(f"district pixels: {int(mask.sum()):,} x {cell:.0f} m "
      f"= {mask.sum() * cell * cell / 1e6:,.1f} km2")

# Rasterise the positives (cell-centre registration, same as the analysis grid).
rows, cols = rasterio.transform.rowcol(tf, pts.geometry.x.to_numpy(), pts.geometry.y.to_numpy())
rows, cols = np.asarray(rows), np.asarray(cols)
seed = np.zeros(mask.shape, dtype=bool)
ok = (rows >= 0) & (rows < mask.shape[0]) & (cols >= 0) & (cols < mask.shape[1])
seed[rows[ok], cols[ok]] = True
print(f"positive cells inside the grid: {int(ok.sum())} / {len(pts)}")

dist_m = distance_transform_edt(~seed) * cell   # distance to nearest positive cell

elig = {}
print("\n  radius   eligible km2   % of district   eligible pixels")
for r in (0, 30, 50, 100, 150, 200, 300, 500):
    m = mask & (dist_m > r)
    km2 = m.sum() * cell * cell / 1e6
    pct = 100 * m.sum() / mask.sum()
    elig[r] = {"km2": round(float(km2), 1), "pct": round(float(pct), 2),
               "pixels": int(m.sum())}
    print(f"  {r:5.0f} m  {km2:10,.1f}   {pct:10.2f} %   {int(m.sum()):10,}")

print("\npositive-to-positive nearest-neighbour distance (group level):")
xy = np.c_[pts.geometry.x, pts.geometry.y]
from scipy.spatial import cKDTree  # noqa: E402
tree = cKDTree(xy)
dnn, _ = tree.query(xy, k=2)
dnn = dnn[:, 1]
for q in (10, 25, 50, 75, 90, 100):
    print(f"  p{q:<3} {np.percentile(dnn, q):8.1f} m")
print(f"  within 250 m : {(dnn <= 250).sum()}")
print(f"  within 1000 m: {(dnn <= 1000).sum()}")

rep["background_domain"] = {"cell_m": cell, "district_km2": round(float(mask.sum() * cell * cell / 1e6), 1),
                            "by_radius": {str(k): v for k, v in elig.items()}}
rep["nn_distance_m"] = {f"p{q}": float(np.percentile(dnn, q)) for q in (10, 25, 50, 75, 90, 100)}
rep["nn_within_250m"] = int((dnn <= 250).sum())
rep["nn_within_1000m"] = int((dnn <= 1000).sum())

# ------------------------------------------------------------ 5. block sizes --
section("5. Positives per candidate square block size")
print(f"{'block':>8}  {'nonempty':>9}  {'pos/blk':>8}  {'max':>5}  {'blocks >=5 pos':>15}")
blocks_rep = {}
for B in (1000, 2000, 3000, 4000, 5000, 8000):
    bx = np.floor((pts.geometry.x - tf.c) / B).astype(int)
    by = np.floor((pts.geometry.y - tf.f) / B).astype(int)
    key = bx.astype(np.int64) * 10000 + by.astype(np.int64)
    vc = pd.Series(key).value_counts()
    blocks_rep[str(B)] = {
        "nonempty_blocks": int(vc.size),
        "mean": round(float(vc.mean()), 2),
        "max": int(vc.max()),
        "blocks_ge5": int((vc >= 5).sum()),
        "blocks_ge10": int((vc >= 10).sum()),
    }
    print(f"{B:8d}  {vc.size:9d}  {vc.mean():8.2f}  {vc.max():5d}  {int((vc>=5).sum()):15d}")

rep["blocks"] = blocks_rep

# ------------------------------------------------- 6. single-linkage clusters --
section("6. Single-linkage clustering of group-level positives")
clusters = {}
for thr in (250, 500, 1000, 1500, 2000, 5000):
    pairs = tree.query_pairs(thr, output_type="ndarray")
    parent = list(range(len(xy)))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in pairs:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[rb] = ra
    n = len({find(i) for i in range(len(xy))})
    clusters[thr] = n
    print(f"  {thr:5d} m -> {n:3d} clusters")

rep["clusters"] = {str(k): int(v) for k, v in clusters.items()}

# ------------------------------------------------------------------ 7. save --
(OUT / "explore.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
print(f"\nwritten -> {OUT / 'explore.json'}")
