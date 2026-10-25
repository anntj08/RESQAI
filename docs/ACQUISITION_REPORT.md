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
| Inventory | events c. 2006–2018 (mostly undated) |
| Roads / rivers | 2026 snapshot / static |

**Known temporal gap:** no acquired inventory contains the July 2024 Wayanad landslides.

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
| **2019–2025 landslide events** | IDENTIFIED_NOT_DOWNLOADED | GSI reports stop at 2019 on Bhusanket; post-2019 state/NDMA inventories not found in an open, machine-readable form. |

No access control was bypassed. Where a source was gated, the blocker is recorded and an open alternative
was validated instead.

---

## 6. Remaining data-quality concerns (ranked by impact on the eventual model)

1. **Inventory coordinate precision.** 35 of 89 records have 2-decimal coordinates → ~1.1 km uncertainty,
   i.e. ~26 DEM cells. Terrain predictors sampled at these points may describe the wrong slope facet.
2. **Inventory duplication.** 22/29 of the 14768 archival records lie within 1 km of a 14337 record. The
   89 extracted records therefore represent materially fewer distinct events (plausibly 55–65). Not merged.
3. **Geology scale.** GLiM at 1:3.75 M gives five classes for the district and is the weakest layer. GSI
   1:50,000 geology remains the single most important missing input.
4. **Missing 2024 event.** The largest recent Wayanad landslide is absent from every acquired inventory.
5. **Undated events.** Antecedent-rainfall predictors cannot be attached to most records.
6. **Land-cover conflation.** Plantations map as Tree cover; 89.6% of the district is one class.
7. **Rainfall resolution.** Monthly, 5.5 km — usable for climatology/antecedent indices, not for triggers.
8. **Small effective sample.** ~60 positive events in 2,121 km²; spatially clustered in a few villages.
   Random splits would leak; spatially blocked validation is mandatory later.

Full detail: `docs/data_quality_report.md`.

---

## 7. Repository state after this phase

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
