# Run Report RUN-2026-10-28-03 — Phase 5 Random Forest susceptibility baseline

**Date:** 2026-10-28 · **Session goal:** the user explicitly moved RESQAI to Phase 5
(modelling): one interpretable, reproducible Random Forest baseline on the committed Phase 4
points and spatial folds — extraction, per-fold evaluation, labelled map, verification,
documentation.
**Starting state:** commit `81da3a8`, tree clean; Phase 4 verified (8/8).
**End state:** commit **`355b0c0`** (work) + this report's commit; all gates and consistency
suites green; nothing pushed.

## 1. What was run, in order

| # | Action | Result |
|---|---|---|
| 1 | Pre-flight: all 10 authoritative Phase 4 files present | OK |
| 2 | Predictor-stack facts re-confirmed: `data/processed/qa/layer_inventory.csv` (24 layers / 35 bands, one grid); `p3_soil.py` already applied SoilGrids scale factors; `p3_rainfall.py` already masked CHIRPS −9999 | extraction must not re-apply/re-mask; assert instead |
| 3 | `python scripts/p4_verify.py` + point-metadata comparison | **8/8 gates PASS**; `fold_assignments` ≡ `modelling_points` |
| 4 | wrote `configs/p5_baseline.json` | seeds, model, fold rule, metrics text, 35-feature spec, map rules, 8 limitations |
| 5 | wrote + ran `scripts/p5_extract_features.py` | 9/9 checks PASS → features_point_table.csv + extraction_checks.json |
| 6 | wrote + ran `scripts/p5_train_baseline.py` | folds asserted vs fold_summary BEFORE fitting; 5 models + fold_metrics.json + 2 figures |
| 7 | server restart interrupted run 6 mid-flight | re-ran script from scratch (deterministic); clean completion |
| 8 | wrote + ran `scripts/p5_map.py` | gates asserted from saved JSONs; map tif + PNG + map_metadata.json |
| 9 | wrote + ran `scripts/p5_verify.py` | **6/6 gates PASS → ALL PHASE 5 GATES PASSED** |
| 10 | `.gitignore` negation; AGENTS.md phase update; PHASE4_PROGRESS.md status note (needle-safe); wrote `docs/PHASE5_PROGRESS.md` | done |
| 11 | p4/p3/p2 consistency checkers + `git diff --check` | 116/116 · 470/470 · pass · clean |
| 12 | commit | `355b0c0` |

## 2. Measured values (quote, do not re-derive)

* **Extraction:** 2,460 points × 35 features; all finite; no declared nodata at points; rainfall
  min at points 2.8253 (> −9998); landcover classes at points {10, 30, 40, 50, 60, 80};
  geology {1, 2, 3, 4, 5}; provenance round-trip byte-equal to `fold_assignments.csv`;
  one grid (2013×2480, 30 m, EPSG:32643) across all 24 layers + mask.
* **Per-fold (spatially held-out presence-background ranking):**
  f0 AUC 0.8674 / AP 0.3517 (52+/419−, 12 clusters, train 298+/1558−, 133 drops);
  f1 0.8712 / 0.5458 (121+/420−, 14, train 235+/1616−, 68);
  f2 **0.9263 / 0.6168 (84+/419−, ⚠ 5 clusters, train 276+/1556−, 125)**;
  f3 0.7882 / 0.3200 (54+/419−, 23, train 308+/1634−, 45);
  f4 0.7720 / 0.3348 (52+/420−, 22, train 309+/1632−, 47).
  Unweighted mean ± sd (correlated folds, not independent): AUC 0.8450 ± 0.0640,
  AP 0.4338 ± 0.1374. **No pooled score reported.**
* **Permutation importance (held-out, ROC-AUC scoring, 20 repeats):** slope 0.0273 ± 0.0139;
  elevation 0.0134 ± 0.0156; all other features ≤ 0.0028.
* **Map:** domain 2,343,343 cells (= district 2,356,538 − 13,195 invalid-predictor);
  float32, nodata −9999, EPSG:32643; vote share min 0.0000 / median 0.0316 / mean 0.1474 /
  p95 0.6594 / max 0.9687; tif sha256 `88687c89…` (full value in map_metadata.json).
* **Versions:** Python 3.14.6, numpy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1,
  rasterio 1.5.2, joblib 1.5.2, matplotlib 3.10.7.

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | `p5_extract_features.py` grid check | `str(ds.transform)` vs `str(tuple(...))` — Affine's `__str__` omits parentheses, so an identical transform failed the string comparison (gate 1 false-FAIL) | compare `tuple(affine)[:6]` numerically against `grid_spec.json` |
| 2 | server restart | training run interrupted after the 5 joblib dumps but before metrics/figures | re-ran the script from scratch; deterministic seeds made regeneration identical; verifier gate 6 later byte-compared all outputs |

## 4. Gate / verification status

| Suite | Result |
|---|---|
| `p4_verify.py` (inside p5 gate 1) | **8/8 PASS** |
| `p5_verify.py` | **6/6 PASS — ALL PHASE 5 GATES PASSED**: Phase 4 authority; feature-table integrity; fold usage ≡ Phase 4 authority; evaluation completeness + **saved models recompute their recorded AUC/AP exactly**; map checks (profile/domain/stats/sha/label); **byte-identical regeneration of all 14 outputs** |
| p4 / p3 / p2 consistency | 116/116 · 470/470 · pass (after PHASE4_PROGRESS.md edits — "no model exists" needle kept truthful by scoping it to the Phase 4 outputs) |
| `git diff --check` | clean |

## 5. Outputs produced

Committed (`355b0c0`): `configs/p5_baseline.json`; `scripts/p5_extract_features.py`,
`p5_train_baseline.py`, `p5_map.py`, `p5_verify.py`;
`data/processed/models/{features_point_table.csv, extraction_checks.json, fold_metrics.json,
map_metadata.json, roc_curves.png, permutation_importance.png, susceptibility_rf_baseline.png}`;
`data/interim/p5/verify_p5.json`; `docs/PHASE5_PROGRESS.md`; `docs/PHASE4_PROGRESS.md`
(status update); `AGENTS.md` (phase update); `.gitignore` (models negation with joblib/tif
re-ignored). **Local only** (regenerate byte-identically; sha256 recorded in committed
metadata): 5× `fold_<f>_rf.joblib`, `final_rf_refit_all_points.joblib`,
`susceptibility_rf_baseline_30m.tif`.

## 6. Current project state

Phase 5 baseline complete and verified. What exists now, and only this: the feature table,
five fold models + one final refit, per-fold ranking metrics with limitations attached,
permutation importance, and ONE labelled susceptibility map (relative ranking conditional on
the observed inventory; not a probability/forecast/warning/timing prediction). Chain:
`355b0c0` ← `81da3a8` ← `889da2c` ← `821e256` ← `554702c` ← `570af94`.

## 7. Next-step handoff (prompt material)

* **Awaiting user decisions:** whether to (a) keep this baseline as the standing reference and
  stop here, (b) authorise sensitivity of results to model settings (never tuning toward fold
  scores), (c) pursue GSI 1:50,000 geology or a multi-year inventory before any further
  modelling.
* **Do not re-derive (quote from docs/PHASE5_PROGRESS.md):** all §2 values above; fold 2 is
  marginal (5 clusters) and its scores must be discounted; the mean-of-folds is correlated,
  not independent; no pooled score exists.
* **Standing constraints for any next run:** train only on the committed folds; every number
  is a presence-background ranking metric beside its limitations; the map label text is
  mandatory on any rendering; categorical layers are never interpolated; CHIRPS −9999 is
  asserted at extraction; SoilGrids factors are already applied.
* **Quick commands:** `python scripts/p5_verify.py` (~10–20 min, regenerates everything and
  byte-compares) · `python scripts/p4_verify.py` · p4/p3/p2 checkers.
* **Open observational item:** the map shows block-scale regional structure (expected under
  spatially adjacent folds) — read cell-wise, not as a seamless surface.
