# RESQAI — Phase 4: Spatial Validation Report

**Phase:** 4 (sampling and validation design). **Status:** executed and verified; no model exists.
**Config authority:** `configs/p4_sampling.json`; fold outputs in
`data/processed/sampling/{spatial_blocks,fold_assignments,fold_drops,modelling_points}.csv`
and `fold_summary.json`.
**Rule:** this phase designs and verifies the validation; it trains nothing and reports no
metric. Any susceptibility surface built on these folds later remains **not a forecast**,
warning or timing prediction (`MODELLING_TARGET_DECISIONS.md`).

---

## 1. Why not a random split

The 363 positives are strongly clustered: 318 of them have another positive within 1 km
(median nearest-neighbour distance 335 m). A random split would put immediate neighbours of the
same hillslope on both sides of the partition, so any later evaluation would partly memorise
shared terrain rather than test spatial transfer. The inventory's own clustering is the leak.

## 2. The design in five steps (decisions V1–V5)

1. **CLUSTER (V2).** Positives are clustered by single linkage at **1,000 m** → **76 clusters**.
   A cluster is atomic: two mapped events within one neighbourhood are never divided between
   folds. The same distance doubles as the buffer gap — one neighbourhood scale.
2. **BLOCK (V1).** The district is tiled into whole **3,000 m** squares aligned to the analysis
   grid (non-negative indexing, unique `bby*10000+bbx` ids). Every analysis point (positive or
   background) belongs to exactly one block; **271 blocks contain points** (73 hold positives).
   Blocks are the atom of assignment — **no block is ever split across folds**.
3. **UNIT.** Blocks sharing a cluster are merged into block units (a cluster crossing block
   boundaries cannot be split): **241 units**, the largest spanning 13 blocks and carrying the
   121-positive agglomeration.
4. **FOLD (V3, V4).** Units are grouped into **5 folds**. Assignment is a **deterministic
   12-candidate sweep**: seeds 20261026–20261037, each a weighted k-means on unit centroids
   followed by a hill-climb that moves whole units to minimise, in order, (a) support deficit
   below the minimums, (b) spread of fold positive counts, (c) tie-break: spread of fold
   background counts. The best end state wins; ties fall to the lowest candidate. The
   assignment is therefore a deterministic function of (data, config): **chosen candidate seed
   20261028, final score [0, 0, 69, 1]** (0 support deficit, 0 cluster deficit, positive spread
   69, background spread 1), 31 repair moves.
5. **BUFFER (V5).** For each fold, every training point within **1,000 m** of *any* test point
   is **dropped** from that fold's training set, with the drop recorded per point
   (`fold_drops.csv`: fold, point id, role, its own fold, distance to the test set, reason).
   Blocks alone leave adjacent folds touching; the buffer creates — and the verification
   re-measures — the gap.

**Support thresholds (config, rationale recorded):** every fold must hold ≥ **45 test
positives** (~12 % of the inventory) and ≥ **5 distinct 1 km clusters** (a fold whose positives
are one agglomeration has effectively one independent location).

## 3. The five folds, measured

| Fold | Test + | Test − | Clusters | Blocks | Train + | Train − | Dropped from train (+ of them) | Min retained train→test gap |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 52 | 419 | 12 | 47 | 298 | 1,558 | 133 (13) | 1,006.2 m |
| 1 | 121 | 420 | 14 | 56 | 235 | 1,616 | 68 (7) | 1,012.0 m |
| 2 | 84 | 419 | **5** | 61 | 276 | 1,556 | 125 (3) | 1,001.3 m |
| 3 | 54 | 419 | 23 | 53 | 308 | 1,634 | 45 (1) | 1,004.6 m |
| 4 | 52 | 420 | 22 | 54 | 309 | 1,632 | 47 (2) | 1,011.5 m |
| Σ | 363 | 2,097 | 76 | 271 | — | — | **418 (26)** | **1,001.3 m** |

Reading of the table:

* **Unequal positives [52, 121, 84, 54, 52] are structural, not a bug.** The largest unit (the
  121-positive, 100-cluster agglomeration) is atomic and cannot be divided; a 12-seed
  measurement places the achievable spread at **69**, which the sweep attains. k=10 fails
  support outright (fold positives 12–34 < 45). k=3 balances ([121,121,121], min 14 clusters)
  but leaves only three evaluation units; k=5 was kept.
* **Fold 2 is the marginal fold:** 84 positives but only **5 distinct clusters** — the entire
  south-eastern single-cluster region. It meets the configured minimum exactly and must be
  flagged whenever its results are read.
* **Drops are audited, not silent:** 418 rows (392 background, 26 positive rows — 395 unique
  points, i.e. 23 points were dropped in more than one fold's buffer). Every dropped positive
  sits near a *neighbouring fold's background*; no positive is ever dropped near a test
  positive, because same-neighbourhood pairs are one cluster and one fold by construction.
* **Buffer comparison (the "blocked vs random" argument, measured):** with no buffer (gap 0)
  the closest cross-fold training/test pair is **150.0 m** — closer than the positives' own
  median NN (335 m): folds touch, which is the random-split failure mode. Gap 500 m → 69
  dropped, gap 1,000 m (chosen) → 418 dropped and a verified 1,001.3 m gap, gap 2,000 m →
  1,399 dropped including 140 positives (too costly for the training budget).

## 4. Leakage checks — verified, not assumed

`scripts/p4_verify.py` gates 6–7 recompute from the **saved assignments**
(`fold_assignments.csv` + `fold_drops.csv`), not from the fold script's own report:

* **0 mixed-fold 3 km blocks** (recomputed per block from the saved per-point folds);
* all **363 event groups**, **76 clusters** and **271 blocks** each lie in exactly one fold;
* per-fold support meets the configured 45-positive / 5-cluster minimums in all five folds;
* every `fold_drops.csv` row's point id **and recorded distance** match an independent
  recomputation of the buffer (paired **by point_id** — the row order of the drop file is the
  generator's, not the assignments' sort order; pairing by row position was a caught-and-fixed
  verification bug);
* the **retained minimum train→test gap, recomputed independently, is 1,001.3 m > 1,000 m
  configured** — the buffer is enforced, not decorative;
* gate 8 re-runs all three Phase 4 scripts and byte-compares all nine outputs (same data,
  same config, same seed → identical files).

## 5. Sensitivity of the validation design (all measured, nothing retrained)

| Dimension | Variants → measured outcome |
|---|---|
| Clustering distance | 500 m → 186 clusters (largest 17), min 30 clusters/fold; **1,000 m → 76 (largest 100), min 7**; 2,000 m → 26 (largest 140), min fold positives 28 and 1 cluster/fold — **fails both support minimums** |
| Fold count k | k=3 → [121,121,121], min 14 clusters; **k=5 → chosen**; k=10 → fold positives 12–34, **fails 45** |
| Inclusion rule | primary 363 points/76 clusters; +undated sites 401/81 (min fold 59); +undated+pre-2000 407/81 (min fold 54) — including the 78 undated records would not collapse the folds, but stays excluded because the label window needs dates |
| Buffer gap | 0/500/1000/2000 m → closest cross-fold pair 150.0 m / 510.0 m / 1,001.3 m / 2,001.2 m; dropped 0/69/418/1,399 |
| Temporal holdout | not viable (see `MODELLING_TARGET_DECISIONS.md` §3): 28 non-2018 labels in 17 clusters, min NN 82.4 m to the 2018 mass; reverse direction not attempted |

One honest caveat on the sensitivity harness: its fold-assignment helper passes no background
blocks, so its k=5 arrangement is **[86, 121, 52, 52, 52]** with min 7 clusters/fold, whereas
the production assignment (which also breaks ties on background counts) is **[52, 121, 84, 54,
52]**. Both meet the support thresholds; the sensitivity conclusions about support and
clustering distance hold under both arrangements. The difference is documented, not hidden.

## 6. What these folds do not guarantee (standing disclaimers)

1. **Spatial independence is not asserted.** The buffer removes training points from the
   immediate neighbourhood of each test fold; adjacent folds still share terrain, land cover
   and rainfall history. Per-fold results will remain correlated to an unmeasurable degree.
2. **Folds are not hydrological or administrative units.** They are sets of whole blocks and may
   form several patches; contiguity was not a design goal, atomicity was.
3. **Background labels are not confirmed absence** — fold composition inherits every limitation
   in `SAMPLING_STRATEGY_REPORT.md` §6.
4. Fold-level numbers in this report are **design properties, not performance**: no model
   exists, so nothing here is an accuracy, AUC, F1 or skill figure.

## 7. Confirmed facts vs assumptions

**Confirmed (measured):** 76 clusters / 241 units / 271 blocks; 0 mixed-fold blocks; chosen
candidate seed 20261028, score [0,0,69,1]; fold positives [52,121,84,54,52], spread 69;
fold 2 holds 5 clusters; 418 drops (392 background + 26 positive rows, 395 unique points);
retained gap 1,001.3 m > 1,000 m; all checks above independently recomputed from the saved
files (8/8 verification gates pass).

**Assumptions (judgements, rationale recorded in config):** 3 km blocks (above the 1 km
clustering scale, ~5 positives per non-empty block); 1 km cluster/buffer distance (the scale at
which the inventory resolves neighbourhoods); k=5 (balancing evaluation units against fold
support); support minimums 45/5; whole-block assignment rather than per-point assignment.
