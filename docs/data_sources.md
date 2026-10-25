# RESQAI — Data Sources and Acquisition Log

**Scope of this phase:** acquisition + basic validation only. No preprocessing, no training table, no models.
**Acquisition date:** 2026-10-25. **Study area:** Wayanad district, Kerala, India.
**Analysis extent used for acquisition:** 75.60–76.55°E, 11.25–12.00°N (buffer around GADM district bounds).
**Verified district extent (GADM 4.1):** 75.7722–76.4356°E, 11.4427–11.9706°N, area 2,121.0 km².

This log records what was actually searched, what responded, and what did not. It deliberately distinguishes
*reachable* from *authoritative* from *verified*.

---

## 1. Working sources (files obtained)

### 1.1 DEM

| Source | Endpoint | Result |
|---|---|---|
| Copernicus DEM GLO-30 (AWS Open Data) | `https://copernicus-dem-30m.s3.amazonaws.com/Copernicus_DSM_COG_10_N11_00_E0{75,76}_00_DEM/...tif` | 2 tiles, 64.2 MB, HTTP 200, no auth |
| SRTM 1 arc-second mirror (Skadi) | `https://s3.amazonaws.com/elevation-tiles-prod/skadi/N11/N11E07{5,6}.hgt.gz` | 2 tiles, 51.9 MB, HTTP 200, no auth |

Why two DEMs: the NASA SRTMGL1 product requires Earthdata authentication (see §3), so the Copernicus GLO-30
tiles are the primary terrain source and the Skadi SRTM mirror is a provenance-matched SRTM 1" cross-check.
The two agree at r = 0.9997 over 2,085 random points (MAD 3.41 m), which is strong evidence that neither
file is corrupt or mis-registered.

**Tile arithmetic (this is the point the previous phase got stuck on):** Wayanad spans both sides of 76°E —
28.5% of its area lies west of 76°E. A single `N11E076` granule therefore covers only **71.5%** of the district.
Both `N11E075` and `N11E076` are required. Verified by geometric intersection, not by tile-name inspection:
2-tile union covers **100.00%** of the GADM polygon.

### 1.2 Land cover

| Source | Endpoint | Result |
|---|---|---|
| ESA WorldCover v200 2021 | `https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map/ESA_WorldCover_10m_2021_v200_N09E075_Map.tif` | 75.6 MB, HTTP 200, no auth |

The 3°×3° tile `N09E075` covers N09–N12 / E075–E078. It is the *only* WorldCover tile touching Wayanad, so
exactly one file is needed — the earlier `N09E075` file in the handover notes may have been a preview because the
Terrascope download route returns a rendered image unless the GeoTIFF link is used.

### 1.3 Rainfall

| Source | Endpoint | Result |
|---|---|---|
| CHIRPS v2.0 monthly | `https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs/chirps-v2.0.YYYY.MM.tif.gz` | 312/312 months (2000-01 → 2025-12), 4.55 GB, 0 failures |

Each monthly file is global by design — CHC publishes no regional or subset endpoint, so the global grid is
unavoidable; clipping happens later on working copies. All 312 gzip streams pass an integrity read.

### 1.4 Geology

| Source | Endpoint | Result |
|---|---|---|
| GLiM / LiMW 2015 (PANGAEA DOI 10.1594/PANGAEA.788537) | Dropbox link published by Univ. Hamburg: `LiMW_GIS 2015.gdb.zip` | 1.14 GB, ESRI File Geodatabase, 1,235,259 polygons |

Native CRS is World Eckert IV (`ESRI:54012`, not resolvable as `EPSG:54012`). A copy was clipped to the
Wayanad bbox into `data/processed/geology/` (29 polygons in bbox, 16 intersecting the district).

### 1.5 Soil

| Source | Endpoint | Result |
|---|---|---|
| ISRIC SoilGrids 250 m (WCS) | `https://maps.isric.org/mapserv?map=/map/{prop}.map&SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage` | 14 GeoTIFFs, 1.6 MB total |

WCS `GetCoverage` with `SUBSET=Long(...)`/`Lat(...)` returned server-side subsets — Wayanad only, no global
download. Properties: clay, sand, silt, bdod, soc, cec, cfvo at 0–5 cm and 15–30 cm.

### 1.6 Boundary

| Source | Endpoint | Result |
|---|---|---|
| GADM 4.1 India level 2 | `https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_2.json.zip` | 1.5 MB, 676 districts, `NAME_2 = Wayanad` |
| OSM / Nominatim polygon | `https://nominatim.openstreetmap.org/search?q=Wayanad&polygon_geojson=1` | 0.09 MB |

Cross-check: GADM 2,121.0 km² vs OSM 2,128.6 km² (0.36% difference), bounds agree to ~0.01°.

### 1.7 Landslide inventory

The GSI "Bhusanket" portal was reverse-engineered to its static resources rather than clicked through:

- Report index: `https://bhusanket.gsi.gov.in/json/LandslideReport/LandslideReport.json` — 1,188 reports total, 8 mention Wayanad.
- PDF pattern (from `js/statewiseLandslideReport.js`): `https://bhusanket.gsi.gov.in/Output/LandslideReport/{State}/{ProjectType}/{AccNo}.pdf`

All 8 Kerala/Wayanad PDFs downloaded (49.9 MB cumulative) and text-extracted with pypdf:

| Acc. No. | Report | Extracted | Records in study area |
|---|---|---|---|
| 14337 | Landslide hazard zonation, Kasaragod/Kannur/Wayanad (2012–13) | `inventory_14337_wayanad.csv` | 35 Wayanad (Annexure-1 rows 65–99) |
| 14768 | Macro-scale 1:50,000, Mananthavady–Kalpetta–Sultan Bathery–Vazhikkadavu (2015–16) | `inventory_14768_table4.csv`, `_table5.csv` | 29 archival (23 inside district) + 17 field (13 inside) |
| ADDL. ITEM | 2018 post-disaster studies, Wayanad | `inventory_2018_postdisaster.csv` | 8 (all inside) |
| 14767 | 1:50,000, TS 49M/14 & 58A/3 (2014–16) | PDF only | tables are ~11.3–11.4°N (Kozhikode/Malappuram), outside Wayanad |
| 14999 | Macro-scale 49M/13 etc. (2016–17) | PDF only | 39/41 table rows are Kannur |
| 14252, 14253, 15990 | Site-specific: Narippara, Kunnamangalam Vayal, Plamoola | PDF only | single-site reports, no tabular inventory |

Plus NASA GLC export CSV (8.5 MB, 11,033 records globally; 50 tagged Kerala, 9 in the Wayanad bbox).

### 1.8 Additional conditioning layers

| Source | Endpoint | Result |
|---|---|---|
| HydroRIVERS v1.0 Asia | `https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_as_shp.zip` | 90.5 MB; 1,298 segments / 3,195 km in bbox |
| OSM roads (Overpass) | `https://overpass-api.de/api/interpreter` | 13,169 segments / 5,968 km inside district |

---

## 2. Sources searched but not usable

| Source | Status | Exact reason |
|---|---|---|
| NASA SRTMGL1 V003 granule download (LP DAAC/ASF) | **ACCESS_RESTRICTED** | CMR granule search returns metadata unauthenticated, but the data endpoint requires an Earthdata Login session. No `.netrc`, `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD` or token exists on this machine. |
| GSI Bhukosh (`bhukosh.gsi.gov.in`) | **ACCESS_RESTRICTED** | TCP connection timeout on both 80 and 443, repeatedly. Not a credential issue — the host is unreachable from this network. |
| GSI Bhusanket ArcGIS REST (`gisserver/rest/services/...`) | **ACCESS_RESTRICTED** | `India_All_Landslided/FeatureServer/0` and `Susceptibility/ImageServer` return `499 Token Required`. The token is injected by the authenticated web app, so it was not pursued or circumvented. |
| Kerala SDI (`ksdi.kerala.gov.in`) | **UNAVAILABLE** | Connection timeout. |
| OneGeology WFS portal | **UNAVAILABLE** | TLS handshake failure from this network. |
| IMD Pune 0.25° gridded rainfall | **ACCESS_RESTRICTED** | Requires account registration/login; no automated route. CHIRPS used as the open alternative. |
| ESA WorldCover via Terrascope | Superseded | Working AWS S3 GeoTIFF route found; avoids the preview-vs-data ambiguity from the earlier attempt. |
| Bhuvan WMS geology | Not pursued | Would return rendered map images, not attributable vector data. |

---

## 3. What was deliberately *not* done

- No attempt to bypass Earthdata, ArcGIS tokens, or portal logins.
- No global SRTM granule download (the earlier "Download All" trap).
- No deduplication or merging of the four inventory extracts (overlaps are documented, not resolved).
- No reprojection, resampling, mosaicking, or clipping of the DEM/land-cover/rainfall rasters.
- No training table, no background/negative sampling, no model, no metrics.

---

## 4. Folder layout

```
data/raw/          original downloads, unchanged
  dem/copernicus_glo30/         2 GeoTIFF tiles
  dem/srtm_1arcsec_skadi/       2 .hgt + .gz
  landcover/                    1 WorldCover GeoTIFF
  rainfall/chirps_v2_monthly/   312 .tif.gz
  soil/soilgrids250m/           14 GeoTIFFs
  geology/glim/                 .gdb.zip + extracted .gdb
  boundary/                     GADM zip + geojson, OSM geojson
  landslide_inventory/gsi_bhusanket/{pdf/, *.json}
  landslide_inventory/nasa_glc/
  additional/{hydrorivers/, osm_roads_wayanad.geojson}
data/interim/      text extracts, per-source inventory CSVs (not merged)
data/processed/    clipped copies only (geology, rivers, roads)
docs/              manifest, this log, quality report, acquisition report
scripts/           every acquisition and validation script, re-runnable
```

Every raw file's SHA-256 is in `data/file_inventory.csv` (404 files, 7.7 GB).
