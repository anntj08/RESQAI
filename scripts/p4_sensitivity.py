"""Phase 4 — sensitivity of the design to its own parameters.

The design fixes an exclusion radius, a sampling density, a clustering distance, a
buffer gap and a fold count. Each is a judgement, so each is varied here and its effect
on the *design* (domain size, fold support, separation) is measured. Nothing is
retrained or scored: this phase has no model.

  1. exclusion radius 50/100/200/300 m      -> eligible area and sample count
  2. sampling density 0.5/1/2 per km2       -> sample count only
  3. clustering distance 500/1000/2000 m    -> clusters, fold support
  4. buffer gap 0/500/1000/2000 m           -> training points lost, separation achieved
  5. fold count 3/5/10                      -> fold support
  6. inventory inclusion rule               -> do weaker records change the folds?
  7. temporal holdout feasibility           -> can 2018 train and non-2018 test?

Writes data/interim/p4/sensitivity.json.

Run:  python scripts/p4_sensitivity.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from p4_sample_background import valid_mask  # noqa: E402  (identical mask code)
from p4_spatial_folds import assign_positive_folds, block_ids, union_find  # noqa: E402

CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
OUTP = ROOT / "data" / "processed" / "sampling"
OUTI = ROOT / "data" / "interim" / "p4"
OUTI.mkdir(parents=True, exist_ok=True)
SEED = int(CFG["random_seed"])
CHOSEN_GAP = float(CFG["spatial_validation"]["buffer_gap_m"])
CHOSEN_K = int(CFG["spatial_validation"]["n_folds"])
CHOSEN_B = float(CFG["spatial_validation"]["block_size_m"])
MINP = int(CFG["spatial_validation"]["min_test_positives"])
MINC = int(CFG["spatial_validation"]["min_test_clusters"])
INV = pd.read_csv(ROOT / "data/processed/inventory/inventory_spatial_suitability.csv"
                  ).set_index("source_record_id")
TR = Transformer.from_crs(CFG["storage_crs"], CFG["analysis_crs"], always_xy=True)


def coords(ids) -> np.ndarray:
    x, y = TR.transform(INV.loc[list(ids), "lon_original"].to_numpy(float),
                        INV.loc[list(ids), "lat_original"].to_numpy(float))
    return np.c_[x, y]


def folds_for(xy: np.ndarray, thr: float, k: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Run the design's own assignment on an arbitrary positive set."""
    pb = block_ids(xy[:, 0], xy[:, 1], tf, CHOSEN_B)
    cid, fold, _, _, ncl, _ = assign_positive_folds(
        xy, pb, thr, k, SEED, tf, CHOSEN_B, MINP, MINC)
    return cid, fold, ncl


def clusters_at(xy: np.ndarray, thr: float) -> np.ndarray:
    pairs = cKDTree(xy).query_pairs(thr, output_type="ndarray")
    raw = union_find(len(xy), pairs)
    return pd.factorize(raw)[0]


def main() -> None:
    global tf
    rep: dict = {}
    audit = pd.read_csv(OUTP / "eligibility_audit.csv")
    pos = audit[audit["p4_use"] == "POSITIVE_EVENT"]
    pxy = coords(pos["source_record_id"])

    with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
        dmask = ds.read(1) == 1
        tf, shape = ds.transform, (ds.height, ds.width)
    cell = abs(tf.a)

    # ---- 1. exclusion radius (same exact-separation rule as the sampler) ------
    print("=" * 78 + "\n1. exclusion radius\n" + "=" * 78)
    valid, _ = valid_mask(shape)
    seed_cells = np.zeros(shape, dtype=bool)
    r, c = rasterio.transform.rowcol(tf, pxy[:, 0], pxy[:, 1])
    seed_cells[np.asarray(r), np.asarray(c)] = True
    dist_m = distance_transform_edt(~seed_cells) * cell
    base = dmask & valid

    # the raster distance is measured to positive CELLS; each recorded positive can sit
    # up to offsets[i] from its own cell centre, so the exact band re-admission applied
    # in scripts/p4_sample_background.py is reproduced here per radius
    offsets = np.hypot(pxy[:, 0] - (tf.c + (np.asarray(c) + 0.5) * tf.a),
                       pxy[:, 1] - (tf.f + (np.asarray(r) + 0.5) * tf.e))
    max_offset = float(offsets.max())
    pos_tree = cKDTree(pxy)

    rows = []
    print(f"{'radius m':>9} {'eligible km2':>13} {'% district':>11} {'bg @1/km2':>10}")
    for rad in CFG["sensitivity"]["exclusion_radius_m"]:
        conservative = base & (dist_m > rad + max_offset)
        band = base & (dist_m > rad) & ~conservative
        br, bc = np.nonzero(band)
        band_xy = np.c_[tf.c + (bc + 0.5) * tf.a, tf.f + (br + 0.5) * tf.e]
        band_keep = pos_tree.query(band_xy, k=1)[0] >= rad
        n_elig = int(conservative.sum()) + int(band_keep.sum())
        km2 = float(n_elig * cell * cell / 1e6)
        rows.append({"radius_m": rad, "eligible_km2": round(km2, 2),
                     "pct_district": round(100 * float(n_elig) / float(dmask.sum()), 3),
                     "background_at_1_per_km2": int(round(km2))})
        print(f"{rad:>9} {km2:>13,.2f} {rows[-1]['pct_district']:>10.2f}% "
              f"{rows[-1]['background_at_1_per_km2']:>10,}")
    rep["exclusion_radius"] = rows
    rep["max_positive_to_own_cell_centre_m"] = round(max_offset, 2)

    # ---- 2. density ---------------------------------------------------------
    print("\n" + "=" * 78 + "\n2. sampling density (domain at the chosen radius)\n" + "=" * 78)
    chosen = next(x for x in rows if x["radius_m"] == CFG["background"]["exclusion_radius_m"])
    dens = []
    print(f"{'per km2':>8} {'samples':>9} {'per positive':>13}")
    for d in CFG["sensitivity"]["sampling_density_per_km2"]:
        n = int(round(d * chosen["eligible_km2"]))
        dens.append({"density_per_km2": d, "samples": n,
                     "per_positive": round(n / len(pos), 2)})
        print(f"{d:>8} {n:>9,} {n / len(pos):>13.2f}")
    rep["density"] = dens

    # ---- 3. clustering distance --------------------------------------------
    print("\n" + "=" * 78 + f"\n3. clustering distance, {CHOSEN_K} folds\n" + "=" * 78)
    print(f"{'thr m':>7} {'clusters':>9} {'largest':>8} {'min fold +':>11} "
          f"{'max fold +':>11} {'min clusters/fold':>18}")
    cl = []
    for thr in (500, 1000, 2000):
        cid, fold, ncl = folds_for(pxy, float(thr), CHOSEN_K)
        counts = np.bincount(fold, minlength=CHOSEN_K)
        per_fold = [len(np.unique(cid[fold == f])) for f in range(CHOSEN_K)]
        largest = int(pd.Series(cid).value_counts().max())
        cl.append({"cluster_threshold_m": thr, "clusters": int(ncl), "largest_cluster": largest,
                   "fold_positives": counts.tolist(), "min_fold_positives": int(counts.min()),
                   "min_clusters_per_fold": int(min(per_fold))})
        print(f"{thr:>7} {ncl:>9} {largest:>8} {counts.min():>11} {counts.max():>11} "
              f"{min(per_fold):>18}")
    rep["clustering_distance"] = cl

    # ---- 4. buffer gap ------------------------------------------------------
    print("\n" + "=" * 78 + "\n4. buffer gap (fold assignment held fixed)\n" + "=" * 78)
    fa = pd.read_csv(OUTP / "fold_assignments.csv")
    gaps = []
    print(f"{'gap m':>7} {'dropped pts':>12} {'dropped +':>10} {'min train-test m':>17}")
    for g in CFG["sensitivity"]["buffer_gap_m"]:
        dropped = dropped_pos = 0
        kept_min = np.inf
        for f in range(CHOSEN_K):
            test = fa[fa["fold"] == f]
            rest = fa[fa["fold"] != f]
            d = cKDTree(test[["x_32643", "y_32643"]].to_numpy()).query(
                rest[["x_32643", "y_32643"]].to_numpy(), k=1)[0]
            keep = d > g
            dropped += int((~keep).sum())
            dropped_pos += int(((~keep) & (rest["role"] == "positive").to_numpy()).sum())
            if keep.any():
                kept_min = min(kept_min, float(d[keep].min()))
        gaps.append({"gap_m": g, "dropped_points_total": dropped,
                     "dropped_positives_total": dropped_pos,
                     "min_train_to_test_m": round(kept_min, 1)})
        print(f"{g:>7} {dropped:>12} {dropped_pos:>10} {kept_min:>17,.1f}")
    rep["buffer_gap"] = gaps

    # ---- 5. fold count ------------------------------------------------------
    print("\n" + "=" * 78 + "\n5. fold count (cluster threshold and gap as chosen)\n" + "=" * 78)
    print(f"{'k':>3} {'fold positives':>42} {'min clusters/fold':>18} {'meets support':>14}")
    ks = []
    for k in (3, 5, 10):
        cid, fold, ncl = folds_for(pxy, CHOSEN_GAP, k)
        counts = np.bincount(fold, minlength=k)
        per_fold = [len(np.unique(cid[fold == f])) for f in range(k)]
        ok = bool(counts.min() >= MINP and min(per_fold) >= MINC)
        ks.append({"k": k, "fold_positives": counts.tolist(),
                   "min_clusters_per_fold": int(min(per_fold)),
                   "meets_support_threshold": ok})
        print(f"{k:>3} {str(counts.tolist()):>42} {min(per_fold):>18} {str(ok):>14}")
    rep["fold_count"] = ks

    # ---- 6. inclusion rule --------------------------------------------------
    print("\n" + "=" * 78 + "\n6. inventory inclusion rule\n" + "=" * 78)
    undated = audit[(audit["p4_use"] == "EXCLUDE_UNDATED_SITE")
                    & (audit["spatial_suitability_use"] == "point_label_ok")]
    pre2000 = audit[(audit["p4_use"] == "EXCLUDE_PRE_2000")
                    & (audit["spatial_suitability_use"] == "point_label_ok")]
    variants = {
        "primary (in-window point labels)":
            list(pos["source_record_id"]),
        "+ undated site records":
            list(pos["source_record_id"]) + list(undated["source_record_id"]),
        "+ undated and pre-2000":
            list(pos["source_record_id"]) + list(undated["source_record_id"])
            + list(pre2000["source_record_id"]),
    }
    inc = {}
    print(f"{'variant':<34} {'points':>7} {'clusters':>9} {'min fold +':>11}")
    for name, ids in variants.items():
        xy = coords(ids)
        cid, fold, ncl = folds_for(xy, CHOSEN_GAP, CHOSEN_K)
        counts = np.bincount(fold, minlength=CHOSEN_K)
        inc[name] = {"points": int(len(xy)), "clusters": int(ncl),
                     "fold_positives": counts.tolist(), "min_fold_positives": int(counts.min())}
        print(f"{name:<34} {len(xy):>7} {ncl:>9} {counts.min():>11}")
    rep["inclusion_rule"] = inc

    # ---- 7. temporal holdout -----------------------------------------------
    print("\n" + "=" * 78 + "\n7. temporal holdout feasibility\n" + "=" * 78)
    y2018 = pos[pos["event_year"] == 2018]
    yother = pos[pos["event_year"] != 2018]
    xy_other = coords(yother["source_record_id"])
    cid_other = clusters_at(xy_other, CHOSEN_GAP)
    nn_other = cKDTree(xy_other).query(xy_other, k=2)[0][:, 1]
    tmp = {
        "train_2018_points": int(len(y2018)),
        "test_non2018_points": int(len(yother)),
        "non2018_clusters_at_1km": int(len(np.unique(cid_other))),
        "non2018_by_year": {str(int(k)): int(v) for k, v in
                            yother["event_year"].value_counts().sort_index().items()},
        "non2018_min_nn_m": round(float(nn_other.min()), 1),
        "reverse_direction_attempted": False,
        "verdict": "train on 2018 and test on the 28 non-2018 labels is technically "
                   "possible but very weak (28 labels, "
                   f"{len(np.unique(cid_other))} clusters); training on 28 and testing on "
                   "335 is not viable and is not attempted",
    }
    print(f"2018 train points          : {tmp['train_2018_points']}")
    print(f"non-2018 test points       : {tmp['test_non2018_points']} "
          f"{tmp['non2018_by_year']}")
    print(f"non-2018 clusters at 1 km  : {tmp['non2018_clusters_at_1km']}")
    print(f"non-2018 min NN            : {tmp['non2018_min_nn_m']} m")
    rep["temporal"] = tmp

    (OUTI / "sensitivity.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    print(f"\nwritten -> {OUTI / 'sensitivity.json'}")


if __name__ == "__main__":
    main()
