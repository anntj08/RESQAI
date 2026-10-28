# Run Report RUN-2026-10-28-01 — Phase 4 completed: sampling + spatial validation design, verified and committed

**Date:** 2026-10-28 · **Session goal:** execute the Phase 4 fold design, verification gates,
sensitivity, documentation and consistency layer; commit.
**Starting state:** Phase 3 baseline `570af94` verified. From earlier Phase 4 runs: eligibility
audit already executed (468 records → 363 positives); background sampler staged with the
exact-separation fix **but not yet executed**; block-unit fold rewrite pending; verify and
sensitivity rewrites pending; no docs, no checker, no commit.
**End state:** commit **`554702c`** ("Complete Phase 4 sampling and spatial validation design"),
working tree **clean**, all suites green, nothing pushed.

---

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | edit `configs/p4_sampling.json` | add block-unit design wording, support minimums 45/5, clustering threshold 1,000 m | config sha `72d41377…e6f7a` |
| 2 | `python data/interim/p4/diag_units.py` | measure block/unit structure before finalising folds | 363 positives in 73 blocks; 271 background blocks; 241 units; k=5 feasible (unit sizes top: 121, 84, 32) |
| 3 | `python scripts/p4_sample_background.py` | exact-separation background sample | eligible 2,330,499 cells = 2,097.45 km² = 98.895 %; band 3,348 kept / 435 rejected by exact test; 2,097 samples; 5.78/positive; exact min separation 113.7 m; seed 20261026 |
| 4 | rewrite `scripts/p4_spatial_folds.py` | block-unit fold design with buffer + drop audit | first run: clusters 76, units 241, blocks 271; positives/fold [121,84,62,48,48], spread 73; 0 mixed-fold blocks |
| 5 | `python data/interim/p4/diag_seeds.py` | 12-seed sweep measurement | seed 20261028 reaches spread 69 (the floor); 11 others stuck at 73 |
| 6 | edit `scripts/p4_spatial_folds.py` + config | deterministic 12-candidate sweep inside `assign_positive_folds` (`N_CANDIDATE_SEEDS = 12`) | final: chosen seed **20261028**, score [0,0,69,1]; **[52, 121, 84, 54, 52]**; 0 mixed blocks |
| 7 | rewrite `scripts/p4_verify.py` | 8 gates, gates 6–7 recompute from saved assignments | after pairing fix: **8/8 PASS** |
| 8 | update + run `scripts/p4_sensitivity.py` | parameter sweeps with new signatures | §1 re-written to exact-separation rule; all sections measured (see §2) |
| 9 | edit `scripts/build_manifest.py` + regenerate | add P4-01…P4-06 | `docs/data_manifest.csv` → **43 datasets**, 16 cols |
| 10 | edit `scripts/p3_check_consistency.py` | relax manifest exact-total (=37) to presence+uniqueness of P2 ids (Phase 2 checker precedent, reason inline) | **470 checks pass** |
| 11 | edit `.gitignore` | `!data/processed/sampling/` + `!**` negation | `git check-ignore` confirms trackable |
| 12 | write 4 docs | target decisions, sampling strategy, spatial validation, progress log | `docs/MODELLING_TARGET_DECISIONS.md`, `docs/SAMPLING_STRATEGY_REPORT.md`, `docs/SPATIAL_VALIDATION_REPORT.md`, `docs/PHASE4_PROGRESS.md` |
| 13 | write + run `scripts/p4_check_consistency.py` | doc-vs-data assertions | **116 checks pass** (after 3 fixes, §3) |
| 14 | full suite + `git diff --check` | closing verification | p4 116 ✓ · p2 ✓ · p3 470/470 ✓ · p4_verify 8/8 ✓ · diff-check exit 0 |
| 15 | stage 33 paths + commit | capture Phase 4 | **`554702c`**, tree clean |

## 2. Measured values (do not re-derive)

All from files on disk; cite the file, not memory.

**Config authority** (`configs/p4_sampling.json`; sha `72d41377967d91114650bc9d2be5c3d55b246ff2f059f5013a9f5e7d701e6f7a`, embedded in `data/processed/sampling/sampling_run_config.json`):
seed 20261026 · exclusion radius 100 m · density 1.0/km² · block 3,000 m · buffer gap 1,000 m · clustering 1,000 m · k=5 · min support 45 positives / 5 clusters · analysis CRS EPSG:32643, storage EPSG:4326.

**Eligibility** (`data/processed/sampling/eligibility_audit.csv`, `eligibility_summary.json`): 468 records → **363 POSITIVE_EVENT** (one per `event_group_id`), 1 duplicate, 5 boundary-uncertain, 78 undated, 12 not-in-district, 6 pre-2000, 1 widen-required, 1 district-centroid, 1 coordinate-error; `EXCLUDE_SUPERSEDED` = 0 (33 records carry `superseded` in `p4_flags`). Positives by year 2006:2, 2007:15, 2008:1, 2009:7, **2018:335 (92.3 %)**, 2019:1, 2024:2. Uncertainty min/median/max **10/30/30 m**. Special records: `KER/WYD/58A03/2024/01` = POSITIVE_EVENT; `14115/p141/row17 (printed Sl.17)` = EXCLUDE_COORDINATE_ERROR; `14115/p140/row15 (printed Sl.15)` = EXCLUDE_BOUNDARY_UNCERTAIN.

**Background** (`sampling_run_config.json`): district 2,356,538 cells = 2,120.88 km²; invalid-predictor cells 13,195; max positive-to-own-cell offset 20.46 m (half diagonal 21.21); conservative margin 120.5 m; band kept 3,348 / rejected 435; **eligible 2,097.45 km² (98.895 %)**; **2,097 samples**, 5.78/positive; **exact min separation 113.7 m**.

**Folds** (`fold_summary.json`, `fold_assignments.csv`, `fold_drops.csv`, `spatial_blocks.csv`): **76 clusters / 241 units / 271 blocks / 0 mixed-fold blocks**; chosen candidate seed 20261028 of 12 (seeds 20261026–20261037), score [0 support deficit, 0 cluster deficit, 69 positive spread, 1 background spread], 31 repair moves.

| Fold | Test+ | Test− | Clusters | Blocks | Train+ | Train− | Dropped (+pos) | Min retained gap |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 52 | 419 | 12 | 47 | 298 | 1,558 | 133 (13) | 1,006.2 m |
| 1 | 121 | 420 | 14 | 56 | 235 | 1,616 | 68 (7) | 1,012.0 m |
| 2 | 84 | 419 | **5** | 61 | 276 | 1,556 | 125 (3) | 1,001.3 m |
| 3 | 54 | 419 | 23 | 53 | 308 | 1,634 | 45 (1) | 1,004.6 m |
| 4 | 52 | 420 | 22 | 54 | 309 | 1,632 | 47 (2) | 1,011.5 m |

Totals: **418 drops** (392 background + 26 positive rows, **395 unique points**), drop distances 150.0–998.6 m; **retained min gap 1,001.3 m > 1,000 m**. Fold 2 is the marginal fold (5 clusters). Spread 69 is the structural floor (atomic 121-positive unit cannot split).

**Sensitivity** (`data/interim/p4/sensitivity.json`): radius 50/100/200/300 m → 2,105.93 / **2,097.45** / 2,070.10 / 2,030.22 km² (99.30 / 98.895 / 97.61 / 95.72 %). Density 0.5/1/2 → 1,049 / 2,097 / 4,195 samples (2.89 / 5.78 / 11.56 per positive). Clustering 500/1000/2000 m → 186 / **76** / 26 clusters (2,000 m fails support: min 28 positives, 1 cluster/fold). Buffer 0/500/1000/2000 m → closest cross-fold pair 150.0 / 510.0 / **1,001.3** / 2,001.2 m; drops 0 / 69 / **418** / 1,399 (incl. positives 0/5/26/140). k=3 [121,121,121] min 14 clusters; k=5 min 7; **k=10 fails** (12–34 positives). Inclusion 363→401→407 points / 76→81 clusters. Temporal: train 2018 (335) vs 28 non-2018 (17 clusters, min NN 82.4 m) — **not viable, reverse not attempted**.

**Harness caveat (documented, not hidden):** the sensitivity helper assigns folds without background blocks, so its k=5 arrangement is [86, 121, 52, 52, 52] (min 7 clusters/fold) vs production [52, 121, 84, 54, 52]; both meet support; conclusions unchanged.

## 3. Bugs caught and fixes

| # | Where | What happened | Fix |
|---|---|---|---|
| 1 | `diag_units.py` | `build()` used `tf` before it was passed (`NameError`) | pass `tf, B` through the signature |
| 2 | fold script | `block_fold = fold` returned per-**unit** folds; `block_fold_map` dict was short (`AssertionError`) | return `fold[unit]` (per-block expansion) |
| 3 | fold script | blocks DataFrame built from per-unit arrays → length mismatch vs `all_blocks` | return `unit_per_block` from `assign_positive_folds`, expand per block |
| 4 | fold script | per-**unit** point totals replicated into every block row (2589/4021 vs 363/2097) | per-block point composition (`value_counts` of `p_blocks`/`b_blocks`) |
| 5 | `p4_verify.py` | two malformed dict literals written in the gate-7 recompute block | rewrote the dict cleanly |
| 6 | `p4_verify.py` gate 7 | drop distances paired by **row order** against `fold_drops.csv`, whose order is the generator's internal point index → all 133 pairs mismatched (values right, order wrong) | pair by **point_id** (`dict(zip(ids, distances)))`; caught as a verification-method bug, not a data bug |
| 7 | `p4_sensitivity.py` §1 | measured the approximate raster domain (2,097.84 km²) instead of the exact-separation domain the sampler implements (2,097.45 km²) | §1 now replicates the sampler's conservative-mask + exact-band rule per radius; 100 m row reproduces the executed domain |
| 8 | `p4_check_consistency.py` | (a) `event_year` is a string column under `keep_default_na=False` → 2018 count read 0; (b) needle spanned a markdown line-wrap → MISS; (c) banned-vocab missed `**not**` (emphasis breaks substring) and flagged "predictor"/wrap continuations; (d) cp1252 console `UnicodeEncodeError` | (a) `pd.to_numeric`; (b) whitespace-normalised haystack (`norm()`); (c) strip emphasis + sentence-based negation check + exclude "predictor"; (d) `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` |

## 4. Verification and gates

| Suite | Result |
|---|---|
| `scripts/p4_verify.py` | **8/8 gates PASS**: 1 Phase 3 baseline intact (p3_verify_all 6/6) · 2 eligibility partition complete · 3 three special records distinct · 4 point integrity + 24 predictor layers valid at all 2,460 points · 5 exact separation 113.7 m ≥ 100 m · 6 leakage (0 mixed blocks; groups/clusters atomic) from saved assignments · 7 support + independently recomputed buffer 1,001.3 m · 8 three scripts re-run, **9 outputs byte-identical** |
| `scripts/p4_check_consistency.py` | **116/116 PASS** (config authority, audit partition, background, fold invariants recomputed by point_id, docs-vs-data needles formatted from the JSONs, disclaimers, sentence-level banned vocabulary, manifest) |
| `scripts/p3_check_consistency.py` | **470/470 PASS** (manifest section relaxed to presence+uniqueness, inline justification) |
| `scripts/p2_check_consistency.py` | all PASS (43 unique ids) |
| `git diff --check` | exit 0 (LF/CRLF warnings only) |

## 5. Outputs produced or changed

* **New data products** (committed): `data/processed/sampling/{eligibility_audit.csv, eligibility_summary.json, background_samples.csv, sampling_run_config.json, spatial_blocks.csv, fold_assignments.csv, fold_drops.csv, modelling_points.csv, fold_summary.json}` (9 files).
* **New scripts**: `scripts/p4_eligibility.py`, `p4_sample_background.py`, `p4_spatial_folds.py`, `p4_sensitivity.py`, `p4_verify.py`, `p4_check_consistency.py`.
* **New config**: `configs/p4_sampling.json` (single design authority).
* **New docs**: `docs/MODELLING_TARGET_DECISIONS.md`, `SAMPLING_STRATEGY_REPORT.md`, `SPATIAL_VALIDATION_REPORT.md`, `PHASE4_PROGRESS.md`.
* **Modified**: `.gitignore` (sampling negation), `scripts/build_manifest.py` (+P4-01…06), `docs/data_manifest.csv` (43 rows), `scripts/p3_check_consistency.py` (manifest presence+uniqueness), `data/interim/p3/compare_rebuild.py` (scoped to baseline dirs), `data/interim/p3/verify_all.json` (timing churn only).
* **Diagnostics** (committed): `data/interim/p4/{explore.py,explore.json,diag_folds.py,diag_units.py,diag_seeds.py,sensitivity.json,verify_p4.json}`.

## 6. Current project state

* **Phase 4 complete**, commit `554702c`, tree clean, nothing pushed. Phase 3 baseline `570af94` products untouched and re-verified inside the run.
* Folds are **leakage-controlled and independently verified**; they are candidate labels only — **no model, training table, synthetic event, susceptibility map or performance metric exists.**
* Every fold-support number, gap and drop is auditable from the committed CSVs/JSONs; docs are pinned to the data by 116 consistency assertions.

## 7. Next-step handoff (prompt material)

**Decision the user must make:** authorise Phase 5 (modelling) or not. Phase 5 must not start without an explicit go.

**If Phase 5 is authorised, it must:**
1. train only on the committed folds (train− points per fold are the buffer-dropped sets; test sets are the full fold contents);
2. report **per-fold** results, never pooled-only, with **fold 2 flagged marginal (5 clusters)**;
3. label any output surface *susceptibility conditional on the observed inventory (92 % 2018)* — a ranking, never a probability, never a forecast/warning/timing statement;
4. attach limitations L1–L4 from `docs/MODELLING_TARGET_DECISIONS.md` to every result;
5. use EPSG:32643 for all geometry math; never interpolate categorical rasters; mask CHIRPS nodata (−9999 undeclared); un-scale SoilGrids integers (×10/×100).

**Quick commands:**
```powershell
python scripts/p4_verify.py          # 8 gates, incl. byte-identical regeneration
python scripts/p4_check_consistency.py
python scripts/p3_check_consistency.py ; python scripts/p2_check_consistency.py
git log --oneline -3                 # 554702c ← 570af94 ← c5e2c42
```
After **any** edit to `configs/p4_sampling.json`: re-run `p4_sample_background.py` + `p4_spatial_folds.py` before `p4_verify.py` (gate 8 byte-compares; run-config embeds the config sha).

**Do not re-derive (quote as-is):** eligible 2,097.45 km² / 98.895 % · 2,097 background · 5.78/positive · exact separation 113.7 m · 76 clusters / 241 units / 271 blocks / 0 mixed · folds [52, 121, 84, 54, 52], spread 69 (structural floor) · chosen seed 20261028 · gap 1,001.3 m · drops 418 (392 bg + 26 pos rows, 395 unique) · k=10 fails · temporal holdout not viable · 418/26/395 · 92.3 % 2018.
