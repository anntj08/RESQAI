"""Phase 4 — spatial fold design and leakage control.

Why not a random split: the 363 positive points have a median nearest-neighbour
distance of 335 m, and 318 of them have a neighbour within 1 km. A random split would
place immediate neighbours on both sides of the partition, so apparent skill would be
partly memorisation of the same hillslope.

Design, applied in this order:

  1. CLUSTER  Positives are clustered by single linkage at 1,000 m — 76 clusters. A
              cluster is atomic: two points in one cluster are the same neighbourhood,
              so they are never divided between folds (and no retained training point
              can be within 1 km of a test positive, because that pair would have been
              one cluster).
  2. BLOCK    The district is tiled into whole 3,000 m square blocks aligned to the
              analysis grid. Every analysis point (positive or background) belongs to
              exactly one block. Block indexing is non-negative and unique.
  3. UNIT     Blocks that contain points of the same cluster are merged into block
              units, so a cluster crossing block boundaries cannot be split. These
              units are the atoms of fold assignment; blocks without positives are
              singleton units.
  4. FOLD     Units are grouped into 5 folds by seeded k-means on unit centroids,
              weighted by positive count. Twelve deterministic candidates (seeds
              20261026..20261037) are hill-climbed by moving WHOLE units to minimise,
              in order, (a) support deficit below the minimum fold support, (b) the
              spread of fold positive counts, (c) — as a tie-break — the spread of
              fold background counts; the best end state wins, ties at the lowest
              candidate, so the result is a deterministic function of data+config.
  5. BUFFER   For each fold, every training point within `buffer_gap_m` of ANY test
              point is DROPPED from that fold's training set. Blocks alone leave
              neighbouring folds touching; this distance rule creates the gap, and the
              gap is verified rather than assumed. Dropped points are written to
              fold_drops.csv with their distance to the test set.

Consequences that follow from the design (asserted below, not assumed):
  * no 3 km block is ever split across folds (0 mixed-fold blocks);
  * no event group, and no 1 km cluster, is ever split across folds.

Outputs (data/processed/sampling/):
  spatial_blocks.csv        block -> unit -> fold, with point counts
  fold_assignments.csv      every analysis point with cluster, block and fold
  fold_drops.csv            points dropped from each fold's training set, with reason
  modelling_points.csv      the candidate positive/background table for Phase 5
  fold_summary.json         per-fold support, buffer losses, leakage checks

Run:  python scripts/p4_spatial_folds.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys

import numpy as np
import pandas as pd
import rasterio
import scipy
import sklearn
from pyproj import Transformer
from scipy.spatial import cKDTree
from sklearn.cluster import KMeans

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
OUT = ROOT / "data" / "processed" / "sampling"

MAX_HILLCLIMB_ITERATIONS = 500
# Deterministic candidate starts for the fold assignment: N weighted k-means runs at
# seeds base_seed..base_seed+N-1, each hill-climbed; the best end state wins and ties
# fall to the lowest candidate, so the assignment stays a function of (data, config).
N_CANDIDATE_SEEDS = 12


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def union_find(n: int, pairs: np.ndarray) -> np.ndarray:
    parent = list(range(n))

    def find(a: int) -> int:
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in pairs:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[rb] = ra
    return np.array([find(i) for i in range(n)])


# --------------------------------------------------------------- block grid ---
def block_ids(x: np.ndarray, y: np.ndarray, tf, B: float) -> np.ndarray:
    """Non-negative unique block id from a point's projected coordinates.

    bbx = floor((x - tf.c)/B)  >= 0 inside the grid
    bby = floor((tf.f - y)/B)  >= 0  (y decreases from the top edge tf.f)
    id  = bby * 10000 + bbx    unique because bbx stays below 10000.
    """
    bbx = np.floor((np.asarray(x, float) - tf.c) / B).astype(np.int64)
    bby = np.floor((tf.f - np.asarray(y, float)) / B).astype(np.int64)
    if (bbx < 0).any() or (bby < 0).any():
        raise ValueError("a point left the analysis grid block range")
    return bby * 10_000 + bbx


def block_centre(bid: int, tf, B: float) -> tuple[float, float]:
    bby, bbx = divmod(int(bid), 10_000)
    return tf.c + (bbx + 0.5) * B, tf.f - (bby + 0.5) * B


# ------------------------------------------------------------ fold assignment ---
def _fold_stats(fold: np.ndarray, w_pos: np.ndarray, w_clu: np.ndarray,
                w_bg: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pos = np.bincount(fold, weights=w_pos, minlength=k).round().astype(int)
    clu = np.bincount(fold, weights=w_clu, minlength=k).round().astype(int)
    bg = np.bincount(fold, weights=w_bg, minlength=k).round().astype(int)
    return pos, clu, bg


def _score(pos: np.ndarray, clu: np.ndarray, bg: np.ndarray,
           minp: int, minc: int) -> tuple[int, int, int, int]:
    pos_def = int(np.clip(minp - pos, 0, None).sum())
    clu_def = int(np.clip(minc - clu, 0, None).sum())
    return (pos_def, clu_def, int(pos.max() - pos.min()), int(bg.max() - bg.min()))


def assign_positive_folds(pxy: np.ndarray, p_blocks: np.ndarray, thr: float, k: int,
                          seed: int, tf, B: float, minp: int, minc: int,
                          extra_blocks: np.ndarray | None = None,
                          extra_counts: dict | None = None
                          ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, int, dict]:
    """Cluster positives, merge their blocks into units, assign whole units to folds.

    Shared by this script and scripts/p4_sensitivity.py so the sensitivity analysis
    exercises the exact assignment used by the design.

    Returns (cid, p_fold, all_blocks, block_fold_per_block, n_clusters,
             {"units": units_df, "log": repair_log}); block->fold lookup is
             dict(zip(all_blocks, block_fold_per_block)).
    """
    # 1. single-linkage clusters of the positives
    pairs = cKDTree(pxy).query_pairs(thr, output_type="ndarray")
    _, cid = np.unique(union_find(len(pxy), pairs), return_inverse=True)
    cid = np.asarray(cid)
    n_clusters = int(cid.max()) + 1

    # 2. blocks; every block (positive-bearing or not) becomes a unit atom
    all_blocks = np.unique(p_blocks) if extra_blocks is None else \
        np.unique(np.concatenate([p_blocks, np.asarray(extra_blocks, np.int64)]))
    b_index = {int(b): i for i, b in enumerate(all_blocks)}

    # 3. union blocks that share a cluster: a cluster's block set moves as one unit
    merge = []
    block_of_cluster = np.empty(n_clusters, dtype=np.int64)
    for c in range(n_clusters):
        bs = sorted({b_index[int(b)] for b in p_blocks[cid == c]})
        block_of_cluster[c] = bs[0]
        merge.extend((bs[0], b) for b in bs[1:])
    _, unit = np.unique(union_find(len(all_blocks),
                                   np.asarray(merge, dtype=np.int64)
                                   if merge else np.zeros((0, 2), np.int64)),
                        return_inverse=True)
    unit = np.asarray(unit)
    n_units = int(unit.max()) + 1

    # unit descriptors
    w_bx = np.array([block_centre(b, tf, B)[0] for b in all_blocks])
    w_by = np.array([block_centre(b, tf, B)[1] for b in all_blocks])
    units = pd.DataFrame({
        "unit": np.arange(n_units),
        "cx": np.bincount(unit, weights=w_bx, minlength=n_units) /
              np.bincount(unit, minlength=n_units),
        "cy": np.bincount(unit, weights=w_by, minlength=n_units) /
              np.bincount(unit, minlength=n_units),
        "n_pos": np.bincount(np.asarray([unit[b_index[int(b)]] for b in p_blocks]),
                             minlength=n_units),
        "n_bg": np.zeros(n_units),
        "n_blocks": np.bincount(unit, minlength=n_units),
    })
    cl_unit = unit[block_of_cluster]
    units["n_clu"] = np.bincount(cl_unit, minlength=n_units)
    bg_sum = np.zeros(n_units)
    if extra_counts is not None:
        for b in all_blocks:
            bg_sum[unit[b_index[int(b)]]] += float(extra_counts.get(int(b), 0))
    units["n_bg"] = bg_sum

    # 4. deterministic candidate sweep: N_CANDIDATE_SEEDS weighted k-means starts
    #    (base_seed .. base_seed + N_CANDIDATE_SEEDS - 1), each hill-climbed; the best
    #    end state by (support deficit, cluster deficit, positive spread, background
    #    spread), ties at the lowest candidate, is the final assignment. Every
    #    candidate is reproducible and the selection rule is fixed, so the result is
    #    a deterministic function of (data, config).
    xy_unit = units[["cx", "cy"]].to_numpy()
    w_unit = (units["n_pos"] + 1).to_numpy()
    w_pos = units["n_pos"].to_numpy(float)
    w_clu = units["n_clu"].to_numpy(float)
    w_bg = units["n_bg"].to_numpy(float)

    def climb(init: np.ndarray) -> tuple[np.ndarray, list[dict], tuple[int, int, int, int]]:
        fold_c = init.astype(int).copy()
        log_c: list[dict] = []
        for _ in range(MAX_HILLCLIMB_ITERATIONS):
            pos, clu, bgc = _fold_stats(fold_c, w_pos, w_clu, w_bg, k)
            best = _score(pos, clu, bgc, minp, minc)
            best_move = None
            for u in range(n_units):
                f0 = fold_c[u]
                pos_np = pos.copy(); pos_np[f0] -= w_pos[u]
                clu_np = clu.copy(); clu_np[f0] -= w_clu[u]
                bg_np = bgc.copy(); bg_np[f0] -= w_bg[u]
                for t in range(k):
                    if t == f0:
                        continue
                    p2 = pos_np.copy(); p2[t] += w_pos[u]
                    c2 = clu_np.copy(); c2[t] += w_clu[u]
                    b2 = bg_np.copy(); b2[t] += w_bg[u]
                    s = _score(p2.round().astype(int), c2.round().astype(int),
                               b2.round().astype(int), minp, minc)
                    if s < best:
                        best, best_move = s, (u, t)
            if best_move is None:
                break
            u, t = best_move
            fold_c[u] = t
            log_c.append({"unit": int(u), "from_fold": int(f0), "to_fold": int(t),
                          "positives_moved": int(w_pos[u])})
        pos, clu, bgc = _fold_stats(fold_c, w_pos, w_clu, w_bg, k)
        return fold_c, log_c, _score(pos, clu, bgc, minp, minc)

    best_key = None
    for i in range(N_CANDIDATE_SEEDS):
        km = KMeans(n_clusters=k, random_state=seed + i, n_init=100).fit(
            xy_unit, sample_weight=w_unit)
        fold_c, log_c, key = climb(km.labels_)
        cand_key = (key[0], key[1], key[2], key[3], i)
        if best_key is None or cand_key < best_key:
            best_key, fold, log = cand_key, fold_c, log_c
            chosen_candidate = i

    p_fold = fold[unit[np.asarray([b_index[int(b)] for b in p_blocks])]]
    block_fold = fold[unit]  # per all_blocks entry: unit index -> that unit's fold
    return cid, p_fold, all_blocks, block_fold, n_clusters, \
        {"units": units, "log": log, "unit_per_block": unit,
         "chosen_candidate": int(chosen_candidate),
         "n_candidates": int(N_CANDIDATE_SEEDS),
         "candidate_scores": best_key[:4]}


# ---------------------------------------------------------------------- main ---
def main() -> None:
    sp = CFG["spatial_validation"]
    B = float(sp["block_size_m"])
    gap = float(sp["buffer_gap_m"])
    thr = float(sp["clustering_threshold_m"])
    k = int(sp["n_folds"])
    minp = int(sp["min_test_positives"])
    minc = int(sp["min_test_clusters"])
    seed = int(CFG["random_seed"])

    audit = pd.read_csv(OUT / "eligibility_audit.csv")
    inv = pd.read_csv(ROOT / "data/processed/inventory/inventory_spatial_suitability.csv"
                      ).set_index("source_record_id")
    bg = pd.read_csv(OUT / "background_samples.csv")
    run = json.loads((OUT / "sampling_run_config.json").read_text(encoding="utf-8"))

    with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
        dmask = ds.read(1) == 1
        tf = ds.transform
        shape = (ds.height, ds.width)

    pos = audit[audit["p4_use"] == "POSITIVE_EVENT"]
    pos_ids = pos["source_record_id"].to_numpy()
    pos_group = pos["event_group_id"].to_numpy()
    pos_year = pos["event_year"].to_numpy()

    tr = Transformer.from_crs(CFG["analysis_crs"], CFG["storage_crs"], always_xy=True)
    tr_fwd = Transformer.from_crs(CFG["storage_crs"], CFG["analysis_crs"], always_xy=True)
    px, py = [np.asarray(v) for v in tr_fwd.transform(
        inv.loc[list(pos_ids), "lon_original"].to_numpy(float),
        inv.loc[list(pos_ids), "lat_original"].to_numpy(float))]
    bgx = bg["x_32643"].to_numpy(float)
    bgy = bg["y_32643"].to_numpy(float)
    pxy = np.c_[px, py]

    p_blocks = block_ids(px, py, tf, B)
    b_blocks = block_ids(bgx, bgy, tf, B)
    bg_counts = {int(b): int(c) for b, c in pd.Series(b_blocks).value_counts().items()}

    cid, p_fold, all_blocks, block_fold, n_clusters, extra = assign_positive_folds(
        pxy, p_blocks, thr, k, seed, tf, B, minp, minc,
        extra_blocks=b_blocks, extra_counts=bg_counts)
    units = extra["units"]
    log = extra["log"]
    unit_per_block = np.asarray(extra["unit_per_block"])
    chosen_candidate = int(extra["chosen_candidate"])
    n_units = int(len(units))
    repair = log

    # block -> fold lookup, then fold every analysis point by its block
    block_fold_map = {int(b): int(f) for b, f in zip(all_blocks, block_fold)}
    assert len(block_fold_map) == len(all_blocks)
    b_fold = np.array([block_fold_map[int(b)] for b in b_blocks])

    pts = pd.concat([
        pd.DataFrame({
            "point_id": [f"POS-{g}" for g in pos_group],
            "role": "positive", "label": 1,
            "event_group_id": pos_group, "event_year": pos_year,
            "cluster_id": cid, "block_id": p_blocks, "fold": p_fold,
            "x_32643": px, "y_32643": py,
        }),
        pd.DataFrame({
            "point_id": bg["sample_id"], "role": "background", "label": 0,
            "event_group_id": "", "event_year": np.nan,
            "cluster_id": -1, "block_id": b_blocks, "fold": b_fold,
            "x_32643": bgx, "y_32643": bgy,
        }),
    ], ignore_index=True)

    lon, lat = tr.transform(pts["x_32643"].to_numpy(), pts["y_32643"].to_numpy())
    pts["lon_4326"] = np.round(lon, 7)
    pts["lat_4326"] = np.round(lat, 7)

    # ---- buffer + verification -----------------------------------------------
    folds = []
    drops = []
    min_gap_overall = float("inf")
    xy_all = pts[["x_32643", "y_32643"]].to_numpy()
    fold_arr = pts["fold"].to_numpy()
    roles = pts["role"].to_numpy()
    pids = pts["point_id"].to_numpy()
    for f in range(k):
        is_test = fold_arr == f
        d = cKDTree(xy_all[is_test]).query(xy_all[~is_test], k=1)[0]
        keep = d > gap
        rest_idx = np.flatnonzero(~is_test)
        kept = rest_idx[keep]
        dropped_idx = rest_idx[~keep]
        min_kept = float(d[keep].min()) if keep.any() else float("inf")
        min_gap_overall = min(min_gap_overall, min_kept)
        is_pos = roles == "positive"
        folds.append({
            "fold": f,
            "test_positives": int((roles[is_test] == "positive").sum()),
            "test_background": int((roles[is_test] == "background").sum()),
            "test_blocks": int(sum(1 for v in block_fold_map.values() if v == f)),
            "test_clusters": int(pts.loc[is_test & is_pos, "cluster_id"].nunique()),
            "train_positives": int((roles[kept] == "positive").sum()),
            "train_background": int((roles[kept] == "background").sum()),
            "dropped_from_train": int(len(dropped_idx)),
            "dropped_positives": int((roles[dropped_idx] == "positive").sum()),
            "min_train_to_test_m": round(min_kept, 1) if np.isfinite(min_kept) else None,
        })
        for j, dist in zip(dropped_idx, d[~keep]):
            drops.append({
                "fold": f, "point_id": pids[j], "role": roles[j], "label":
                    1 if roles[j] == "positive" else 0,
                "point_fold": int(fold_arr[j]),
                "distance_to_test_m": round(float(dist), 1),
                "reason": f"point lies within the {gap:.0f} m buffer of test fold {f}",
            })

    # Leakage invariants, from the assembled table (not from internals).
    assert pts["point_id"].is_unique, "duplicate point_id"
    assert pts["fold"].between(0, k - 1).all(), "unassigned fold"
    assert (pd.DataFrame({"g": pos_group, "f": p_fold}).groupby("g")["f"].nunique() == 1
            ).all(), "an event group spans more than one fold"
    assert (pd.DataFrame({"c": cid, "f": p_fold}).groupby("c")["f"].nunique() == 1
            ).all(), "a spatial cluster spans more than one fold"
    assert (pd.DataFrame({"b": pts["block_id"], "f": pts["fold"]})
            .groupby("b")["f"].nunique() == 1).all(), "a block is split across folds"
    assert min_gap_overall > gap, (
        f"a retained training point is within the buffer: min gap {min_gap_overall:.1f} "
        f"m <= {gap:.0f} m")
    assert all(fl["test_positives"] >= minp for fl in folds), \
        "a fold has too few test positives to evaluate"
    assert all(fl["test_clusters"] >= minc for fl in folds), \
        "a fold holds too few distinct clusters to evaluate"

    rows, cols = rasterio.transform.rowcol(tf, xy_all[:, 0], xy_all[:, 1])
    rows, cols = np.asarray(rows), np.asarray(cols)
    assert np.all((rows >= 0) & (rows < shape[0]) & (cols >= 0) & (cols < shape[1])), \
        "a point falls outside the analysis grid"
    assert bool(dmask[rows, cols].all()), "a point falls outside the district mask"

    # ---- write ----------------------------------------------------------------
    npos_blocks = pd.Series(p_blocks).value_counts().to_dict()
    nbg_blocks = pd.Series(b_blocks).value_counts().to_dict()
    bclu_blocks = (pd.DataFrame({"b": p_blocks, "c": cid}).drop_duplicates()
                   .groupby("b").size().to_dict())
    blocks = pd.DataFrame({
        "block_id": all_blocks,
        "bx": [int(b % 10_000) for b in all_blocks],
        "by": [int(b // 10_000) for b in all_blocks],
        "unit_id": [int(u) for u in unit_per_block],
        "fold": [int(f) for f in block_fold],
        "n_positives": [int(npos_blocks.get(int(b), 0)) for b in all_blocks],
        "n_background": [int(nbg_blocks.get(int(b), 0)) for b in all_blocks],
        "n_clusters": [int(bclu_blocks.get(int(b), 0)) for b in all_blocks],
    })
    dbg = (int(blocks["n_positives"].sum()), int(blocks["n_background"].sum()),
           int((pts["role"] == "positive").sum()), int((pts["role"] == "background").sum()))
    assert dbg[:2] == dbg[2:], f"block point counts do not match the point table: {dbg}"
    blocks = blocks.sort_values("block_id")
    blocks.to_csv(OUT / "spatial_blocks.csv", index=False, encoding="utf-8",
                  lineterminator="\n")

    drops_df = pd.DataFrame(drops)
    drops_df.to_csv(OUT / "fold_drops.csv", index=False, encoding="utf-8",
                    lineterminator="\n")

    pts_sorted = pts.sort_values(["role", "point_id"]).reset_index(drop=True)
    pts_sorted.to_csv(OUT / "fold_assignments.csv", index=False, encoding="utf-8",
                      lineterminator="\n")
    pts_sorted[["point_id", "role", "label", "x_32643", "y_32643", "lon_4326",
                "lat_4326", "event_group_id", "event_year", "cluster_id", "block_id",
                "fold"]].to_csv(OUT / "modelling_points.csv", index=False,
                                encoding="utf-8", lineterminator="\n")

    sizes = (pd.Series(cid).value_counts()).sort_values(ascending=False)
    summary = {
        "design": "cluster-atomic, block-base spatial folds with a verified distance "
                  "buffer: whole 3 km blocks are grouped into units by shared 1 km "
                  "positive clusters; whole units are assigned to folds; training "
                  "points within the buffer gap of a test fold are dropped",
        "n_folds": k,
        "buffer_gap_m": gap,
        "clustering_threshold_m": thr,
        "block_size_m": B,
        "random_seed": seed,
        "min_test_positives": minp,
        "min_test_clusters": minc,
        "clusters": n_clusters,
        "cluster_sizes_desc": [int(v) for v in sizes.tolist()],
        "blocks": int(len(blocks)),
        "block_units": n_units,
        "assignment": {
            "method": ("12 deterministic weighted-kmeans candidates hill-climbed on "
                       "(support deficit, cluster deficit, positive spread, background "
                       "spread); best end state wins, ties at the lowest candidate"),
            "candidate_seeds": [seed + i for i in range(extra["n_candidates"])],
            "chosen_candidate_seed": seed + chosen_candidate,
            "candidate_score": list(extra["candidate_scores"]),
        },
        "repair_moves": int(len(repair)),
        "repair_log": repair,
        "mixed_fold_blocks": int((pd.DataFrame({"b": pts["block_id"], "f": pts["fold"]})
                                  .groupby("b")["f"].nunique() > 1).sum()),
        "points": {"positives": int((pts["role"] == "positive").sum()),
                   "background": int((pts["role"] == "background").sum())},
        "folds": folds,
        "totals": {
            "test_positives": sum(f["test_positives"] for f in folds),
            "test_background": sum(f["test_background"] for f in folds),
            "dropped_from_train": sum(f["dropped_from_train"] for f in folds),
            "dropped_positives": sum(f["dropped_positives"] for f in folds),
        },
        "invariants": {
            "point_ids_unique": True,
            "event_group_in_one_fold": True,
            "cluster_in_one_fold": True,
            "block_in_one_fold": True,
            "all_points_in_district_mask": True,
            "buffer_enforced_and_verified": True,
            "min_train_to_test_m": round(float(min_gap_overall), 1),
            "buffer_gap_m": gap,
        },
        "inputs": {
            "eligibility_audit_sha256": sha256(OUT / "eligibility_audit.csv"),
            "background_samples_sha256": sha256(OUT / "background_samples.csv"),
            "background_run_seed": int(run["random_seed"]),
        },
        "versions": {
            "python": sys.version.split()[0],
            "numpy": np.__version__, "pandas": pd.__version__,
            "scipy": scipy.__version__, "sklearn": sklearn.__version__,
            "rasterio": rasterio.__version__,
        },
        "not_claimed": [
            "spatial independence between folds is not asserted: adjacent hillslopes "
            "still share terrain, land cover and rainfall history; the buffer only "
            "removes training points from the immediate neighbourhood of each test fold",
            "background points are not confirmed absence of landsliding",
            "a fold is a set of whole blocks, not a hydrological or socio-administrative "
            "unit; folds are contiguous where blocks join but may form several patches",
        ],
    }
    (OUT / "fold_summary.json").write_text(json.dumps(summary, indent=2),
                                           encoding="utf-8")

    counts = np.bincount(p_fold, minlength=k)
    print(f"clusters {n_clusters}  units {n_units}  blocks {len(blocks)}  "
          f"candidates 12 -> chosen seed {seed + chosen_candidate}  "
          f"repair moves {len(repair)}")
    print(f"positives/fold {counts.tolist()}  spread {counts.max() - counts.min()}")
    print(f"mixed-fold 3 km blocks: {summary['mixed_fold_blocks']} (must be 0)")
    print(f"\n{'fold':>4} {'test+':>6} {'test-':>7} {'clust':>6} {'blocks':>7} "
          f"{'train+':>7} {'train-':>7} {'dropped':>8} {'min gap m':>10}")
    for f in folds:
        print(f"{f['fold']:>4} {f['test_positives']:>6} {f['test_background']:>7} "
              f"{f['test_clusters']:>6} {f['test_blocks']:>7} {f['train_positives']:>7} "
              f"{f['train_background']:>7} {f['dropped_from_train']:>8} "
              f"{f['min_train_to_test_m']:>10}")
    print(f"\nwritten -> {OUT / 'fold_summary.json'}")


if __name__ == "__main__":
    main()
