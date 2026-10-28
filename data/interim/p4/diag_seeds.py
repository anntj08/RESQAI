"""Diagnostic: how much does the assignment improve over a deterministic seed sweep?

For seeds seed..seed+N the same hill-climb is run; the final score tuple
(support deficit, cluster deficit, positive spread, background spread) is reported,
plus which seed wins with the design tie-break rule 'strictly best seed wins, ties ->
lowest seed'.
"""
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import p4_spatial_folds as pf  # noqa: E402

CFG = pf.CFG
SAMP = ROOT / "data" / "processed" / "sampling"

audit = pd.read_csv(SAMP / "eligibility_audit.csv")
pos = audit[audit["p4_use"] == "POSITIVE_EVENT"]
inv = pd.read_csv(ROOT / "data/processed/inventory/inventory_spatial_suitability.csv"
                  ).set_index("source_record_id")
bg = pd.read_csv(SAMP / "background_samples.csv")
with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
    tf = ds.transform
B = float(CFG["spatial_validation"]["block_size_m"])
k = int(CFG["spatial_validation"]["n_folds"])
thr = float(CFG["spatial_validation"]["clustering_threshold_m"])
minp, minc = 45, 5
seed = int(CFG["random_seed"])

tr = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
px, py = [np.asarray(v) for v in tr.transform(
    inv.loc[list(pos["source_record_id"]), "lon_original"].to_numpy(float),
    inv.loc[list(pos["source_record_id"]), "lat_original"].to_numpy(float))]
p_blocks = pf.block_ids(px, py, tf, B)
b_blocks = pf.block_ids(bg["x_32643"].to_numpy(float), bg["y_32643"].to_numpy(float), tf, B)
bg_counts = {int(b): int(c) for b, c in pd.Series(b_blocks).value_counts().items()}

results = []
for i in range(12):
    s = seed + i
    _, p_fold, all_blocks, block_fold, ncl, extra = pf.assign_positive_folds(
        np.c_[px, py], p_blocks, thr, k, s, tf, B, minp, minc,
        extra_blocks=b_blocks, extra_counts=bg_counts)
    counts = np.bincount(p_fold, minlength=k)
    bb = pf.block_ids(bg["x_32643"].to_numpy(float), bg["y_32643"].to_numpy(float), tf, B)
    bf_map = {int(b): int(f) for b, f in zip(all_blocks, block_fold)}
    bgf = np.array([bf_map[int(b)] for b in bb])
    bgc = np.bincount(bgf, minlength=k)
    score = (int(np.clip(minp - counts, 0, None).sum()),
             int(counts.max() - counts.min()), int(bgc.max() - bgc.min()))
    results.append((s, score, counts.tolist(), [int(x) for x in bgc]))
    print(f"seed {s}: spread {score[1]:>3}  bg_spread {score[2]:>4}  "
          f"pos/fold {counts.tolist()}  bg/fold {bgc.tolist()}")

ok = np.array([(r[1][0], r[1][1], r[1][2]) for r in results])
best_i = int(np.lexsort((ok[:, 2], ok[:, 1], ok[:, 0]))[0])
print(f"\nstrictly best (deterministic rule: minimise spread, tie -> "
      f"background spread then lowest seed): seed {results[best_i][0]}  "
      f"score {results[best_i][1]}  counts {results[best_i][2]}")
