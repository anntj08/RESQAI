"""Diagnostic: block-unit structure for the block-based fold rewrite.

Measures, before anything is finalised:
  * how the 3 km block grid covers positives + background (non-negative indexing);
  * how blocks merge through shared clusters (unit sizes);
  * whether 5 folds over block units can satisfy support (>=45 positives,
    >=5 clusters) and what spread / buffer losses result;
  * the same for 3 and 4 folds as fallback.

Read-only; prints a report. Run:  python data/interim/p4/diag_units.py
"""
import json
import pathlib

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.spatial import cKDTree
from sklearn.cluster import KMeans

ROOT = pathlib.Path(__file__).resolve().parents[3]
CFG = json.loads((ROOT / "configs" / "p4_sampling.json").read_text(encoding="utf-8"))
SAMP = ROOT / "data" / "processed" / "sampling"

MINP, MINC = 45, 5


def block_id(x, y, tf, B):
    bbx = np.floor((x - tf.c) / B).astype(int)
    bby = np.floor((tf.f - y) / B).astype(int)
    assert (bbx >= 0).all() and (bby >= 0).all(), "negative block index"
    return bby * 10_000 + bbx


def block_centre(bid, tf, B):
    bby, bbx = divmod(int(bid), 10_000)
    return tf.c + (bbx + 0.5) * B, tf.f - (bby + 0.5) * B


def union_find(n, pairs):
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for a, b in pairs:
        ra, rb = find(int(a)), find(int(b))
        if ra != rb:
            parent[rb] = ra
    return np.array([find(i) for i in range(n)])


def build(pxy, p_blocks, gap, k, seed, tf, B, extra_blocks=None, extra_counts=None):
    pairs = cKDTree(pxy).query_pairs(gap, output_type="ndarray")
    _, cid = np.unique(union_find(len(pxy), pairs), return_inverse=True)
    ncl = int(cid.max() + 1)
    blocks = (np.unique(np.concatenate([p_blocks, extra_blocks]))
              if extra_blocks is not None else np.unique(p_blocks))
    index = {int(b): i for i, b in enumerate(blocks)}
    merge = []
    for c in range(ncl):
        bs = sorted({int(index[int(b)]) for b in p_blocks[cid == c]})
        for b in bs[1:]:
            merge.append((bs[0], b))
    lab = union_find(len(blocks), np.array(merge) if merge else np.zeros((0, 2), np.int64))
    _, unit = np.unique(lab, return_inverse=True)
    units = pd.DataFrame({"block": blocks, "unit": unit})
    cx, cy = zip(*[block_centre(b, tf, B) for b in blocks])
    units["cx"], units["cy"] = cx, cy
    npos = pd.Series(p_blocks).value_counts()
    units["n_pos"] = units["block"].map(npos).fillna(0)
    nclu = pd.DataFrame({"b": p_blocks, "c": cid}).drop_duplicates().groupby("b").size()
    units["n_clu"] = units["block"].map(nclu).fillna(0)
    if extra_counts is not None:
        units["n_bg"] = units["block"].map(extra_counts).fillna(0)
    else:
        units["n_bg"] = 0

    def stats(fold_arr):
        pos = np.bincount(fold_arr, weights=units["n_pos"], minlength=k).astype(int)
        clu = np.bincount(fold_arr, weights=units["n_clu"], minlength=k).astype(int)
        bgc = np.bincount(fold_arr, weights=units["n_bg"], minlength=k).astype(int)
        return pos, clu, bgc

    # k-means weighted by positives
    km = KMeans(n_clusters=k, random_state=seed, n_init=100).fit(
        units[["cx", "cy"]].to_numpy(), sample_weight=(units["n_pos"] + 1).to_numpy())
    fold = km.labels_.astype(int)

    # hill-climb: minimise (support deficit, positive spread, background spread)
    for _ in range(500):
        pos, clu, bgc = stats(fold)
        deficit = (int(np.clip(MINP - pos, 0, None).sum())
                   + 100 * int(np.clip(MINC - clu, 0, None).sum()))
        spread = int(pos.max() - pos.min())
        bg_spread = int(bgc.max() - bgc.min())
        best = (deficit, spread, bg_spread)
        best_move = None
        for u in range(len(units)):
            f0 = fold[u]
            pf = pos.copy(); pf[f0] -= units["n_pos"][u]; pf_new = pf
            cf = clu.copy(); cf[f0] -= units["n_clu"][u]
            bf = bgc.copy(); bf[f0] -= units["n_bg"][u]
            for t in range(k):
                if t == f0:
                    continue
                p2 = pf.copy(); p2[t] += units["n_pos"][u]
                c2 = cf.copy(); c2[t] += units["n_clu"][u]
                b2 = bf.copy(); b2[t] += units["n_bg"][u]
                d2 = (int(np.clip(MINP - p2, 0, None).sum())
                      + 100 * int(np.clip(MINC - c2, 0, None).sum()))
                s2 = (d2, int(p2.max() - p2.min()), int(b2.max() - b2.min()))
                if s2 < best:
                    best, best_move = s2, (u, t)
        if best_move is None:
            break
        u, t = best_move
        fold[u] = t

    pos, clu, bgc = stats(fold)
    p_fold = fold[unit[np.asarray([index[int(b)] for b in p_blocks])]]
    return cid, p_fold, ncl, fold, units, (pos, clu, bgc)


def main():
    audit = pd.read_csv(SAMP / "eligibility_audit.csv")
    pos = audit[audit["p4_use"] == "POSITIVE_EVENT"]
    inv = pd.read_csv(ROOT / "data/processed/inventory/inventory_spatial_suitability.csv"
                      ).set_index("source_record_id")
    tr = Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)
    px, py = [np.asarray(v) for v in tr.transform(
        inv.loc[pos["source_record_id"], "lon_original"].to_numpy(float),
        inv.loc[pos["source_record_id"], "lat_original"].to_numpy(float))]
    bg = pd.read_csv(SAMP / "background_samples.csv")

    with rasterio.open(ROOT / CFG["grid"]["district_mask"]) as ds:
        tf = ds.transform
    B = float(CFG["spatial_validation"]["block_size_m"])
    gap = float(CFG["spatial_validation"]["buffer_gap_m"])
    seed = int(CFG["random_seed"])

    pxy = np.c_[px, py]
    p_blocks = block_id(px, py, tf, B)
    b_blocks = block_id(bg["x_32643"].to_numpy(float), bg["y_32643"].to_numpy(float), tf, B)
    bg_counts = pd.Series(b_blocks).value_counts().to_dict()

    print(f"positives {len(pxy)}  blocks P {len(np.unique(p_blocks))}  "
          f"blocks B {len(np.unique(b_blocks))}  total {len(np.unique(np.r_[p_blocks, b_blocks]))}")

    for k in (5, 4, 3):
        cid, p_fold, ncl, u_fold, units, (posf, cluf, bgf) = build(
            pxy, p_blocks, gap, k, seed, tf, B,
            extra_blocks=b_blocks, extra_counts=bg_counts)
        n_units = int(units["unit"].nunique())
        print(f"\nk={k}: units {n_units}  clusters {ncl}")
        print(f"  positives/fold {posf.tolist()}  clusters/fold {cluf.tolist()}  "
              f"background/fold {bgf.tolist()}")
        print(f"  spread {posf.max() - posf.min()}  ok={bool((posf >= MINP).all() and (cluf >= MINC).all())}")
        # buffer losses
        tot = kept_min = 0
        kept_min = np.inf
        dropp = 0
        for f in range(k):
            test = pxy[p_fold == f]
            rest = pxy[p_fold != f]
            d = cKDTree(test).query(rest, k=1)[0]
            dropp += int((d <= gap).sum())
            if (d > gap).any():
                kept_min = min(kept_min, float(d[d > gap].min()))
        print(f"  dropped from train (positives, all folds): {dropp}, "
              f"min kept gap {kept_min:.1f} m")
        sizes = units.groupby("unit")["n_pos"].sum().sort_values(ascending=False)
        print(f"  unit sizes desc (top 8): {sizes.head(8).astype(int).tolist()}")
        n_blocks_per_unit = units.groupby("unit").size().sort_values(ascending=False)
        print(f"  blocks/unit desc (top 5): {n_blocks_per_unit.head(5).astype(int).tolist()}")


if __name__ == "__main__":
    main()
