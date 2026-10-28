# RESQAI — Phase 5 Progress Report

**Phase:** 5 — modelling: Random Forest susceptibility baseline for Wayanad.
**Started:** 2026-10-28, explicitly authorised by the user (AGENTS.md phase moved the same day).
**Config authority:** `configs/p5_baseline.json` (single source of truth for seeds, model
settings, feature order, fold usage, map rules; sha256 recorded in every output JSON).
**Standing label rule:** every product of this phase is a *relative susceptibility ranking
conditional on the observed inventory* (92.3 % of labels from 2018). Nothing here is a
probability of failure, and nothing here is a forecast, warning, or timing prediction —
susceptibility estimates *where* conditions favour failure, never *when* failure will occur.

Sections 2–6 record **confirmed results** (measured on saved files; models audited by
independent recomputation; full pipeline byte-reproducible). Section 7 lists **limitations**.
Section 8 holds **interpretation and recommendations only**. Section 9 states status.

---

## 1. Purpose and scope

One interpretable Random Forest baseline, one fixed configuration, trained and evaluated
strictly on the committed Phase 4 points and spatial folds:

* extract the documented predictor stack at the 2,460 committed points (no resampling,
  source rasters read-only);
* for each of the 5 outer folds, train on the other folds minus the committed 1,000 m
  buffer drops, predict only that held-out fold, and report per-fold presence-background
  ranking metrics;
* quantify interpretability via permutation importance on held-out folds;
* produce ONE labelled susceptibility map (final refit, after gates).

Out of scope by instruction: hyperparameter search, XGBoost or any competing model, synthetic
events, any pooled headline score, any temporal split.

## 2. Design as configured (confirmed from `configs/p5_baseline.json`)

| Item | Value |
|---|---|
| Model | `sklearn.ensemble.RandomForestClassifier`, 500 trees, gini, `min_samples_leaf=5`, `max_features="sqrt"`, bootstrap, `class_weight="balanced_subsample"`, `random_state=20261026`, `n_jobs=-1` |
| Rationale (recorded) | single fixed config, no tuning: 500 trees for stable importances; leaf 5 against single-cell noise; class weighting so the arbitrary 5.78:1 background density does not dominate the fit |
| Class handling | positive = audited event point (label 1, 363); background = *no mapped landslide in the available inventory* (label 0, 2,097) — never confirmed stable ground |
| Fold usage | test(f) = all points with fold==f; train(f) = fold≠f **minus** `fold_drops.csv` rows with fold==f; counts asserted equal to `fold_summary.json` before fitting; no random split, no reassignment |
| Metrics | per-fold ROC-AUC + average precision — **spatially held-out presence-background RANKING metrics** (case-control); folds correlated; unweighted mean reported with a caveat, never presented as independent |
| Interpretability | permutation importance, held-out folds, scoring roc_auc, 20 repeats, seed 20261026 |
| Software | Python 3.14.6, numpy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1, rasterio 1.5.2, joblib 1.5.2 (all recorded in output JSONs) |

## 3. Data and feature extraction (confirmed)

`scripts/p5_extract_features.py` samples the **24 Phase 3 layers (35 bands)** at the
containing 30 m cell of every point — no interpolation, categoricals included. All 9
extraction checks passed:

* grid alignment: all 24 layers + district mask share exactly one grid, equal to
  `grid_spec.json` (2013 × 2480, 30 m, EPSG:32643);
* all 2,460 points map in bounds; all 35 × 2,460 sampled values finite; no value equals a
  declared nodata; no rainfall value ≤ −9998 (sentinel rule re-asserted);
* soil features in physical units (SoilGrids scale factors were **already applied** in
  `scripts/p3_soil.py`; Phase 5 does **not** re-apply them), inside plausible ranges;
* categorical classes observed at points: land cover {10, 30, 40, 50, 60, 80} ⊆ WorldCover
  codes; geology {1, 2, 3, 4, 5} — full class sets; label-encoded (documented simplification);
* provenance: the 12 provenance columns round-trip byte-equal to `fold_assignments.csv`;
  per-fold test counts equal `fold_summary.json`.

Output: `data/processed/models/features_point_table.csv` (2,460 rows; 12 provenance + 35
feature columns in fixed config order) and `extraction_checks.json` (with sha256 of every
input raster).

## 4. Per-fold results (confirmed; READ THE LABEL BESIDE THEM)

Constructed folds were asserted equal to `fold_summary.json` before fitting. Metrics are
**spatially held-out presence-background ranking metrics**:

| Fold | Test support (+/−) | Test clusters | Train support (+/− after drops) | Drops | ROC-AUC | Avg. precision |
|---|---|---|---|---|---|---|
| 0 | 52 / 419 | 12 | 298 / 1,558 | 133 | **0.8674** | **0.3517** |
| 1 | 121 / 420 | 14 | 235 / 1,616 | 68 | **0.8712** | **0.5458** |
| 2 ⚠ | 84 / 419 | **5** | 276 / 1,556 | 125 | **0.9263** | **0.6168** |
| 3 | 54 / 419 | 23 | 308 / 1,634 | 45 | **0.7882** | **0.3200** |
| 4 | 52 / 420 | 22 | 309 / 1,632 | 47 | **0.7720** | **0.3348** |
| unweighted mean ± sd | — | — | — | 418 | 0.8450 ± 0.0640 | 0.4338 ± 0.1374 |

**Fold 2 is flagged marginal: 84 positives but only 5 distinct clusters (the configured
minimum). Its high scores must be discounted accordingly.**

What these numbers are, stated beside the results: ROC-AUC here is the probability that a
random mapped event point ranks above a random background point, in a model trained on
spatially disjoint folds; average precision is ranking quality under heavy background
prevalence. They are **not** accuracy on all Wayanad landslides, **not** performance on
confirmed absences (background is "no mapped event in the available inventory"), and **not**
calibrated skill. Folds are spatially adjacent and correlated; the mean is not an
independent-replication estimate and no pooled score is reported. The inventory is 92.3 %
single-year (2018), so scores characterise that event population; the only temporal test
would rest on 28 non-2018 labels across 17 clusters — not viable, so temporal transfer is
**untested**.

Permutation importance (held-out folds, mean decrease in ROC-AUC under permutation):
`dem_slope_deg` 0.0273 ± 0.0139 dominates; `dem_elev_m` 0.0134 ± 0.0156; everything else
≤ 0.0028 with overlapping uncertainty. Interpretive only, not a performance claim.

## 5. Susceptibility map (confirmed; produced only after gates)

`scripts/p5_map.py` asserts the extraction and fold-evaluation verdicts before fitting.

* **Domain:** 2,343,343 cells = district (2,356,538) − 13,195 invalid-predictor cells;
  everything else nodata −9999 (declared).
* **Model:** the same single configuration refit on ALL 2,460 points. This final model is
  **not cross-validated**; its skill characterisation is the per-fold evaluation above.
* **Value:** positive-class vote share (`predict_proba[:, 1]`) — a relative ranking, not a
  calibrated probability. Observed range at valid cells: min 0.0000, median 0.0316, mean
  0.1474, p95 0.6594, max 0.9687.
* **Label (in metadata and on the figure):** "relative landslide susceptibility ranking
  conditional on the observed inventory (92.3 % of labels from 2018); not a probability,
  forecast, warning, or timing prediction".
* Outputs: `susceptibility_rf_baseline_30m.tif` (float32, EPSG:32643, sha256 `88687c89…`
  — recorded in `map_metadata.json`; stays local, regenerates byte-identically),
  `susceptibility_rf_baseline.png`, `map_metadata.json`, `final_rf_refit_all_points.joblib`.

## 6. Verification (confirmed)

`scripts/p5_verify.py` — **6/6 gates passed, ALL PHASE 5 GATES PASSED** (2026-10-28):

1. Phase 4 authority intact — `p4_verify.py` re-run: 8/8;
2. feature-table integrity — provenance byte-equal to Phase 4 assignments, 35 features in
   config order, all finite, sentinel and categorical rules hold;
3. fold usage matches Phase 4 authority — all 5 folds rebuilt from `fold_assignments.csv` +
   `fold_drops.csv` equal `fold_summary.json` and the recorded metric counts; test folds
   partition all 2,460 points; no random split;
4. evaluation completeness + model audit — fold 2 flagged marginal, correlation caveat and
   limitations present, model params equal config, and **each saved fold model recomputes
   its recorded AUC/AP exactly** (f0 0.8674/0.3517 … f4 0.7720/0.3348);
5. map checks — profile (float32, nodata −9999, EPSG:32643, 2013×2480), domain 2,343,343,
   stats recomputed from the tif equal the metadata, disclaimers present, tif sha256 matches;
6. reproducibility — all three scripts re-run; **all 14 outputs byte-identical**.

`data/interim/p5/verify_p5.json` is the saved evidence.

## 7. Limitations (carried into every reading of the results)

1. 92.3 % single-year (2018) inventory: scores characterise that event population, not all
   Wayanad landslides; no viable temporal holdout exists (28 non-2018 labels, 17 clusters) —
   temporal transfer is untested.
2. Background labels mean "no mapped event in the available inventory", not confirmed stable
   terrain; the 5.78:1 background:positive ratio is a sampling-design artefact (mitigated
   in-fit by class weighting).
3. Folds are spatially adjacent and correlated; per-fold scores are not independent
   replications, and the mean-of-folds is reported with that caveat only.
4. Fold 2 is marginal (5 clusters); its scores are the least trustworthy despite being the
   highest.
5. Categorical predictors (land cover, geology) enter as integer codes; aspect enters
   linearly despite being circular — documented baseline simplifications.
6. Training near misses and survey effort are unmodelled: the inventory reflects where
   mapping happened, not everywhere landsliding happened.
7. The map's visible block-scale regional structure reflects learning on spatially adjacent
   folds; regional differentiation of the vote share is expected and is a reason to read the
   map as a ranking, cell by cell, rather than as a seamless surface.
8. Geology is GLiM at 1:3.75 M (GSI 1:50,000 still missing); one RF configuration was run —
   no sensitivity of results to model settings has been measured.

## 8. Interpretation and recommendations (not confirmed results)

* The fold spread (0.772–0.926) and the drop in AP on folds 3–4 are consistent with
  regionally varying event populations under a single-year inventory; read per fold, with
  fold 2 discounted.
* Slope's dominance is consistent with the terrain controls expected for shallow
  landsliding, but with only this inventory it cannot be claimed as a validated process
  finding.
* Sensible next steps, each requiring its own authorisation: GSI 1:50,000 geology when
  obtainable; a multi-year inventory to enable a temporal test; only then any model
  comparison or configuration sensitivity — never tuning toward the fold scores.

## 9. Current project status

Phase 5 baseline is **complete and verified** (6/6 gates; Phase 4 8/8 gates re-confirmed;
byte-identical regeneration). What exists now, and only this: the feature table, the five
fold models + final refit, per-fold ranking metrics with limitations, permutation
importance, and one labelled susceptibility map. Run report:
`reports/RUN-2026-10-28-03_phase5-rf-baseline.md`. Any further modelling (tuning, model
comparison, synthetic events, hazard-vs-susceptibility framing) needs explicit user
authorisation.
