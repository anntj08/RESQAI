# RESQAI — Phase 3 Progress Log

**Scope:** geospatial preprocessing, inventory preparation, data-readiness audit.
**Started:** 2026-10-26. **Base commit:** `c5e2c42` (Phase 2 complete).
**Rule:** append-only checkpoint log. If interrupted, resume from the last DONE marker.
Nothing in this phase trains a model, builds a training table or reports a performance metric.

Every script listed here is idempotent and can be re-run without touching `data/raw/`.
One exception to "re-run from scratch" is important and was learned the hard way: Phase 3
**consumes four Phase 1 processed products** under `data/processed/geology/` and
`data/processed/additional/` (the GLiM clip, its lithology summary, and the two OSM/HydroRIVERS
clips). Those directories mix Phase 1 and Phase 3 outputs, so `data/processed/` must never be
deleted wholesale — that removes inputs, not just outputs. See the "Recovery, verification and
reproducibility" section at the end.
Outputs are written under `data/processed/`.

---

## Stage 1 — Inspect and protect the repository — DONE

- [x] Only one `AGENTS.md` (repo root, 4,200 bytes); read and followed.
- [x] Docs read: `README.md`, `ACQUISITION_REPORT.md`, `INVENTORY_VERIFICATION_REPORT.md`,
      `SOURCE_DISCOVERY_REPORT.md`, `data_quality_report.md`, `data_sources.md`,
      `data_manifest.csv` (28 datasets, 16 columns), `PHASE2_PROGRESS.md`.
- [x] Repo state: clean tree at `c5e2c42`; 431 raw files / 7,808.5 MB.
- [x] `scripts/p3_inspect_inputs.py` → `data/interim/p3/inputs_metadata.json`
      (per-file dimensions, dtype, CRS, transform, nodata, tags, res, block layout,
      value range and, for vectors, feature count/validity/bounds/columns).
- [x] Phase 2 inventory figures re-verified against `inventory_source_records.csv`:
      468 records, 445 `INCLUDED` / 10 `INCLUDED_BOUNDARY_REVIEW` /
      12 `EXCLUDED_OUT_OF_DISTRICT` / 1 `INCLUDED_FLAGGED`, 445 `usable_for_spatial_analysis`.
- [x] Raw data untouched. No re-download: every input needed already exists.

### Verified input inventory (measured on disk, not from the handover)

| Input | Measured | Note |
|---|---|---|
| Copernicus GLO-30 | 2 tiles, 3600×3600 float32, EPSG:4326, 1/3600°, nodata **absent** | tagged `AREA_OR_POINT=Point` |
| SRTM 1″ (.hgt) | 2 tiles, 3601×3601 int16, nodata −32768, **0 voids** | 1 duplicated edge node per join |
| WorldCover 2021 | 1 tile 36000×36000 uint8, 10 m, nodata 0, classes 10–95 | tile N09E075 covers the district |
| CHIRPS | 312 `.tif.gz` files, 2000-01 → 2025-12 | nodata −9999 undeclared |
| SoilGrids | 14 rasters, 420×314 int16, identical grid | nodata undeclared, 0 values present |
| GLiM | `.gdb` 46 files, native `ESRI:54012` | clip on disk holds **29** bbox polygons, not the 16 that intersect the district |
| Boundary | GADM (676 India rows → 1 Wayanad), OSM (1 polygon) | GADM is the working boundary |
| Rivers / roads | HydroRIVERS 1,428,959 Asia lines; OSM roads 24,063 raw | clips hold 1,298 / 13,169 features |

## Stage 2 — Spatial reference and study grid — DONE

Script: `scripts/p3_build_grid.py`, `scripts/p3_boundary_diagnostics.py`.

- [x] Working CRS **EPSG:32643** (UTM 43N, CM 75E). Wayanad 75.77–76.44 E lies inside
      zone 43 (72–78 E), so the scale distortion is small and no zone choice is ambiguous.
      All distances/areas measured in this CRS, never in degrees.
- [x] Grid: **30 m**, origin `x0=583110, y0=1264170` (floor to a multiple of 30 m),
      **2480 × 2013** pixels, extent 583110–657510 E / 1264170–1324560 N,
      transform `(30, 0, 583110, 0, −30, 1324560)`.
- [x] Extent = GADM district + **1,000 m** terrain buffer; final layers clipped to the
      district mask (`district_mask_30m.tif`, pixel-centre rule).
- [x] Mask area **2,120.9 km²** vs GADM polygon 2,121.0 km² (−0.005 %); a 10 m mask gives
      2,121.0 km², so the 30 m rasterisation does not distort the district.
- [x] GADM retained as primary boundary; OSM 2,128.6 km² kept as a cross-check.

### Finding that changes a published claim

The area difference GADM↔OSM is 0.36 %, but **area agreement hides an outline
disagreement**. Measured along the edges at 50 m spacing:

| Metric | Value |
|---|---|
| Median separation of the two outlines | **744–771 m** |
| p90 / p99 | 1,078–1,148 m / 1,319–1,390 m |
| Max | 1,462–1,579 m |
| Share of edge within 100 m | 4.6–4.8 % |
| Symmetric difference | **8.75 % of the district** (89.1 + 96.6 km²) |

Consequence: a ±0.75 km band around the district edge is boundary-ambiguous. 4 of the
23 records outside GADM (all KER2018, 212–648 m outside) fall **inside** OSM, so their
`INCLUDED_BOUNDARY_REVIEW` label is supported by the cross-check. No Phase 2 label was
changed: reclassifying them would silently move record counts. Details:
`data/processed/grid/boundary_diagnostics.json`.

## Stage 3 — DEM validation and terrain derivatives — DONE

Script: `scripts/p3_dem.py` → `data/processed/dem/dem_validation.json`.

### Registration — a measured correction to AGENTS.md

All four files carry `AREA_OR_POINT=Point`, pixel size exactly 1/3600°, the same stored *y*
origin (12.000139) and *x* origins exactly 1° apart:

| File | Shape | Stored x origin | First sample | Last sample |
|---|---|---|---|---|
| Copernicus E075 | 3600 × 3600 | 74.999861 | 74.999861 | 75.999583 |
| Copernicus E076 | 3600 × 3600 | 75.999861 | 75.999861 | 76.999583 |
| SRTM E075 `.hgt` | 3601 × 3601 | 74.999861 | 74.999861 | 75.999861 |
| SRTM E076 `.hgt` | 3601 × 3601 | 75.999861 | 75.999861 | 76.999861 |

Copernicus E075's last centre (**75.999583**) and E076's first (75.999861) are exactly one
1/3600° step apart, so mosaicking the two GeoTIFF tiles needs **no resampling**: contiguous,
no gap, no duplicated sample. The `.hgt` mirror **does** repeat the tile-edge node (E075's
index-3600 sample sits at 75.999861, the same coordinate as E076's first), so an `.hgt` mosaic
must drop **one duplicated column per join plus the outer southern edge row** (3601 → 3600).
That is asserted in code, not assumed.

Matching tags are not proof of matching ground samples — a 3600-centre tile and a 3601-node
tile are different conventions even when both say `Point`. So the alignment was **measured**:
SRTM was resampled at −1.0 … +1.0 px in both axes and its MAD against Copernicus compared over
325,760 district samples.

| Offset (px) | MAD (m) | Offset (px) | MAD (m) |
|---|---|---|---|
| **0, 0** | **3.42** | 0, ±0.5 | 3.95 / 4.26 |
| ±0.5, 0 | 3.82 / 4.07 | 0, ±1.0 | 5.42 / 5.87 |
| ±1.0, 0 | 5.02 / 5.43 | −0.5, −0.5 | 4.22 |

The minimum is exactly at zero and rises in every direction. A half-pixel misregistration
would have cost ~+0.4 m MAD and a whole-pixel shift ~+1.6 m, so the test is sensitive enough to
detect the error it looked for. **No half-pixel correction is applied, because none is needed.**

The AGENTS.md caution that GeoTIFF DEMs are area-registered and that naive mixing shifts data
by half a pixel is **not true of these files** — both are tagged `Point`, so the stated
dichotomy does not describe them. See §11.3 of `data_quality_report.md`.

### Results

- Native mosaic 7200×3600 over 75–77 E / 11–12 N; no voids, no nodata in either tile.
- Cross-DEM at shared nodes inside the district (2,280,319 nodes):
  mean diff −1.27 m, **MAD 3.42 m**, p95 8.74 m, max 147 m (447 nodes > 50 m),
  **r = 0.9997**. Reproduces the Phase 1 figures.
- Reprojection to the study grid: bilinear, no nodata created
  (2,356,538/2,356,538 district pixels valid).
- Round trip native→UTM→native: MAD 0.88 m, p99 4.03 m, max 15.98 m.
- Georeferencing ground check (four towns of known altitude): Kalpetta 750 m (−30),
  Manathavady 770 m (−31), Sulthan Bathery 892 m (−8), Vythiri 768 m (−32).
  A transposed, mirrored or half-pixel-shifted mosaic fails this.
- **Elevation range correction.** The full district raster spans **117–2,230 m**, not the
  Phase 1 figure of 165–1,849 m, which came from 2,085 random sample points and missed
  the highest southern peaks and lowest southern valley floors. 0.196 % of district
  pixels are < 300 m, all in narrow southern valleys where the GADM outline descends the
  escarpment; both DEMs independently record them, so they are treated as real, not as
  artefacts, but they are not representative terrain.
- Derivative reliability, same algorithm on each DEM: slope mean 11.53° (GLO-30) vs
  10.69° (SRTM), **MAD 2.24°**, p95 5.96°, r = 0.943. This ±2° is the honest uncertainty
  on the slope covariate.
- Buffer test: without the 1 km buffer **70.09 %** of the outer 2-cell ring
  (10,873/15,514 px) would have no valid 3×3 neighbourhood. Where computable, buffered
  and unbuffered values are identical (difference exactly 0), so the buffer adds
  coverage without changing values.
- Plausibility: max slope 67.8° (< 90, no impossible values); 0.011 % of pixels > 60°;
  6.66 % < 2°; 11,380 flat pixels (0.48 %) where aspect is undefined and stored as
  nodata rather than faked as north.

Outputs: `dem_glo30_mosaic_4326.tif`, `dem_glo30_30m_buf.tif`,
`dem_glo30_30m_district.tif`, `slope_deg_30m_district.tif`,
`aspect_deg_30m_district.tif`, `profile_curv_30m_district.tif`,
`plan_curv_30m_district.tif`.

Curvature only (no TRI/TPI): on a 30 m **DSM** the fine-scale roughness signal is
dominated by canopy and building texture rather than ground relief, so TRI would encode
land-cover noise as terrain. Profile/plan curvature at the 3×3 scale are the derivatives
that carry a defensible geomorphological meaning here.

## Stage 4 — Land cover: WorldCover 2021 v200 — DONE

Script: `scripts/p3_landcover.py` → `data/processed/landcover/`.

- [x] Native 10 m window over the district: 6,815 × 8,441, offset row 112 / col 9026.
- [x] District area measured on **geodesic pixel area**, not on a flat 100 m² assumption.
      True cell area at this latitude is **83.75 m²**; the naive assumption would report
      2,533.7 km² instead of the correct **2,121.9 km²** (19 % error).
- [x] Downsample 10 m → 30 m by **mode** (majority class). Nearest kept only as a control:
      the two grids disagree on **1.21 %** of district pixels, which is what mode buys.
- [x] 7 classes retained; nodata inside the district **0**; no unexpected class codes.
- [x] Composition preserved to **max 0.495 pp**:

| Class | Native % | Grid % | Change |
|---|---|---|---|
| Tree cover | 89.629 | 90.124 | +0.495 pp |
| Grassland | 5.899 | 5.579 | −0.321 |
| Cropland | 2.953 | 2.941 | −0.012 |
| Built-up | 0.913 | 0.762 | **−0.151 (−17 % rel.)** |
| Bare / sparse | 0.019 | 0.010 | −0.009 (−47 % rel.) |
| Water | 0.581 | 0.579 | −0.002 |
| Wetland | 0.004 | 0.004 | −0.000 |
| Shrubland | 1 px | 0 px | **class disappears** |

- [x] **8.62 %** of 30 m-equivalent native blocks are not class-pure, which is exactly why the
      small classes lose area. The loss is quantified and flagged; it is not silently absorbed.
- [x] Shrubland is retained in the legend with zero area so the loss stays visible.

Outputs: `landcover_worldcover2021_30m_district.tif`, `landcover_class_legend.csv`,
`landcover_validation.json`.

## Stage 5 — Rainfall: CHIRPS monthly 2000–2025 — DONE

Script: `scripts/p3_rainfall.py` → `data/processed/rainfall/` (runtime ~190 s).

- [x] **312 / 312** archives streamed through gzip CRC verification and parsed as TIFFs in full
      (~18 GB decompressed). Not a sample: every file, every month.
- [x] Sequence 2000-01 → 2025-12 complete and ordered: **0 duplicates, 0 missing, 0 unexpected**;
      all files share one shape and transform (asserted).
- [x] Undeclared sentinel handled explicitly. `nodata=None` but −9999 is stored; it appears in
      **all 312** padded windows (the window reaches the Arabian Sea) and in **0**
      district-overlapping cells. The first version of this assertion conflated the two and
      failed; the test was **corrected to the district cells**, not loosened.
- [x] Area weighting: 97 native cells overlap the district, equivalent to **68.985** whole cells
      after cos(lat) weighting. Each cell's contribution is weighted by its sub-cell overlap
      fraction (10 × 10 subcells) × cos(lat), because a pixel-centre mean would bias the total.
- [x] District series (mm):

| Statistic | Value |
|---|---|
| Monthly min / mean / max | 5.82 / 203.26 / 976.56 |
| Annual mean (std) | **2,439.1** (351.0) |
| Driest / wettest year | 1,571 (2016) / 3,128 (2007) |
| JJAS mean | 1,601.1 = **65.6 %** |
| Driest-month mean (JFM) | 19.4 |
| Wettest month | **July 554.0** |

- [x] Plausibility check only: 2024-07 district mean **698.8 mm** vs KSDMA Kalladi
      572.8 mm in two days. Right order of magnitude; **not** a validation of event rainfall,
      and no monthly value is attached to any landslide.
- [x] **2026 is absent** — the series ends 2025-12 and no value was invented.
- [x] Study-grid rasters written by **nearest**, with effective resolution 5.5 km in the tags.
- [x] **All-NaN window cells handled explicitly.** 140 of the padded window's 1,088 cells
      (12.87 %) are −9999 in every month (the Arabian Sea). Reductions over them correctly
      produce nodata but make numpy emit `Mean of empty slice`, `All-NaN slice encountered`
      and `Degrees of freedom <= 0`. These are now scoped to the three affected reductions and
      paired with an assertion that each result's NaN footprint is exactly the no-data
      footprint, so a real empty-slice bug still fails. Counts are recorded in the validation
      JSON. Arithmetic unchanged: all 3 rasters and 3 CSVs verified byte-identical before and
      after. This also removed a dead `if False` branch whose `np.stack(clim)` would have
      stacked the 12 *district scalars* instead of rasters.

Outputs: 3 CSVs, native 4-band summary, 3 study-grid GeoTIFFs, `rainfall_validation.json`.

## Stage 6 — Soil: SoilGrids 250 m — DONE

Script: `scripts/p3_soil.py` → `data/processed/soil/`.

- [x] Scale factors applied: bdod ÷100; cec, cfvo, clay, sand, silt, soc ÷10. Using the raw
      integers would be a 10–100× error that still looks plausible in a histogram.
- [x] **Texture closure is the proof:** clay + sand + silt = **100.0 %** (median 100.0,
      p05 99.94, p95 100.06, 100 % of 2,352,881 cells within 1 pp). That identity only holds if
      all three divisors are right.
- [x] Undeclared nodata: all 14 files contain exactly **8,312** zero cells and the zero masks are
      **identical across all 14 independent properties** (verified: min = max = 8,312 per file).
      8,262 lie outside the district = the acquisition crop's mask. bdod = 0 g/cm³ is physically
      impossible. Therefore **raw 0 → nodata for all 14**.
- [x] Cost stated: a genuine cfvo = 0 % is discarded rather than guessed. 50 cells (3.1 km²,
      0.15 %) lost inside the district → 3,657 grid nodata pixels (**0.155 %**).
- [x] No plausibility violations in any property at either depth.
- [x] Bilinear 250 m → 30 m (native cell only ~8× the grid cell, so interpolation is meaningful);
      effective resolution 250 m written into every tag.

Outputs: 14 native + 14 grid GeoTIFFs, `soil_properties.csv`, `soil_validation.json`.

## Stage 7 — Geology: GLiM / LiMW 2015 — DONE

Script: `scripts/p3_geology.py` → `data/processed/geology/`.

- [x] Native CRS confirmed as **`ESRI:54012`** (World Eckert IV). `EPSG:54012` **raises
      `CRSError`** — the code must be read from the file, never typed from memory.
- [x] **Phase 1 product corrected:** `glim_wayanad_clip.gpkg` is a **bbox** clip with 29
      polygons, only 16 of which intersect the district. Kept unmodified; a proper district
      intersection written alongside it (16 polygons, 5 classes, 2,121.0 km² = **100.0 %**).
- [x] Shares: amphibolite facies 57.81 %, plutonic acidic 26.45 %, metamorphic undifferentiated
      12.57 %, plutonic basic 3.14 %, acidic-with-overprint 0.03 %.
- [x] **Local-usefulness test, measured not asserted.** 45 inventory records carry GSI field
      lithology; 43 fall inside a GLiM polygon. The 39 GSI "charnockite–gneiss" records split
      **22 / 14 / 1** across plutonic-acidic, metamorphic-amphibolite and plutonic-basic. One
      rock population, three GLiM classes — measured proof the layer cannot resolve local
      lithology.
- [x] Scale check: median distance from a site to the nearest class boundary **1,063 m**
      (p90 4,623 m); mean polygon 132.6 km²; source scale 1:3.75 M.

Outputs: `glim_wayanad_district_32643.gpkg`, `glim_lithology_shares.csv`,
`geology_class_legend.csv`, `geology_class_30m_district.tif`,
`site_lithology_vs_glim.csv`, `geology_validation.json`.

## Stage 8 — Additional layers: roads and rivers — DONE

Script: `scripts/p3_additional.py` → `data/processed/additional/`.

- [x] Roads: 24,063 raw → **13,169** in-district; **0 features lost**, **100.0 %** of in-district
      length retained (5,968.2 km); 0 invalid / empty / null / zero-length / duplicate.
- [x] Attribute completeness is uneven and recorded: `highway` 100 %, `surface` 10.8 %,
      `ref` 3.9 %, `name` 8.3 %.
- [x] Rivers: 1,298 segments, 3,195.5 km geometry vs 3,384.4 km attribute total (segments are cut
      at the district edge); **40 segments (3.08 %)** truncated — the network is topologically
      incomplete by construction; 0 duplicate `HYRIV_ID`; orders 1–5
      (673 / 322 / 178 / 84 / 41).
- [x] Metric copies written in EPSG:32643; source clips untouched.
- [x] **Distance rasters deliberately not produced** — deriving them is a modelling decision
      needing a proxy rationale and, for rivers, a stream-order threshold.

Outputs: `roads_wayanad_district_32643.gpkg`, `hydrorivers_wayanad_district_32643.gpkg`,
`additional_layers_validation.json`.

## Stage 9 — Inventory preparation — DONE

Script: `scripts/p3_inventory_suitability.py` → `data/processed/inventory/`.

- [x] **Determinism proven first.** Rebuilt the Phase 2 inventory from source
      (`build_consolidated_inventory.py` → `assemble_inventory.py`) and compared SHA-256 of all
      **7 products: bit-for-bit identical**. Backup at `data/interim/p3/inventory_backup/`
      (a local copy like every other derived artefact — `data/processed/**` and these snapshots
      are not committed; see `.gitignore`).
- [x] Phase 2 tables **not modified**. Suitability lives in new columns in a new file.
- [x] Uncertainty model: `positional_uncertainty_m = max(0.5 × printed_step × 111320,
      source_accuracy_floor_m)`; floors are labelled ASSUMPTIONS on every row.
- [x] Roles: 372 in-window / 78 undated sites / 12 excluded / 6 pre-2000.
- [x] Uses: **408 `point_label_ok`**, 36 `review_widen_label`, 10 `review_boundary_uncertain`,
      12 `exclude_not_in_district`, 1 `exclude_district_centroid`, 1 `exclude_until_corrected`.
- [x] Event groups: **371**; **363 have a usable point label**, 8 do not; 339 are 2018,
      32 non-2018.
- [x] `review_before_spatial_use` records were **not** upgraded to `point_label_ok` — they keep
      a distinct `review_boundary_uncertain` use, because GADM/OSM disagree by ~750 m there.

### Four findings

1. **The "44 two-decimal records" are not 44 events.** They are 35 *undated* GSI 14337 site rows
   plus 9 NASA GLC rows, 7 of them outside the district. Only **2 dated in-window** records are
   2-decimal, and one (`GLC/101`) is a **district centroid**.
2. GSI 14337's 35 rows occupy only **28 unique coordinates**; **12 rows share a coordinate**.
3. The 33 accepted crosswalk pairs (≤ 1.5 km; 2 rejected at 7,428.8 m and 16,579.0 m) map onto
   only **26 distinct GSI 14115 sites** — not 33 independent locations.
4. **Precision defect found:** `GSI_PDLS/p95` prints whole-second DMS but stored
   `coord_precision_deg = 2.778 × 10⁻⁶` (displays as 0.000003); corrected to **0.000278** in the
   new table only (factor 100, uncertainty 10 m → 15.5 m). A first version of the script keyed the
   fix on the Phase 2 working label instead of the real `source_record_id`, so it reported the
   correction without applying it; an assertion now fails the run if any correction key matches no
   row. The Phase 2 CSV is untouched so published numbers stay reproducible.

Outputs: `inventory_spatial_suitability.csv` (468 rows), `event_group_point_status.csv`,
`inventory_suitability_summary.json`.

## Stages 10–11 — Cross-layer integrity and readiness metrics — DONE

Script: `scripts/p3_verify_processed.py` → `data/processed/qa/`.

- [x] **All 25 layers on the common grid** — `"all_on_grid": true`, `"problems": []`,
      `"n_layers": 25`. Checked by comparing the stored transform tuple to the grid spec,
      not by trusting a successful reprojection.
- [x] Nodata inside the district: aspect **0.483 %** (flat ground), soil **0.155 %**, all others
      **0 %**.
- [x] **Coverage at usable labels: 408 / 408 = 100.00 % in every one of the 24 predictor layers.**
      Values were read to test validity and discarded; **no feature table was written**.
- [x] Clustering: median nearest-neighbour **335 m** (p10 77.9, min 1.0); 141 within 250 m;
      **318 / 363 within 1 km**. Single-linkage clusters: 278 @ 250 m, 186 @ 500 m,
      **76 @ 1 km**, 26 @ 2 km, 2 @ 5 km.
- [x] **2018 supplies 92.0 %** of usable labels (335 of 364); date precision is 328 year-only,
      8 month, 26 day, 2 multi-event.

Outputs: `layer_inventory.csv`, `grid_alignment_report.json`, `readiness_metrics.json`.

## Stage 12 — Documentation and reproducibility — DONE

- [x] `docs/PREPROCESSING_REPORT.md` — CRS/grid decisions, per-layer before/after
      information-preservation audit, transformation log (19 operations), feature lineage,
      15 detected losses with corrective action, 7 measured corrections to earlier claims,
      what was deliberately not produced, residual limits and blockers.
- [x] `docs/DATA_READINESS_REPORT.md` — 27 readiness items each classified
      PASS / PASS_WITH_LIMITATIONS / BLOCKED / NOT_ASSESSED with evidence, the recommended
      spatially blocked validation design, and the five decisions required before modelling.
- [x] `docs/data_quality_report.md` — Phase 3 corrections section appended.
- [x] `README.md` — status table and outputs updated.
- [x] `scripts/build_manifest.py` extended with the Phase 3 derived products;
      `docs/data_manifest.csv` regenerated by running it (never hand-edited).
- [x] `scripts/p3_check_consistency.py` added: ties every Phase 3 number quoted in the docs to
      the JSON/CSV outputs, so a silent drift fails a test instead of shipping.
      **470 assertions, all passing** (453 at first write, +17 added to pin the three
      easily-conflated inventory records and the registration/grid-alignment keys).
- [x] `scripts/p2_check_consistency.py` still passes — **68 assertions**, all passing. Phase 3
      did not disturb Phase 2 outputs. The manifest section was relaxed from "exactly 28 rows"
      to "every one of the 28 Phase 2 ids is still present and no id is duplicated", because
      Phase 3 legitimately appends 9 derived rows; the inventory invariants are unchanged.
      (`PHASE2_PROGRESS.md` said "60 assertions" — that figure was already stale at `c5e2c42`,
      where the committed script actually ran 68 checks, 66 pass + 2 fail against the grown
      manifest. Corrected in that file.)
- [x] **Pipeline re-run end to end through `data/interim/p3/rebuild_all.ps1`**: 11/11 stages
      exit 0, no stderr noise. Measured reproducibility, not asserted:
      - raw inputs: **431/431** files (7,808.5 MB) match the acquisition-time SHA-256
        manifest — 0 size, 0 hash mismatches;
      - generation A vs generation B (same code, two runs): **68/74 byte-identical**, 6
        content-equal (GeoPackage containers + one JSON timer), **0 failures**;
      - against the pre-recovery baseline: 68 byte-identical, 5 content-equal, 1
        **declared additive** difference (three evidence keys added to
        `rainfall_validation.json`), 0 failures.
- [x] `scripts/p3_verify_all.py` added: one command runs all six gates and writes
      `data/interim/p3/verify_all.json`. Current result: **6/6 PASSED**.

### Overall Phase 3 verdict

Preprocessing is **complete**: 24 predictor layers exist on one grid and cover 100 % of the 408
usable labels. It is **not** a green light to model. Two decisions gate that:
how "not a landslide" is represented (currently **BLOCKED** — no absence/background sample
exists), and whether the target is 2018-conditioned or general susceptibility (92 % of labels are
2018). See `docs/DATA_READINESS_REPORT.md` §4.

---

## Recovery, verification and reproducibility (2026-10-26)

Stages 1–12 above were written as they were completed. This section records the *verification*
pass that followed, because it found four defects that the earlier pass had not caught. Each is
recorded with the evidence that exposed it, not just the fix.

### What was checked, and what it found

| # | Defect | How it was found | Severity |
|---|---|---|---|
| 1 | `rebuild_all.ps1` aborted after the rainfall stage on a benign stderr warning | first rebuild attempt died at rainfall with exit 1 although the stage had succeeded | pipeline would not complete unattended |
| 2 | The rebuild's "delete all outputs" step destroyed **four Phase 1 inputs** | `p3_geology.py` failed with `DataSourceError: glim_wayanad_clip.gpkg: No such file or directory` | inputs lost; recoverable from backup |
| 3 | `p3_rainfall.py` let three numpy all-NaN-slice warnings escape to stderr, and carried a dead `if False` branch that would have stacked 12 district scalars as if they were rasters | stderr captured during the repaired run | noisy logs, latent trap |
| 4 | Three documentation claims were wrong: `layers_off_grid` (a key that does not exist), a stale DEM mosaic coordinate (`75.999722` vs measured `75.999583`), and "60 assertions" for a suite that runs 68 | targeted grep against the JSON schemas and the actual script output | docs disagreed with data |

### 1. PowerShell runner

`$ErrorActionPreference = "Stop"` promotes a *stderr line* from a native command into a
terminating error, even when the process exits 0. The runner now uses `"Continue"` and judges
each stage by `$LASTEXITCODE` alone, checked immediately after every invocation, failing fast at
the first nonzero exit. PowerShell-native file operations carry an explicit
`-ErrorAction Stop`, and each stage's script SHA-256 and the host Python version are written to
the log for provenance. Native output is redirected through `cmd /c`, because PowerShell's own
`*>>` mangles carriage-return progress bars into unreadable log noise.

### 2. The Phase 1 input boundary

`data/processed/geology/` and `data/processed/additional/` **mix Phase 1 outputs with Phase 3
outputs**. The rebuild therefore cannot start from an empty `data/processed/`. Four Phase 1
products are required inputs:

| Input | Producer | Re-runnable offline? |
|---|---|---|
| `geology/glim_wayanad_clip.gpkg` | `scripts/clip_geology.py` | yes — reads `data/raw` only |
| `geology/glim_wayanad_lithology_summary.csv` | `scripts/clip_geology.py` | yes |
| `additional/osm_roads_wayanad_clip.gpkg` | `scripts/acquire_osm_roads.py` | **no — live Overpass query** |
| `additional/hydrorivers_wayanad_clip.gpkg` | `scripts/acquire_hydrorivers.py` | yes — skips download if present |

Because the roads clip is a live snapshot, re-running its producer would silently change the
input and make any byte comparison meaningless. The runner therefore **checks** these four and
exits 3 with a named list if any is missing, instead of failing deep inside a stage. All four
were restored from `data/interim/p3/rebuild_backup/` and verified byte-identical to the
baseline. `p3_geology.py` itself was never missing or broken — the fault was the deletion.

### 3. Rainfall warnings

140 of the padded window's 1,088 cells (12.87 %) are −9999 in every month. Reducing over them
correctly yields nodata, but numpy emits `Mean of empty slice`, `All-NaN slice encountered` and
`Degrees of freedom <= 0`. These are now scoped to the three affected reductions and paired with
an assertion that each result's NaN footprint is **exactly** the no-data footprint — so a real
empty-slice bug fails instead of being filtered away. Counts are recorded in
`rainfall_validation.json` (`all_nan_window_cells` = 140, `all_nan_window_pct` = 12.87). No
warning is suppressed globally, and warnings from other stages still print.

**Arithmetic proven unchanged:** all three study-grid rainfall rasters and all three CSVs are
byte-identical before and after the change; the only JSON difference is the three additive
evidence keys plus the volatile `elapsed_s`.

### 4. Documentation corrections

- `DATA_READINESS_REPORT.md` §2 said `"layers_off_grid": []`; the report actually has
  `"all_on_grid": true`, `"problems": []`, `"n_layers": 25`.
- `PHASE3_PROGRESS.md` Stage 3 quoted E075's last centre as `75.999722`; the measured value is
  **75.999583**, and the section now records the sub-pixel shift test that supersedes the
  original reasoning.
- `PHASE2_PROGRESS.md` and `PHASE3_PROGRESS.md` said the Phase 2 suite has "60 assertions"; it
  runs **68** (verified by running the committed script from `c5e2c42`).
- Both progress logs and `PREPROCESSING_REPORT.md` said the pipeline "re-runs from a clean
  checkout"; that is now stated precisely, including the Phase 1 input boundary.

### Verification commands

```powershell
# one command, all six gates
python scripts/p3_verify_all.py

# or individually
python scripts/p3_verify_raw_immutable.py       # 431 raw files by sha256
python scripts/p3_verify_phase2_untouched.py    # 7 Phase 2 products by sha256
python scripts/p3_verify_processed.py           # 25 layers on one grid
python scripts/p3_check_consistency.py          # 470 doc-vs-data assertions
python scripts/p2_check_consistency.py          # 68 Phase 2 assertions
python data/interim/p3/compare_rebuild.py       # 74 outputs vs baseline
python scripts/build_manifest.py                # regenerate the manifest

# full pipeline (11 stages), writing data/interim/p3/rebuild_run.log
powershell -ExecutionPolicy Bypass -File data/interim/p3/rebuild_all.ps1
```

### Final measured state

| Check | Result |
|---|---|
| Pipeline stages | **11 / 11 exit 0** |
| Raw inputs | **431 / 431** sha256 match, 7,808.5 MB |
| Phase 2 products | **7 / 7** byte-identical |
| Layers on the study grid | **25 / 25** |
| Determinism (two runs, same code) | **68 byte-identical + 6 content-equal, 0 failures** |
| vs pre-recovery baseline | **68 identical + 5 content-equal + 1 declared additive, 0 failures** |
| Phase 3 consistency assertions | **470 / 470 passed** |
| Phase 2 consistency assertions | **68 / 68 passed** |
| Manifest | generated, **37 rows × 16 columns** |
| `git diff --check` | clean (exit 0) |

**Phase 3 status: complete, with documented limitations.** No model, training table, synthetic
event or performance metric exists in this phase.

---
