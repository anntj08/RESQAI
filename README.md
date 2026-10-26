# RESQAI — Resilient Emergency Intelligence Platform

Final-year engineering project. Long-term: AI-driven disaster decision intelligence (synthetic scenarios,
landslide/flood risk, GIS risk maps, decision support, authority & citizen interfaces).

**Current scope:** landslide *susceptibility* mapping for Wayanad district, Kerala, India.
Susceptibility = where conditions favour failure. Not a timing forecast.

## Status (2026-10-26)

| Phase | State |
|---|---|
| Dataset acquisition | Done — 8 categories, phase 2 added the event inventory sources |
| Dataset validation | Done for raster/vector layers; inventory validated per record |
| Landslide inventory (2000–2026) | Done — 468 source records, 372 in-window, 371 event groups, 408 usable point labels |
| Preprocessing | **Done, with documented limitations** — 24 predictor layers on one 30 m grid (EPSG:32643), 100 % valid coverage at all 408 usable labels |
| Training table | Not built |
| Model / metrics | None. No accuracy figure exists. |

Preprocessing being finished is **not** permission to model. Two design decisions gate that and
neither can be settled from the data on disk: how "not a landslide" is represented (no absence or
background sample exists), and whether the target is 2018-conditioned or general susceptibility
(92 % of usable labels are 2018). See `docs/DATA_READINESS_REPORT.md` §4.

## Read first

- `AGENTS.md` — conventions and hard rules
- `docs/INVENTORY_VERIFICATION_REPORT.md` — record counts, precision, duplicates, year coverage
- `docs/PREPROCESSING_REPORT.md` — CRS/grid decisions, per-layer before/after audit, transformation log
- `docs/DATA_READINESS_REPORT.md` — 27 readiness verdicts, blocked-validation design, gating decisions
- `docs/SOURCE_DISCOVERY_REPORT.md` — source landscape and the ranked gap register
- `docs/ACQUISITION_REPORT.md` — what was obtained, what was blocked and why
- `docs/data_quality_report.md` — validation evidence and caveats per dataset (**§11** carries the
  measured Phase 3 corrections)
- `docs/data_manifest.csv` — every dataset and derived product with source, version, CRS, status
- `docs/data_sources.md` — every endpoint tried, including failures
- `docs/PHASE2_PROGRESS.md`, `docs/PHASE3_PROGRESS.md` — resumable checkpoint logs

## Data

Raw downloads live under `data/raw/` and are git-ignored. Checksums for every raw file are in
`data/file_inventory.csv`. Per-source inventory extracts are in `data/interim/inventory_extracts/`
and are deliberately **not merged**.

Consolidated inventory products are in `data/processed/inventory/`:

| File | Contents |
|---|---|
| `inventory_source_records.csv` | 468 records with inclusion decision, event group, verification status |
| `inventory_events_2000_2026.csv` | 385 dated records, event-level view |
| `inventory_spatial_suitability.csv` | 468 records with measured precision, uncertainty class and per-record spatial use |
| `duplicate_crosswalk.csv` | 45 candidate pairs with measured separations and decisions |
| `coverage_2000_2026.csv` | per-year record and event counts |

Analysis layers are in `data/processed/`, all on the same 30 m EPSG:32643 grid (2480 × 2013,
origin 583110 / 1264170):

| Path | Contents |
|---|---|
| `grid/` | grid spec, GADM and OSM boundaries in metric CRS, district mask, boundary diagnostics |
| `dem/` | GLO-30 native mosaic, buffered and district DEM, slope, aspect, profile/plan curvature |
| `landcover/` | ESA WorldCover 2021, mode-aggregated 10 m → 30 m |
| `rainfall/` | district monthly/annual/JJAS series and three 30 m rasters (effective resolution 5.5 km) |
| `soil/` | 14 SoilGrids 250 m properties, native and on-grid (effective resolution 250 m) |
| `geology/` | GLiM district intersection, class raster, lithology cross-check |
| `additional/` | OSM roads and HydroRIVERS in EPSG:32643 (no distance rasters yet) |
| `qa/` | layer inventory, grid alignment report, readiness metrics |

Acquisition, assembly and preprocessing are reproducible via the scripts in `scripts/` (each is
idempotent; `scripts/p3_*.py` run in numeric stage order). Regenerate the manifest with
`python scripts/build_manifest.py`, never by hand-editing the CSV.

**One input boundary:** Phase 3 consumes four Phase 1 processed products under
`data/processed/geology/` and `data/processed/additional/`. Those directories mix Phase 1 and
Phase 3 outputs, so never delete `data/processed/` wholesale. The OSM roads clip is a live
Overpass snapshot and is treated as a fixed input, not a reproducible derivation.

## Verify the repository

One command runs every gate and writes `data/interim/p3/verify_all.json`:

```powershell
python scripts/p3_verify_all.py
```

| Gate | Proves |
|---|---|
| `p3_verify_raw_immutable.py` | 431 raw files unchanged, by SHA-256 (431/431 pass) |
| `p3_verify_phase2_untouched.py` | 7 Phase 2 inventory products unchanged (7/7 pass) |
| `p3_verify_processed.py` | 25 layers on one grid, nodata accounted for |
| `p3_check_consistency.py` | 470 assertions tying doc figures to the output files |
| `p2_check_consistency.py` | 68 Phase 2 inventory invariants |
| `compare_rebuild.py` | 74 outputs reproduce from the pipeline |

Full pipeline (11 stages, log at `data/interim/p3/rebuild_run.log`):

```powershell
powershell -ExecutionPolicy Bypass -File data/interim/p3/rebuild_all.ps1
```

Reproducibility is measured, not claimed: the pipeline was run twice and the outputs compared
— **68 of 74 files byte-identical, the other 6 content-equal, 0 failures**.

## Inventory at a glance

- **468 source records from 8 sources**; 385 dated, 83 undated site records.
- **372 in-window records (2000–2026) → 371 distinct event groups**; 363 groups have a usable point label.
- **408 usable point labels** = 364 in-window + 38 undated sites + 6 pre-2000. Undated and
  pre-2000 records are site evidence, never dated events.
- 2018 supplies **92 %** of usable labels (335 of 364) because a statewide mapped inventory exists
  for that monsoon. 19 of 27 years have no record — an **observation gap**, not evidence of absence.
- 0 of the 44 two-decimal-coordinate records are usable as point labels; 36 need a widened label.
- Source-record counts are always reported separately from distinct-event counts.

## Known gaps

- GSI 1:50,000 geology (Bhukosh unreachable; ArcGIS services token-gated) — GLiM 1:3.75 M used instead
- Puthumala 2019 primary record — GSI's 2019-20 Wayanad report is absent from the public index;
  the event is `SECONDARY_SOURCE_ONLY`
- 2020–2023 events — no GSI post-disaster volume exists for those years
- Event dates — 328 of 364 usable in-window labels resolve only to a year
- Official Survey of India district boundary — not obtained; GADM 4.1 used, ~750 m median outline
  disagreement with OSM
- No absence/background sample — modelling is gated on that design decision

**No training table, synthetic event, model or performance metric has been produced.** Preprocessing
is complete; modelling is explicitly gated, not merely pending.
