# RESQAI — Phase 3 Data Readiness Report

**Phase:** 3 · **Date:** 2026-10-26 · **Base commit:** `c5e2c42`
**Study area:** Wayanad district, Kerala (2,121 km²)
**Companion document:** `docs/PREPROCESSING_REPORT.md` (what was transformed and at what cost)

> **This report answers one question:** can each predictor and each inventory component be used
> for landslide *susceptibility* analysis, and under what conditions?
>
> **It does not answer** whether a model will work. No model has been fitted, no training table
> exists, and no accuracy figure has been produced. A `PASS` below means "this layer is
> internally consistent and defensible at its stated resolution", **not** "this layer predicts
> landslides".

---

## 1. Verdict summary

Verdict vocabulary, applied strictly:

| Verdict | Meaning |
|---|---|
| **PASS** | Every integrity check on the actual file passed. Usable at its stated resolution with no condition attached. |
| **PASS_WITH_LIMITATIONS** | Integrity checks passed, but a measured property bounds how the layer may be used. The condition is stated and is part of the verdict. |
| **BLOCKED** | Cannot be used for the stated purpose until something outside this phase is resolved. |
| **NOT_ASSESSED** | Not evaluated for this purpose in this phase. Not a failure; an explicit deferral. |

| # | Readiness item | Verdict |
|---|---|---|
| 1 | Working CRS and grid definition | **PASS** |
| 2 | Grid alignment of all processed layers | **PASS** |
| 3 | District mask fidelity | **PASS** |
| 4 | Boundary definition | **PASS_WITH_LIMITATIONS** |
| 5 | DEM integrity, mosaicking and registration | **PASS** |
| 6 | DEM horizontal georeferencing | **PASS** |
| 7 | DEM vertical reliability | **PASS_WITH_LIMITATIONS** |
| 8 | Terrain derivatives (slope, aspect, curvature) | **PASS_WITH_LIMITATIONS** |
| 9 | Land-cover class fidelity | **PASS** |
| 10 | Land cover as a predictor | **PASS_WITH_LIMITATIONS** |
| 11 | Soil unit conversion | **PASS** |
| 12 | Soil nodata decision | **PASS_WITH_LIMITATIONS** |
| 13 | Soil as a predictor | **PASS_WITH_LIMITATIONS** |
| 14 | Geology | **PASS_WITH_LIMITATIONS** |
| 15 | Rainfall record completeness | **PASS** |
| 16 | Rainfall as a predictor | **PASS_WITH_LIMITATIONS** |
| 17 | Roads and rivers vector integrity | **PASS** |
| 18 | Roads and rivers as predictors | **NOT_ASSESSED** |
| 19 | Inventory record integrity and determinism | **PASS** |
| 20 | Inventory positional precision | **PASS_WITH_LIMITATIONS** |
| 21 | Duplicate and event-group structure | **PASS** |
| 22 | Predictor coverage at usable labels | **PASS** |
| 23 | Temporal representativeness | **PASS_WITH_LIMITATIONS** |
| 24 | Spatial independence | **PASS_WITH_LIMITATIONS** |
| 25 | Observed-vs-background (absence) design | **BLOCKED** |
| 26 | Provenance and reproducibility | **PASS** |
| 27 | Manifest completeness | **PASS** |

**Overall:** preprocessing is **complete** and every predictor is usable at a stated resolution,
with the limitations listed below. **Modelling is not yet permitted**, because item 25 — how
"not a landslide" is represented — is unresolved and materially changes what any result means.

---

## 2. Item-by-item findings

### 1. Working CRS and grid definition — PASS

EPSG:32643, 30 m, 2,480 × 2,013, origin (583110, 1264170), transform
`(30, 0, 583110, 0, −30, 1324560)`. Wayanad (75.77–76.44 E) lies wholly inside UTM zone 43N, so
no zone exception is needed and scale distortion is below 0.1 %. The origin is derived by
flooring the buffered district bounds to a multiple of 30 m, so the grid is regenerable from the
polygon alone.

*Evidence:* `data/processed/grid/grid_spec.json`.

### 2. Grid alignment of all processed layers — PASS

All **25** layers (1 mask + 24 predictor layers) share the identical transform, CRS and shape:
`"all_on_grid": true`, `"problems": []`, `"n_layers": 25`. This is checked by comparing the
stored transform tuple to the grid spec — not by assuming that a successful reprojection
implies alignment.

*Evidence:* `data/processed/qa/grid_alignment_report.json`, `layer_inventory.csv` (`same_grid` = True for all 25).

### 3. District mask fidelity — PASS

Pixel-centre rasterisation gives 2,356,538 pixels = **2,120.9 km²**, versus the GADM polygon's
2,121.0 km² (−0.005 %). The same mask at 10 m gives 2,121.0 km², so the 30 m rasterisation is not
distorting the outline.

*Evidence:* `grid_spec.json` (`district_mask_area_km2`, `district_mask_area_10m_km2`, `mask_vs_polygon_pct`).

### 4. Boundary definition — PASS_WITH_LIMITATIONS

**Limitation:** GADM 4.1 and OSM agree on area to 0.36 % but their **outlines differ by a median
of 744–771 m**, p90 1.08–1.15 km, max 1,579 m; the symmetric difference is **8.75 %** of the
district (89.05 + 96.6 km² of unique area).

**Condition:** a ±0.75 km band around the district edge is boundary-ambiguous. GADM is retained
because it is stable and citable; OSM is the cross-check. **10 inventory records** lie in this
band (212–2,836 m outside GADM) and are labelled `review_boundary_uncertain`. They were **not**
reclassified and **not** relabelled `point_label_ok`, even though 4 of them fall inside OSM.
Reclassifying them would silently change published record counts; the cross-check supports their
inclusion but does not prove it.

*Evidence:* `grid/boundary_diagnostics.json`.

### 5. DEM integrity, mosaicking and registration — PASS

Two Copernicus tiles mosaic with **no resampling** (measured join spacing exactly 1/3600°), zero
voids, zero nodata. Both tiles and both `.hgt` tiles carry `AREA_OR_POINT=Point`; the `.hgt`
mosaic needed exactly 1 duplicated column and 1 edge row dropped, nothing else. Cross-DEM at
2,280,319 shared district nodes: mean diff −1.27 m, **MAD 3.42 m**, p95 8.74 m, **r = 0.9997**.

Identical tags do not by themselves prove identical ground samples, so the alignment was
measured: shifting SRTM by −1.0 to +1.0 pixel and re-comparing gives a MAD minimum exactly at
zero offset (3.42 m, against 3.82–4.26 m at ±0.5 px and 5.02–5.87 m at ±1 px). No half-pixel
correction is applied because none is needed.

*Evidence:* `dem/dem_validation.json` (`copernicus_tiles`, `srtm_tiles`, `same_node_grid`, `cross_dem`).

### 6. DEM horizontal georeferencing — PASS

Four towns of known altitude sample correctly: Kalpetta 750.1 m, Mananthavady 769.5 m,
Sulthan Bathery 892.4 m, Vythiri 768.3 m — all within ~50 m of the expected value. A transposed,
mirrored or half-pixel-shifted mosaic fails this. The native→UTM→native round trip has MAD
0.88 m and max 15.98 m.

*Evidence:* `dem_validation.json` (`georeferencing_ground_checks`, `roundtrip_native_utm_native`).

### 7. DEM vertical reliability — PASS_WITH_LIMITATIONS

**Limitations, both real:**

1. Copernicus GLO-30 is a **Digital Surface Model**, not bare earth. Wayanad is 90 % tree cover,
   so elevation and slope are *surface* values under canopy.
2. A consistent **−30 m offset** appears at all four ground checks. That is the EGM2008 geoid
   relative to published orthometric town altitudes — a datum difference, not a horizontal error.
   It is irrelevant for slope and curvature; it matters if absolute elevation is used as a
   feature.

**Condition:** use elevation as a relative terrain attribute, not as an absolute altitude, and
treat slope as a canopy-surface slope.

*Evidence:* `dem_validation.json` (`product: DSM`, `georeferencing_ground_checks` deltas).

### 8. Terrain derivatives — PASS_WITH_LIMITATIONS

Slope mean 11.53°, max 67.77° (no impossible values), p99 39.15°. Aspect undefined on 11,380
flat pixels (0.48 %), stored as nodata rather than faked north. Curvature ranges are physically
plausible (|κ| < 0.07 m⁻¹ everywhere).

**Limitation:** the **±2.24° MAD** between the same algorithm on two independent DEMs is the
honest uncertainty on slope. p95 disagreement is 5.96°, r = 0.943. This is disagreement between
products, not error against truth — both could share a bias.

**Condition:** do not report slope to better than ~1°. Slope near 0–2° (6.66 % of pixels) is
within noise. Any threshold rule ("slope > 25° = high") straddles that uncertainty.

The 1,000 m buffer is validated: without it, 70.09 % of the outer two-cell ring (10,873 / 15,514
px) would have no valid 3×3 neighbourhood, and among the pixels that remain computable the
difference is **exactly 0**.

*Evidence:* `dem_validation.json` (`derivatives`, `cross_dem_slope`, `buffer_test`, `sanity`).

### 9. Land-cover class fidelity — PASS

Native 10 m composition is measured on geodesic pixel area (83.75 m² per cell at this latitude —
a flat 100 m² assumption would have inflated the district to 2,533.7 km², 19 % too large). The
mode-aggregated 30 m grid preserves class composition to within **0.495 pp**; mode and nearest
disagree on only 1.21 % of pixels. No unexpected class codes. Zero nodata inside the district.

*Evidence:* `landcover/landcover_validation.json`, `landcover_class_legend.csv`.

### 10. Land cover as a predictor — PASS_WITH_LIMITATIONS

**Limitations:**

1. **Built-up is under-represented at 30 m**: 0.913 % → 0.762 % (−0.151 pp, −17 % relative),
   because settlement edges are narrow relative to a 30 m cell and 8.62 % of 30 m blocks are not
   class-pure. Bare/sparse loses 47 % relative; shrubland (1 native pixel) disappears entirely.
2. **A single 2021 snapshot** is used for events spanning 2006–2024. It is a present-day proxy,
   not the land cover at event time.
3. **Tree cover is 90.1 % of the district** and WorldCover maps shade coffee, rubber and tea
   plantations largely as class 10. Forest and plantation are not separable, so land cover cannot
   distinguish natural slope from cultivated slope.
4. One dominant class means the layer carries **little discriminative contrast** across Wayanad
   by construction.

**Condition:** usable as a coarse land-cover covariate. Do not interpret class 10 as "forest",
and do not expect it to separate plantation from natural vegetation. Any built-up predictor is
biased against small settlement clusters.

*Evidence:* `landcover_validation.json` (`native_classes`, `aggregation`, `native_heterogeneity_3x3`).

### 11. Soil unit conversion — PASS

All 7 properties × 2 depths converted with the published factors (bdod ÷100; cec, cfvo, clay,
sand, silt, soc ÷10). The proof is **texture closure: clay + sand + silt = 100.0 % exactly**
(median 100.0, p05 99.94, p95 100.06, 100 % of 2,352,881 cells within 1 pp). That identity holds
only if all three divisors are correct. No plausibility violations at either depth.

*Evidence:* `soil/soil_validation.json` (`texture_closure`, `plausibility_violations`), `soil_properties.csv`.

### 12. Soil nodata decision — PASS_WITH_LIMITATIONS

**Evidence for the decision:** all 14 rasters contain exactly **8,312** zero cells and the zero
masks are **identical across all 14 independent properties** (verified: min = max = 8,312 per
file; 8,312 cells where any file is zero and 8,312 where all are). 8,262 of those lie outside the
district — the shape of the acquisition crop. A genuine clay = 0 % and bdod = 0 g/cm³ would not
coincide across 14 unrelated properties, and bdod = 0 is physically impossible.

**Limitation / cost:** raw 0 → nodata for all 14. A genuine cfvo = 0 % cannot be distinguished
from a masked cell and is **discarded rather than guessed**. 50 cells (3.1 km², 0.15 % of the
district) are lost this way, producing 3,657 nodata grid pixels (**0.155 %**).

**Condition:** the direction of the error is conservative — data removed, not invented.

*Evidence:* `soil_validation.json` (`checks`, `nodata_decision`).

### 13. Soil as a predictor — PASS_WITH_LIMITATIONS

**Limitations:** native support is **250 m** (and slightly anisotropic, ~246 m E–W × 265 m N–S),
upsampled by bilinear to 30 m. Eight 30 m cells sit inside one prediction. SoilGrids values are
model predictions, not samples, and carry their own unquantified uncertainty. Only the 0–5 cm
and 15–30 cm depths exist on disk; there is no deeper horizon, so no depth-to-bedrock or
weathering-front information is available — a first-order control on landslide depth that this
project simply does not have.

**Condition:** effective resolution is 250 m and is written into every output tag. Do not
interpret soil patterns at 30 m.

*Evidence:* `soil_validation.json` (`resolution_note`), `layer_inventory.csv` (14 soil rows).

### 14. Geology — PASS_WITH_LIMITATIONS

District intersection: 16 polygons, 5 classes, 2,121.0 km² = **100.0 %** coverage, 0 invalid
geometries. Dominant class amphibolite facies at 57.81 %.

**Limitation, measured not asserted:** 45 inventory records carry GSI field lithology. The 39
described as **charnockite–gneiss split 22 / 14 / 1** across three different GLiM classes
(plutonic-acidic, metamorphic-amphibolite, plutonic-basic). GLiM assigns one population of
charnockitic gneiss to three classes, so it **cannot resolve local lithology**. Median distance
from a site to the nearest class boundary is 1,063 m; mean polygon area 132.6 km²; source scale
1:3.75 M.

**Condition:** usable **only as coarse regional context**. Do not interpret the 30 m raster as
30 m geological detail, and do not present a lithology coefficient as a local rock property. GSI
1:50,000 geology remains the correct source and remains unavailable.

*Evidence:* `geology/geology_validation.json` (`site_lithology_check`, `scale_check`), `glim_lithology_shares.csv`.

### 15. Rainfall record completeness — PASS

**312 / 312** archives were streamed through gzip CRC verification and parsed as TIFFs in full
(~18 GB decompressed), not sampled. The monthly sequence 2000-01 → 2025-12 is complete and
ordered: 0 duplicates, 0 missing, 0 unexpected. Every file has identical shape and transform.

The undeclared −9999 sentinel was handled explicitly. It is present in all 312 files globally and
in all 312 padded windows (the window reaches the Arabian Sea), but in **0 district-overlapping
cells** — which is the only set district statistics depend on. This distinction was tested
separately; an earlier version of the check conflated the two and failed, and the assertion was
corrected rather than loosened.

**All-NaN window cells are counted, not silenced.** 140 of the padded window's 1,088 cells
(12.87 %) are −9999 in every month. Reducing over them correctly yields nodata, but numpy emits
`Mean of empty slice` / `All-NaN slice encountered` / `Degrees of freedom <= 0`. Those warnings
are now scoped to the three affected reductions and paired with an assertion that the NaN
footprint of each result is *exactly* the no-data footprint, so a genuine empty-slice bug still
fails instead of being filtered away. The counts are recorded in the validation JSON. The
arithmetic was not changed: all three study-grid rasters and all three CSVs were verified
byte-identical before and after the change.

*Evidence:* `rainfall/rainfall_validation.json` (`date_sequence`, `file_reads`,
`all_nan_window_cells` = 140, `all_nan_window_pct` = 12.87, `all_nan_note`).

### 16. Rainfall as a predictor — PASS_WITH_LIMITATIONS

District series: annual mean **2,439.1 mm** (std 351.0), range 1,571 (2016) to 3,128 (2007);
JJAS 1,601.1 mm = 65.6 %; wettest month July 554.0 mm.

**Limitations:**

1. **Monthly, not daily or hourly.** A monthly 5.5 km field cannot represent the hours-scale
   trigger that actually initiates a slope failure. It supports *antecedent-condition*
   covariates (30/60/90-day totals, monsoon anomaly) only.
2. **5.5 km support** upsampled to 30 m by nearest. The grid carries 5.5 km values; the 30 m
   appearance is storage, not information.
3. **No 2026.** The series ends 2025-12 and no value was invented, so a 2026 event could not be
   represented.
4. **No per-event rainfall was assigned.** The 2024-07 district mean of 698.8 mm is a magnitude
   plausibility check against the KSDMA record (572.8 mm in two days at Kalladi), not a
   validation of event rainfall.

**Condition:** usable for antecedent-condition covariates. Must not be described as a trigger
variable, and no rainfall value may be attached to an individual landslide from this layer.

*Evidence:* `rainfall_validation.json` (`district_series`, `local_consistency_check`, `study_grid_rasters`).

### 17. Roads and rivers vector integrity — PASS

Roads: 13,169 features, 5,968.2 km, 0 invalid / empty / null / zero-length / duplicate.
Clipping is an intersection, so **0 features were lost** and **100.0 %** of in-district length is
retained. Rivers: 1,298 segments, 3,195.5 km, 0 invalid, 0 duplicate `HYRIV_ID`, orders 1–5.

*Evidence:* `additional/additional_layers_validation.json`.

### 18. Roads and rivers as predictors — NOT_ASSESSED

**Deferred, deliberately.** No distance-to-road or distance-to-river raster was produced. Doing
so is a modelling decision requiring (a) a stated proxy rationale — road ≈ cut slope /
anthropogenic disturbance, river ≈ basal erosion / undercutting — and (b) for rivers, a
defensible stream-order threshold, since HydroRIVERS includes 673 first-order segments whose
influence on any given slope is unknown.

Two measured caveats carry forward regardless: the OSM road layer is a **2026 snapshot** with no
historical state (roads built after an event would be counted for it), and the clipped river
network is **topologically truncated** (40 / 1,298 segments, 3.08 %, have `NEXT_DOWN` outside the
district).

*Evidence:* `additional_layers_validation.json` (`distance_rasters.produced: false`, `caveats`).

### 19. Inventory record integrity and determinism — PASS

Phase 2 tables were rebuilt from source and compared by SHA-256: all **7 products bit-for-bit
identical** (`build_consolidated_inventory.py` → `assemble_inventory.py`). The Phase 2 CSVs were
**not modified** by this phase. Suitability judgements were written to a new file with new
columns; the input hash is recorded in the summary. The check is now repeatable at any time:

```
python scripts/p3_verify_phase2_untouched.py   -> 7/7 byte-identical, exit 0
```

*Evidence:* `data/interim/p3/inventory_hashes_before.json`, `inventory_suitability_summary.json` (`phase2_tables_modified: false`, `input.sha256`), `scripts/p3_verify_phase2_untouched.py`.

### 20. Inventory positional precision — PASS_WITH_LIMITATIONS

468 source records classified under an explicit model
(`positional_uncertainty_m = max(0.5 × printed_step_deg × 111320, source_accuracy_floor_m)`):

| Spatial use | Count |
|---|---|
| `point_label_ok` | **408** |
| `review_widen_label` | 36 |
| `review_boundary_uncertain` | 10 |
| `exclude_not_in_district` | 12 |
| `exclude_district_centroid` | 1 |
| `exclude_until_corrected` | 1 |

Of the 372 in-window records, **370 are class A (≤ 100 m)** and 2 are class C (300–800 m).

**Limitations:**

1. The per-source accuracy floors are **assumptions**, not measured errors, and are labelled as
   such on every row.
2. Printed precision is an upper bound on accuracy, not a statement of it. A 4-decimal coordinate
   is not a 10 m coordinate — this is why floors were imposed at all (KER2018 30 m, GSI14768 50 m).
3. The `GSI_PDLS/p95` stored precision was **wrong** (2.778 × 10⁻⁶ ° where the printed whole-second DMS
   supports 0.000278° — a factor of 100). Corrected in the new file only; the Phase 2 CSV is untouched for
   reproducibility.
4. 36 records (35 undated GSI14337 + 1 in-window GLC) require a widened label or exclusion.

**Condition:** the 408 usable labels support sub-100 m analysis. The remaining 60 records support
inventory statements, not point analysis.

*Evidence:* `inventory/inventory_spatial_suitability.csv`, `inventory_suitability_summary.json`.

### 21. Duplicate and event-group structure — PASS

372 in-window records form **371 event groups**; 363 groups have at least one usable point label,
8 do not. The near-duplicate structure is fully accounted for:

- `EV-2024-MUNDAKKAI` has **2 records from 2 independent sources** (GSI PDLS + Sreekumar 2025) —
  corroboration, correctly kept as one event.
- GSI 14337's 35 rows occupy **28 unique coordinates** (12 rows share a coordinate).
- The 33 accepted 14337→14115 crosswalk pairs (< 1.5 km) map onto only **26 distinct 14115
  sites**; 2 pairs were rejected at 7,428.8 m and 16,579.0 m. They are **not** 33 new locations
  and must never be counted as such.

**Condition:** count **363 groups**, never 468 records and never 89 "events".

*Evidence:* `inventory_suitability_summary.json` (`two_decimal_records`, `crosswalk_resolution`, `event_groups`).

### 22. Predictor coverage at usable labels — PASS

All **408** usable point labels land on a **valid pixel in all 24 predictor layers** —
**408/408 = 100.00 %** in every one. This is a coverage test only: values were read to test
validity and then discarded. No feature table was written.

*Evidence:* `qa/readiness_metrics.json` (`coverage_by_layer`), `layer_inventory.csv`.

### 23. Temporal representativeness — PASS_WITH_LIMITATIONS

Usable in-window labels by year:

| 2006 | 2007 | 2008 | 2009 | 2018 | 2019 | 2024 |
|---|---|---|---|---|---|---|
| 2 | 15 | 1 | 7 | **335** | 1 | 3 |

**2018 supplies 92.0 %** of usable labels. Date precision is coarse: 328 resolved only to
**year**, 8 to month, 26 to day, 2 flagged multi-event. Only 26 labels carry a day-level date.

**Limitation and consequence:** an inventory dominated by one monsoon year cannot support a claim
of general susceptibility across 2000–2026. A model fitted here will largely learn **2018's
monsoon**, and any apparent skill is conditional on that event. The single 2024 record is the
only label from the most recent and most destructive event in the district.

**Condition:** the result may be described as "susceptibility conditioned on the observed
inventory (92 % 2018)". It may not be described as a general 2000–2026 susceptibility map.

*Evidence:* `qa/readiness_metrics.json` (`records_per_year`, `share_2018_pct`, `date_precision`).

### 24. Spatial independence — PASS_WITH_LIMITATIONS

Event points are heavily clustered. Nearest-neighbour distance: median **335 m**, p10 77.9 m,
p25 142.6 m, minimum **1.0 m**; **141** have a neighbour within 250 m and **318 of 363** have one
within 1 km. Single-linkage clustering of the 363 groups gives:

| Threshold | Independent clusters |
|---|---|
| 250 m | 278 |
| 500 m | 186 |
| **1,000 m** | **76** |
| 2,000 m | 26 |
| 5,000 m | 2 |

**Limitation:** a random train/test split on these points would put spatially adjacent records on
both sides of the split and inflate apparent performance through spatial autocorrelation. The
data are **not** independent under random splitting.

**Condition:** validation must be spatially blocked. This is a constraint on the design, and it
is satisfiable — see §3.

*Evidence:* `qa/readiness_metrics.json` (`nearest_neighbour_distance_m`, `single_linkage_clusters`).

### 25. Observed-vs-background (absence) design — BLOCKED

**This is the one genuine blocker.**

The inventory records **where landslides were observed**. It contains no record of where slopes
did not fail. There is no absence sample, no pseudo-absence set, and no surveyed stable-slope
inventory on disk.

This matters because the choice of background determines what the model output *means*:

- **Presence-only** (one-class, or presence vs. a defined background) estimates relative
  favourability, and the result is a ranking, not a probability.
- **Presence/absence** estimates a probability conditional on the sampling design, and requires
  negatives that were sampled by a known rule.
- Treating every unrecorded cell as a true negative would assert that all 2,120 km² minus a few
  hundred points are stable slopes — which the data cannot support and which the project rules
  expressly forbid.

**Why this cannot be resolved from the evidence on disk:** the choice is a scientific-design
decision, not a data-integrity question. Any of the three options above is defensible; they
produce different quantities and different claims. Picking one silently would prejudge what the
project's headline result means.

**Also unresolved and coupled to it:** whether the 8 event groups without a usable point label,
and the 60 records outside `point_label_ok`, can contribute at all (they cannot to a point-based
design), and whether the 29 non-2018 records form a viable out-of-year test (they do not form a
viable training set — see §3).

*Evidence:* the absence of any negative-sample product in `data/processed/`; `inventory_suitability_summary.json` (`counts_by_spatial_use`).

### 26. Provenance and reproducibility — PASS

Every processed raster carries `source`, `script`, and where relevant `resampling`,
`effective_resolution` and `scale_factor` tags. Every script is idempotent and re-runnable
without touching `data/raw/`. Two independent measurements back the claim:

- **Raw inputs unchanged.** All **431** raw files (7,808.5 MB) re-hashed against the
  acquisition-time manifest `data/file_inventory.csv` (git-tracked, unmodified):
  **0 size mismatches, 0 hash mismatches**. This is content-level evidence, not timestamps.
- **Outputs reproduce.** The full 11-stage pipeline was run twice. Comparing generation A
  against generation B: **68 of 74 files byte-identical**, the other 6 content-equal
  (GeoPackage containers and one JSON timer differ, parsed content does not), **0 failures**.
  Against the pre-recovery baseline the only content change is three declared *additive*
  keys in `rainfall_validation.json` (§ below); the rainfall rasters and CSVs are
  byte-identical across that change.

Phase 3 also has an **input boundary that is not raw data**: four Phase 1 processed products
under `data/processed/geology/` and `data/processed/additional/` are consumed, not
re-derived. Those two directories **mix Phase 1 and Phase 3 outputs**, so deleting
`data/processed/` wholesale removes inputs. The runner asserts the four prerequisites and
fails with an explicit message rather than a traceback. The OSM roads clip in particular
comes from a live Overpass query and cannot be reproduced byte-for-byte by re-running it.

*Evidence:* `scripts/p3_verify_raw_immutable.py`, `scripts/p3_verify_phase2_untouched.py`,
`data/interim/p3/rebuild_comparison.json`, `data/interim/p3/rebuild_comparison_roundtrip.json`,
`data/interim/p3/verify_all.json`; raster tags; `data/interim/p3/inputs_metadata.json`.

### 27. Manifest completeness — PASS

`docs/data_manifest.csv` is generated only by `scripts/build_manifest.py`. Phase 3 derived
products are registered there with their provenance and limitations; the file is never
hand-edited. Row and column counts are asserted by `scripts/p3_check_consistency.py`.

*Evidence:* `docs/data_manifest.csv`, `scripts/build_manifest.py`, `scripts/p3_check_consistency.py`.

---

## 3. Recommended spatially blocked validation design

This section is a **recommendation**, not a result. It follows from the measurements in items 23
and 24 and exists so that the modelling phase does not accidentally default to a random split.

**Structure available:** 364 usable in-window point records → **363 event groups** → **76
single-linkage clusters at 1 km**. 92.0 % of labels are 2018.

**Recommended scheme**

1. **Group by `event_group_id` first**, then by spatial cluster. A record is never split from its
   own event group, and two records of the same landslide are never on opposite sides of a split.
2. **Block at 1,000 m, with a buffer.** Connected components at 1 km give **76 blocks**. Use
   group-aware k-fold (or leave-one-block-out) over those 76 blocks, so no block contributes to
   both training and testing. Optionally repeat with **2,000 m** blocking (**26 blocks**) as a
   sensitivity check — if apparent skill collapses between 1 km and 2 km blocking, it was
   autocorrelation, not signal.
3. **Never random-split point records.** With a median nearest-neighbour distance of 335 m and a
   minimum of 1.0 m, a random split guarantees leakage.
4. **Report the per-fold spread, not a single pooled number.** With 76 blocks, a 5-fold split
   leaves ~15 blocks per test fold, holding ~4.8 event groups on average. A single pooled AUC
   would hide that variance; a mean alone would be misleading. Report mean, min, max and the
   number of folds.
5. **Run an out-of-year check in the only direction the data allow.** Train on 2018 → test on the
   **29 non-2018 labels** (2006–2009, 2019, 2024). This is a weak check with 29 records, and it
   must be reported as weak. The reverse (train on 29, test on 335) is not viable and must not be
   attempted.
6. **Do not report a single performance figure as the project's headline.** Any estimate here is
   conditional on 2018 and on 76 spatial blocks. An interval is required.

**Why not a random 80/20 split:** it would place immediate neighbours (median 335 m apart) on
both sides, inflating apparent skill without adding information. This is the specific failure mode
the project rules name.

---

## 4. What must be decided before any model is fitted

In order of consequence. Each is a decision, not a task that can be completed by running a script.

| # | Decision | Why it matters | Evidence needed to settle it |
|---|---|---|---|
| 1 | **How is "not a landslide" represented?** (§2 item 25) | Determines whether the output is a ranking or a probability, and what claim the project can make | A stated sampling design for background/absence, with its assumptions written down |
| 2 | **What is the target — 2018 monsoon susceptibility, or general susceptibility?** | 92 % of labels are 2018; a general claim is not supported | Either accept the 2018 conditioning explicitly, or acquire more non-2018 events |
| 3 | **Which predictors enter, and at what effective resolution?** | Soil (250 m), rainfall (5.5 km) and geology (~1–4.6 km) are far coarser than terrain (30 m); mixing them silently implies uniform information density | A stated feature set with each feature's effective resolution recorded |
| 4 | **Are road/river distance rasters needed, and with what rationale and stream-order threshold?** (§2 item 18) | Currently NOT_ASSESSED, so deliberately absent | A written proxy rationale; for rivers, a defensible order cutoff |
| 5 | **Is GLiM retained as a predictor or demoted to descriptive context?** (§2 item 14) | It provably cannot resolve local lithology (22/14/1 split) | A decision, informed by whether a coarse regional term adds anything over terrain |

Items 1 and 2 materially affect scientific validity and cannot be resolved from the data on disk.
They are the natural opening decisions of the modelling phase, not defects in this phase.

---

## 5. What is definitively *not* a blocker

Recorded so that the gating decision above is not confused with the rest of the work, all of which
is finished:

- All 24 predictor layers exist, are on one grid, and cover all 408 usable labels (item 22).
- The DEM is correctly registered, correctly georeferenced, and its derivatives are validated
  against an independent DEM (items 5, 6, 8).
- All 312 rainfall files were verified individually (item 15).
- Soil scale factors are proven by texture closure (item 11).
- The inventory is deterministic, auditable, and its duplicate structure is fully resolved
  (items 19, 21).
- The municipal boundary disagreement is measured and carried as a labelled limitation rather than
  silently ignored (item 4).

Nothing in the list above needs redoing before modelling. Only §4 items 1 and 2 must be settled.
