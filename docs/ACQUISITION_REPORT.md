# RESQAI — Autonomous Data Acquisition: Completion Report

**Date:** 2026-10-25
**Phase:** dataset discovery, download, organisation, basic validation
**Explicitly out of scope and not performed:** preprocessing, mosaicking/resampling, training-table
construction, background/negative sampling, any model training or evaluation.

---

## 1. Starting state

The repository at `C:\Major` was **empty**: a git repository with zero commits, no `AGENTS.md`, no
`data/`, no manifests, no prior downloads. Everything described in the handover document existed as
narrative context only — the earlier ESA WorldCover file, the SRTM point search, and the GSI PDF
references had left no artefacts on disk.

Consequence: there was nothing to reuse and nothing to avoid duplicating. All eight dataset categories
were acquired from scratch in this session.

---

## 2. What was downloaded

**Totals: 404 raw files, 7.7 GB** (including both archives and their extracted contents), plus 6.7 MB of
clipped working copies and 14 interim files.

| # | Dataset | Product / version | Local path | Size | Status |
|---|---|---|---|---|---|
| 1 | DEM — primary | Copernicus DEM GLO-30, 2 tiles (N11E075, N11E076) | `data/raw/dem/copernicus_glo30/` | 64.2 MB | **VERIFIED** |
| 2 | DEM — SRTM cross-check | SRTM 1″ (Skadi mirror), N11E075 + N11E076 | `data/raw/dem/srtm_1arcsec_skadi/` | 51.9 MB | **VERIFIED** |
| 3 | DEM — requested product | NASA SRTMGL1 V003 | — | 0 | **ACCESS_RESTRICTED** |
| 4 | Land cover | ESA WorldCover v200 2021, tile N09E075 | `data/raw/landcover/` | 75.6 MB | **VERIFIED** |
| 5 | Rainfall | CHIRPS v2.0 monthly, 312 months (2000-01→2025-12) | `data/raw/rainfall/chirps_v2_monthly/` | 4,545.6 MB | **VERIFIED** |
| 6 | Soil | ISRIC SoilGrids 250 m, 7 properties × 2 depths | `data/raw/soil/soilgrids250m/` | 1.7 MB | **VERIFIED** |
| 7 | Geology | GLiM / LiMW 2015 File Geodatabase | `data/raw/geology/glim/` | 1,138.7 MB (zip) | **VERIFIED** |
| 8 | Boundary | GADM 4.1 India level 2 → Wayanad | `data/raw/boundary/` | 1.5 MB | **VERIFIED** |
| 9 | Boundary — cross-check | OSM/Nominatim Wayanad polygon | `data/raw/boundary/` | 0.09 MB | **VERIFIED** |
| 10 | Inventory | GSI 14337 (2012-13) PDF + 35 Wayanad records | `data/raw/landslide_inventory/gsi_bhusanket/pdf/` | 1.6 MB | **DOWNLOADED_NOT_FULLY_VALIDATED** |
| 11 | Inventory | GSI 14768 (2015-16) PDF + 29 archival + 17 field records | same | 9.1 MB | **DOWNLOADED_NOT_FULLY_VALIDATED** |
| 12 | Inventory | GSI 2018 post-disaster PDF + 8 records | same | 2.5 MB | **DOWNLOADED_NOT_FULLY_VALIDATED** |
| 13 | Inventory — context | GSI 14767, 14999, 14252, 14253, 15990 PDFs | same | 36.7 MB | **DOWNLOADED_NOT_FULLY_VALIDATED** |
| 14 | Inventory — global | NASA Global Landslide Catalog export | `data/raw/landslide_inventory/nasa_glc/` | 8.5 MB | **VERIFIED** |
| 15 | Drainage | HydroRIVERS v1.0 Asia | `data/raw/additional/hydrorivers/` | 90.5 MB | **VERIFIED** |
| 16 | Roads | OSM Overpass snapshot | `data/raw/additional/` | 6.1 MB | **VERIFIED** |

Working copies (clipped, originals untouched):

- `data/processed/geology/glim_wayanad_clip.gpkg` — 16 polygons, 5 lithology classes
- `data/processed/additional/hydrorivers_wayanad_clip.gpkg` — 1,298 segments
- `data/processed/additional/osm_roads_wayanad_clip.gpkg` — 13,169 segments

---

## 3. Coverage achieved

**Spatial:**

| Layer | Coverage of GADM Wayanad polygon |
|---|---|
| Copernicus DEM (2 tiles) | **100.00%** |
| SRTM 1″ (2 tiles) | **100.00%** |
| WorldCover (1 tile) | **100.00%** |
| SoilGrids (WCS subset) | covers 75.60–76.55 E / 11.25–12.00 N |
| CHIRPS | covers (global grid) |
| GEOLOGY (GLiM) | 16 polygons intersect district |
| Rivers / roads | clipped to bbox / district |

The single-tile assumption from the previous phase is now resolved quantitatively: **N11E076 alone covers
71.50% of the district**; N11E075 covers the remaining 28.50%. Both are required, and both were obtained.

**Temporal:**

| Layer | Period |
|---|---|
| DEM | 2000 (SRTM) / ~2021 (Copernicus) |
| Land cover | 2021 |
| Rainfall | 2000-01 → 2025-12, monthly |
| Inventory | events c. 1961–2024 (phase 1 alone: c. 2006–2018, mostly undated) |
| Roads / rivers | 2026 snapshot / static |

**Known temporal gap (phase 1):** no acquired inventory contained the July 2024 Wayanad landslides.
**Resolved in phase 2** — see §7.

---

## 4. Validation results (evidence, not assertion)

| Check | Result |
|---|---|
| rasters open + read | 100% of GeoTIFF/HGT/GPKG files |
| CRS declared | all: EPSG:4326 except GLiM native Eckert IV (reprojected in the clip copy) |
| Resolution as advertised | DEM 1″ ✓, WorldCover 10 m ✓, SoilGrids ~250 m ✓, CHIRPS 0.05° ✓ |
| District coverage | DEM 100.00%, WorldCover 100.00% (geometric test, not tile-name guess) |
| CHIRPS archive integrity | 312/312 gzip streams decompress cleanly |
| SRTM voids | 0 cells = −32768 in both tiles |
| DEM mutual agreement | r = 0.9997, MAD = 3.41 m, p95 = 8.50 m (n = 2,085 points) |
| Rainfall plausibility | 2,526 mm/yr climatology 2000–2025; 2024 = 2,601 mm |
| Boundary agreement | GADM 2,121.0 km² vs OSM 2,128.6 km² (0.36%) |
| Inventory counts vs source text | 35/35, 29/29, 17/17, 8/8 — all match the reports' own totals |
| Inventory points inside district | 35/35, 23/29, 13/17, 8/8 |
| File-level provenance | SHA-256 for all 404 raw files in `data/file_inventory.csv` |

---

## 5. Not obtained, and exactly why

| Item | Status | Reason |
|---|---|---|
| **NASA SRTMGL1 V003 tiles** | ACCESS_RESTRICTED | Earthdata Login required for the data endpoint. CMR metadata search works unauthenticated; the download does not. No credentials on this machine. **Substituted** with Copernicus GLO-30 (primary) + an SRTM 1″ mirror (cross-check), both validated. |
| **GSI Bhukosh geology / geomorphology** | ACCESS_RESTRICTED | `bhukosh.gsi.gov.in` refused TCP connections on ports 80 and 443 across repeated attempts — host unreachable from this network, not a credentials problem. |
| **GSI Bhusanket ArcGIS landslide inventory & susceptibility services** | ACCESS_RESTRICTED | `India_All_Landslided/FeatureServer/0` and `Susceptibility/ImageServer` return `499 Token Required`. Token is injected by the authenticated web app; not pursued. The same information was instead obtained from the public GSI PDF reports. |
| **Kerala SDI boundary / state layers** | UNAVAILABLE | `ksdi.kerala.gov.in` connection timeout. |
| **IMD 0.25° gridded rainfall** | ACCESS_RESTRICTED | Login-gated. CHIRPS used as the open alternative. |
| **Official Survey of India district boundary** | IDENTIFIED_NOT_DOWNLOADED | No open distribution found; GADM + OSM cross-check used instead. |
| **2019–2025 landslide events** | PARTLY RESOLVED in phase 2 | **Superseded:** GSI PDLS 2024 and PDLS 2025 volumes were located and acquired, supplying the July 2024 Mundakkai-Chooralmala record and a June 2024 Meenakshi Bridge record. 2020–2023 remain unrepresented because no GSI post-disaster volume exists for those years. Puthumala 2019 remains blocked (§7). |

No access control was bypassed. Where a source was gated, the blocker is recorded and an open alternative
was validated instead.

---

## 6. Remaining data-quality concerns (ranked by impact on the eventual model)

Phase-1 assessment, updated with phase-2 measurements. Items 1, 2, 4 and 5 changed materially.

1. **Inventory coordinate precision.** ~~35 of 89 records have 2-decimal coordinates → ~1.1 km
   uncertainty.~~ **Refined:** 44 of 468 records are 2-decimal (~1.1 km); a further 332 resolve only to a
   year. But 33/35 of the two-decimal GSI records were tied to arc-second records at the same sites
   (median separation 471 m), so their usable precision is sub-30 m. 44 records remain at 2 dp.
2. **Inventory duplication.** **Resolved as a measured crosswalk, not a merge.** 45 candidate pairs, each
   with a measured separation and a decision. 33/35 GSI 14337 rows are within 1.5 km of a GSI 14115 row;
   8 GSI 2018 slides are 361–1,453 m from any mapped 2018 point and stay separate. Source records (468)
   are still reported separately from distinct events (371 in-window).
3. **Geology scale.** GLiM at 1:3.75 M gives five classes for the district and is the weakest layer. GSI
   1:50,000 geology remains the single most important missing input. **Phase 2 adds** site lithology for
   45 records, usable to validate a vector layer later.
4. **Missing 2024 event.** **Resolved.** GSI PDLS 2024 supplies the July 2024 Mundakkai-Chooralmala
   42-point datasheet, and the coordinate was corroborated to within 495 m against an independent
   publication.
5. **Undated events.** **Partially resolved.** 385 records now carry a stated date (379 in the 2000–2026
   window); 83 remain undated site records, correctly excluded from event counts.
6. **Land-cover conflation.** Plantations map as Tree cover; 89.6% of the district is one class.
7. **Rainfall resolution.** Monthly, 5.5 km — usable for climatology/antecedent indices, not for triggers.
8. **Small effective sample.** 371 in-window event groups, but 339 of them are the 2018 monsoon and 332
   resolve only to a year. The *independent* time spread is far smaller than the record count implies.
   Random splits would leak; spatially blocked validation is mandatory later.

Full detail: `docs/data_quality_report.md`.

---

## 7. Repository state after phase 1

```
C:\Major
├── AGENTS.md                      project conventions for future sessions
├── README.md                      what this repo is, current phase
├── docs/
│   ├── data_manifest.csv          16 datasets, machine-readable, 16 fields
│   ├── data_sources.md            every endpoint searched, incl. failures
│   ├── data_quality_report.md     validation evidence + caveats
│   └── ACQUISITION_REPORT.md      this file
├── data/
│   ├── file_inventory.csv         404 files + SHA-256 + sizes
│   ├── raw/                       originals, unchanged
│   ├── interim/                   PDF text + per-source inventory CSVs
│   └── processed/                 3 clipped working copies
├── scripts/                       every acquisition/validation script (re-runnable)
└── data/processed, outputs/, models/, notebooks/, src/   empty placeholders
```

No model, no training table, no synthetic data, no accuracy figure exists at this point — by design.

---

## 8. Phase 2 — acquisition-gap recovery and inventory verification

**Date:** 2026-10-25. **Base commit:** `b148ad7`.
**Detail:** `docs/SOURCE_DISCOVERY_REPORT.md`, `docs/INVENTORY_VERIFICATION_REPORT.md`.

### 8.1 What phase 2 added

| Item | Size | Local path |
|---|---|---|
| 2018 Kerala monsoon inventory, 12 files (Hao, van Westen et al., CC-BY-4.0) | 15.2 MB | `data/raw/landslide_inventory/kerala_2018_dans/` |
| GSI `gsi_14115.pdf` (Landslide Inventory of Kerala, Wayanad table) | 4.9 MB | `data/raw/landslide_inventory/gsi_bhusanket/pdf/` |
| GSI `gsi_PDLS_2024_51817.pdf` | 15.1 MB | same |
| GSI `gsi_PDLS_2025_61074.pdf` | 22.5 MB | same |
| GSI `gsi_14336.pdf`, `gsi_12272.pdf`, `gsi_12236.pdf` | 12.7 MB | same |
| KSDMA Meppadi PDNA 2024 (647 pp) | 19.8 MB | `data/raw/landslide_inventory/ksdma/` |
| KSDMA Memorandum 17082024 | 4.1 MB | same |
| KSDMA October 2021 event report | 10.7 MB | same |
| KSDMA G.O. Ms 6 DMD-GSI | 0.2 MB | same |
| GFLD supplementary tables t01–t03 | 0.02 MB | `data/raw/landslide_inventory/gfld/` |
| Two PMC open-access full texts | 0.3 MB | `data/raw/literature_events/` |

### 8.2 Inventory result

**468 source records from 8 sources; 385 dated; 83 undated site records.**
**372 in-window included records → 371 distinct event groups.**

| Year | Records | Event groups |
|---:|---:|---:|
| 2006 | 2 | 2 |
| 2007 | 18 | 18 |
| 2008 | 1 | 1 |
| 2009 | 7 | 7 |
| 2017 | 1 | 1 |
| 2018 | 339 | 339 |
| 2019 | 1 | 1 |
| 2024 | 3 | 2 |
| all other 2000–2026 years | 0 | 0 |

Nineteen of twenty-seven years are empty. This is an **observation gap**, not evidence that no
landslides occurred: no GSI post-disaster volume exists for 2020–2023, and the 2025 volume's
only Wayanad record describes a June 2024 event.

### 8.3 Blockers confirmed in phase 2

| Item | Status | Evidence |
|---|---|---|
| GSI 2019-20 Wayanad/Kannur post-disaster report (Sulal et al. 2020) | **UNAVAILABLE** | Cited in GSI's own 2025 bibliography but absent from the public 1,188-report index; verified by enumerating all 62 Kerala reports. Consequence: Puthumala 2019 stays `SECONDARY_SOURCE_ONLY`. |
| GSI Bhukosh | **ACCESS_RESTRICTED** | TCP connect timeout on 443, repeated. |
| GSI Bhusanket ArcGIS REST | **ACCESS_RESTRICTED** | `499 Token Required`. |
| Kerala ILDM | **UNAVAILABLE** | TLS handshake fails for every path including `/`. |
| FABDEM | **ACCESS_RESTRICTED** | `data.bris.ac.uk` connect timeout. |
| GFLD event database | **CLOSED** | Supplements contain only the trigger taxonomy; the event DB is not redistributed. |
| KSDMA per-year pages as inventories | **CLOSED** | They lead to needs assessments and memoranda, not event lists. |

No access control was bypassed. Every blocker is recorded with the exact observed failure mode.

### 8.4 Repository state after phase 2

```
docs/
  data_manifest.csv                28 datasets, 16 fields (regenerate: scripts/build_manifest.py)
  data_sources.md                  endpoints searched, incl. failures
  data_quality_report.md           validation evidence + caveats
  ACQUISITION_REPORT.md            this file
  SOURCE_DISCOVERY_REPORT.md       source landscape + ranked gap register G1–G8
  INVENTORY_VERIFICATION_REPORT.md record counts, precision, duplicates, coverage
  PHASE2_PROGRESS.md               resumable checkpoint log
data/processed/inventory/
  inventory_source_records.csv     468 records + decisions + event groups
  inventory_events_2000_2026.csv   385 dated records
  duplicate_crosswalk.csv          45 candidate pairs with measured separations
  coverage_2000_2026.csv           27 rows, per-year
  inventory_all_source_records.csv pre-decision assembly
  2024_corroboration.json/.csv     2024 coordinate evidence
data/interim/inventory_extracts/   per-source CSVs, never merged
```

**Still no model, training table, synthetic data or performance metric. Susceptibility mapping has not
begun.**
