# Run Report RUN-2026-10-28-06 — Descriptive comparison: Phase 5 RF ranking map vs GSI 2022 LSZ zones (LSZ-01)

**Date:** started 2026-10-28, finished 2026-10-29 (crossed midnight; filename per task
specification) · **Session goal:** descriptive, area-weighted comparison of two susceptibility
products — the Phase 5 RF ranking map and the KSDMA-hosted GSI 2022 LSZ zones — on the project
GADM boundary domain; NO retraining, tuning, or changes to any Phase 4/5 output; the GSI zones
are NOT ground truth, NOT geology, NOT validation labels.
**Starting state:** commit `91f26d7` (RUN-2026-10-28-05 complete), tree clean.
**End state:** commit of this run (pinned in §6); comparison-only outputs under
`outputs/lsz_rf_comparison/`; sources untouched; `LSZ-01` stays
**`DOWNLOADED_NOT_FULLY_VALIDATED`** (not upgraded); tree clean; nothing pushed.

**Standing disclaimers (attached to every table, figure and metadata file produced here):**
1. The RF raster is a **relative ranking conditional on the observed inventory** (92.3 % of
   labels from 2018) — not a calibrated probability, not a forecast, warning or timing
   prediction.
2. The GSI 2022 zones (LSZ-01) are **another model-derived susceptibility product** — not
   ground truth, not geology, not validation labels.
3. This is **descriptive zone/ranking agreement only**; no significance tests; no independence
   claims — spatial autocorrelation is expected in both products (and both use some overlapping
   factor families: terrain, land cover, rainfall).
4. The GSI file covers **95.99 % of the GADM 4.1 project boundary** and has **not been
   field-validated**; the zones are **not extrapolated** to the missing GADM area.

## 1. What was run, in order

| # | Command / file | Purpose | Result (key numbers) |
|---|---|---|---|
| 1 | re-read `AGENTS.md`, `reports/README.md`; `git status` | conventions + clean start | tree clean at `91f26d7` |
| 2 | `python scripts/validate_ksdma_lsz_wayanad.py` | re-validate the LSZ archive per task requirement | sha256 match True; CRC OK; coverage GADM 95.99 %; union 2,118.6972 km² — identical to RUN-05 |
| 3 | hash gate (inline) | confirm archive + RF raster unchanged | zip `e5da8e03…37e2f` matches fetch_evidence + manifest; RF raster `88687c89…2a053` matches `map_metadata.json` record |
| 4 | `python scripts/lsz_rf_map_comparison.py` | the comparison (geometry repair, domain, quantiles, cross-tab, stats, figure) | see §2 → `outputs/lsz_rf_comparison/` |
| 5 | **figure inspection** | QA of the overlay figure | found fake rectangular blocks → traced to an extent-order bug (§3 #1) |
| 6 | `python scripts/probe_rf_zero_plateaus.py` | investigate whether the rectangles were real data (undeclared nodata suspicion, AGENTS.md rule 3) | **refuted**: RF==0 = 463,743 district cells in 7,391 irregular components (largest fill ratio 0.34 — no rectangles in the data); predictor −9999s inside probe windows lie OUTSIDE the district; p5 map assert (domain = district − 13,195) already excludes undeclared sentinels → bug was rendering-only (§3 #1) |
| 7 | re-run comparison with fixed extent + wrapped disclaimers | final outputs | identical numbers (data untouched); figure correct |
| 8 | p2/p3/p4 checkers + `git diff --check` | regression | pass / 470/470 / 116/116 / clean (§4) |
| 9 | commit + hash pin | capture | §6 |

## 2. Measured values (do not re-derive; every number traceable to a file)

### 2.1 Inputs and gates
- LSZ zip sha256 `e5da8e031c0523a8f98a1086f4c13ebaad76721cd2afd34e6a20b35556037e2f` — matches
  `fetch_evidence.json` and the manifest limitation text. Status unchanged:
  `DOWNLOADED_NOT_FULLY_VALIDATED`.
- RF raster sha256 `88687c890439b272a14263ab02751bd33da8e4e3b81e18188df43818eb92a053` — matches
  `data/processed/models/map_metadata.json` → the Phase 5 map was not touched.
- LSZ re-validation reproduced RUN-05 exactly: union 2,118.6972 km²; coverage GADM 95.99 %
  (mask 95.99 %, all_touched 96.11 %; OSM 99.07 %).

### 2.2 Geometry repair (documented method + area check)
- Method: **`shapely.validation.make_valid` applied per feature** to the 3 delivered
  MultiPolygons (all 3 formally invalid as delivered); `buffer(0)` fallback never needed.
- Per-class areas raw vs repaired (`comparison_domain.json` → `geometry_repair`): High
  80.8611 → 80.8611; Low 1,636.2242 → 1,636.2242; Moderate 401.6119 → 401.6119 km².
  **Total delta = 0.0 km² — the repair changes no measured areas.** All repaired geometries
  valid. Overlay used the repaired geometries only; raw zip untouched.

### 2.3 Comparison domain (primary domain = project GADM 4.1 boundary)
- Rule: **district mask (GADM) ∩ GSI zone coverage ∩ RF valid**, on the 30 m EPSG:32643 grid.
- **2,248,841 cells = 2,023.96 km²** = **95.43 %** of the district mask (2,356,538 cells) and
  **95.97 %** of the RF map domain (2,343,343 cells).
- Excluded, with no extrapolation: GADM area without GSI zones **94,542 cells = 85.09 km²**;
  GSI-covered cells where RF is invalid **13,155 cells**.
- Per-zone capture (`zone_capture_in_domain`): Low 95.10 %, Moderate 97.30 %, High 95.50 % of
  each zone's area falls inside the domain. Vector-vs-rasterized area deltas are tiny
  (Low +0.03 %, Moderate −0.07 %, High −0.31 %) — the 30 m rasterization is faithful.

### 2.4 RF quantile classes (method recorded)
- 5 quintile bands defined **over the comparison-domain cells** (equal-area 30 m cells → cell
  quantiles are area-weighted quantiles). Assignment `np.searchsorted(cuts, score, 'left')+1`.
- Cuts: p20 = **0.0**, p40 = **0.007447**, p60 = **0.082566**, p80 = **0.277386**.
- Measured class shares: Q1 20.293 %, Q2 19.707 %, Q3–Q5 exactly 20.000 % — the p20 cut equals
  the score floor (a large tie mass of exactly-0 vote shares), so Q1 is slightly heavier than
  20 %; reported as measured.
- Context: 463,743 district cells (417.4 km², 19.7 %) carry vote share **exactly 0.0** — a
  genuine model output (7,391 irregular components; largest 269.9 km², bbox fill ratio 0.34),
  not a data artifact (§3 #2).

### 2.5 Cross-tabulation — GSI zone × RF quintile (area in km²; % within GSI zone)
| GSI zone | Q1 | Q2 | Q3 | Q4 | Q5 | zone total |
|---|---|---|---|---|---|---|
| Low | 375.10 (24.10 %) | 355.52 (22.84 %) | 337.91 (21.71 %) | 282.98 (18.18 %) | 204.97 (13.17 %) | 1,556.49 |
| Moderate | 35.47 (9.08 %) | 43.00 (11.01 %) | 59.36 (15.20 %) | 96.74 (24.78 %) | 155.91 (39.93 %) | 390.49 |
| High | 0.16 (0.21 %) | 0.34 (0.44 %) | 7.52 (9.76 %) | 25.06 (32.56 %) | 43.91 (57.03 %) | 76.98 |
| ALL | 410.72 (20.29 %) | 398.86 (19.71 %) | 404.79 (20.00 %) | 404.79 (20.00 %) | 404.79 (20.00 %) | 2,023.96 |

Composition of the top RF band Q5: 50.64 % GSI-Low, 38.52 % GSI-Moderate, 10.85 % GSI-High.
(Percent-of-quintile column also in the CSV; full table:
`outputs/lsz_rf_comparison/crosstab_gsi_class_x_rf_quintile.csv`.)

### 2.6 RF score distribution within each GSI zone
| GSI zone | mean | median | p05 | p25 | p75 | p95 | max |
|---|---|---|---|---|---|---|---|
| Low | 0.1002 | 0.0105 | 0.0000 | 0.0006 | 0.1354 | 0.4909 | 0.9562 |
| Moderate | 0.2725 | 0.1882 | 0.0000 | 0.0186 | 0.4662 | 0.7923 | 0.9687 |
| High | 0.3818 | 0.3287 | 0.0504 | 0.1479 | 0.5984 | 0.8371 | 0.9626 |
| ALL (domain) | 0.1442 | 0.0269 | 0.0000 | 0.0012 | 0.2120 | 0.6572 | 0.9687 |

(Quintile-membership percentages per zone are in
`outputs/lsz_rf_comparison/rf_score_stats_within_gsi_zones.csv`.)

### 2.7 Descriptive reading (no inference)
- The RF ranking is **monotone across the GSI zones**: mean 0.100 (Low) < 0.272 (Moderate) <
  0.382 (High); medians 0.010 / 0.188 / 0.329.
- GSI-High is concentrated in the upper RF bands: 89.59 % of its domain area lies in Q4∪Q5;
  only 0.65 % in Q1∪Q2.
- GSI-Low spans the whole ranking (24.10 % in Q1 down to 13.17 % in Q5) — expected, since it
  covers 77 % of the district and necessarily contains both low- and high-scoring terrain.
- The overlap of factor families (terrain, land cover, rainfall enter both products' lineage)
  means agreement is expected to some degree; agreement is NOT evidence of accuracy for either
  product.

### 2.8 Limitations
1. Neither product is field-validated; zone/ranking agreement is not correctness.
2. The GSI file's own district boundary (KSDMA clip; 86 m median offset vs OSM, 694 m vs GADM)
   cuts edge strips: 85.09 km² of GADM has no GSI class (excluded, not extrapolated).
3. 13,155 GSI-covered cells lack valid RF values (predictor gaps) and are excluded.
4. RF vote-share ties (≥ 19.7 % of district cells at exactly 0.0) shift Q1 above exactly 20 %.
5. Quantile classes are defined on the comparison domain (per task); they are not the same
   classes one would get over the full RF map domain.
6. The GSI polygons were rasterized to the 30 m grid for the overlay (categorical, never
   interpolated); measured rasterization area deltas ≤ 0.31 % per zone.
7. Faint straight seams visible in the RF surface (e.g., near 76°E) are inherited predictor-
   mosaic structure — the Phase 2 DEM join was verified (no resampling, join spacing exactly
   1/3600°, zero offset, cross-DEM MAD 3.42 m; `DATA_READINESS_REPORT.md` §5, PASS) and was
   not re-examined here.
8. The RF ranking is conditional on an inventory that is 92.3 % single-year (2018).

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | `lsz_rf_map_comparison.py` figure | **imshow extent-order bug**: passed rasterio bounds order `[left, bottom, right, top]` where matplotlib expects `(left, right, bottom, top)` → the map rendered ~10× oversized with fake uniform rectangular blocks; the blocks triggered a false undeclared-nodata alarm (AGENTS.md rule 3) | fixed to `(left, right, bottom, top)`; **investigated the data before trusting the figure**: `probe_rf_zero_plateaus.py` showed RF==0 forms 7,391 irregular components (no rectangles in the data), predictor −9999s in the probe windows lie outside the district, and the p5 map assert (`domain = district − 13,195`) already excludes undeclared sentinels → rendering-only bug; re-rendered at true scale |
| 2 | `lsz_rf_map_comparison.py` | `KeyError` on the sha lookup: Windows backslash key vs forward-slash literal | `relative_to(ROOT).as_posix()` on both sides |
| 3 | shell workflow | `python … \| Select-Object -First 8` closed the pipe early → spurious `exit=-1` while the script was still writing | re-ran redirecting full output to a log file (`data/interim/lsz_comparison_probe/comparison_run_log.txt`); exit 0, identical numbers |
| 4 | figure text | disclaimer line truncated in rendering | wrapped into 3 lines at 175 chars, 6.8 pt |

## 4. Verification and gates

| Suite | Result |
|---|---|
| LSZ re-validation (task-required) | pass — sha256 match, CRC OK, coverage/union identical to RUN-05 |
| Input hash gates (zip + RF raster) | pass — both match their recorded sha256; Phase 5 artifacts untouched |
| `p2_check_consistency.py` | pass |
| `p3_check_consistency.py` | **470/470** |
| `p4_check_consistency.py` | **116/116** |
| `git diff --check` | clean |
| Figure QA | true-scale overlay verified visually after extent fix |

## 5. Outputs produced or changed

All new, comparison-only (nothing upstream modified):
- `outputs/lsz_rf_comparison/crosstab_gsi_class_x_rf_quintile.csv` — GSI zone × RF quintile:
  cells, km², % within zone, % of quintile; four disclaimers as `#` header lines.
- `outputs/lsz_rf_comparison/rf_score_stats_within_gsi_zones.csv` — per-zone RF score
  distribution (mean/std/min/p05/p25/median/p75/p95/max + per-quintile shares); disclaimers.
- `outputs/lsz_rf_comparison/comparison_domain.json` — full metadata: input sha256s + gate
  results, geometry-repair method and per-feature area check, domain rule/cells/areas,
  quantile method + cuts + measured shares, zone capture, RF map record (label, domain rule,
  nodata), disclaimers.
- `outputs/lsz_rf_comparison/overlay_map.png` — labelled overlay: RF vote-share background
  (colourbar labelled "relative ranking (not a probability)"), GSI zones as translucent
  categorical overlay with zone legend, GADM 4.1 boundary line, domain/gap annotation, and
  the four disclaimers.
- `scripts/lsz_rf_map_comparison.py` — re-runnable comparison (one concern per script).
- `scripts/probe_rf_zero_plateaus.py` + `data/interim/lsz_comparison_probe/probe_results.json`
  + `comparison_run_log.txt` — the §3 #1 investigation evidence.

**Explicitly NOT done:** no retraining, tuning or model comparison beyond description; no
change to the susceptibility raster, model artifacts, Phase 4 tables, manifest, or phase docs;
LSZ-01 status not upgraded; GSI zones not extrapolated to the GADM−LSZ gap; no significance
tests anywhere.

## 6. Current project state

Phase 5 baseline complete and verified (unchanged; RF raster sha256 re-confirmed). A
**descriptive comparison layer** now exists alongside the two susceptibility products: domain
2,024.0 km² (95.43 % of the district), monotone RF ordering across GSI zones (means
0.100/0.272/0.382), GSI-High 89.6 % in the top two RF quintiles. `LSZ-01` remains
`DOWNLOADED_NOT_FULLY_VALIDATED`. Commit of this run: **`9fa4f62`** (work + this report; a
one-line follow-up pins the hash).

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Whether to surface the comparison in phase documentation (a one-line pointer in
     `PHASE5_PROGRESS.md`) — deliberately not done this run to keep Phase 4/5 docs untouched.
  2. Whether a sensitivity variant is wanted: quintile classes defined over the **full RF map
     domain** (2,343,343 cells) instead of the comparison domain, or all_touched rasterization
     — would change band edges slightly (cuts recorded in §2.4 make both variants
     reproducible).
  3. Whether to compare against GSI class boundaries in vector space (polygon-level weighted
     means) instead of the 30 m grid — the grid route was chosen for exact cell alignment with
     the RF raster and the project mask.
- **What the next step must do / must not do:** must keep the four disclaimers attached to any
  reuse of these tables/figures; must never use the GSI zones as labels, validation truth, or
  predictors; must not upgrade `LSZ-01` status without new file-level evidence; must not read
  RF vote shares as probabilities. If the LSZ archive is ever re-downloaded, re-run
  `validate_ksdma_lsz_wayanad.py` and the hash gate first (§1 #3).
- **Quick commands:** `python scripts/validate_ksdma_lsz_wayanad.py` ·
  `python scripts/lsz_rf_map_comparison.py` · `python scripts/probe_rf_zero_plateaus.py` ·
  p2/p3/p4 checkers.
- **Do not re-derive (quote as-is):** domain 2,248,841 cells = 2,023.96 km² (95.43 % of mask,
  95.97 % of RF domain); GADM−LSZ exclusion 94,542 cells = 85.09 km²; RF-invalid-but-LSZ 13,155
  cells; make_valid area delta 0.0 km²; cuts 0.0 / 0.007447 / 0.082566 / 0.277386; cross-tab
  and score stats in §2.5–2.6; zone capture 95.10/97.30/95.50 %; RF==0 tie mass 463,743
  district cells in 7,391 components; zip sha256 `e5da8e03…37e2f`; RF raster sha256
  `88687c89…2a053`.
