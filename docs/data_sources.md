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

**GSI 1:50,000 geology — re-check 2026-10-28** (run `RUN-2026-10-28-04`; evidence:
`data/interim/gsi_geology/probe_results.json`, `ngdr_probe.json`, `ngdr_guest_services.json`,
`ngdr_asset_endpoints.json`; probe scripts `scripts/probe_gsi_geology_50k.py`,
`probe_ngdr_geodata.py`, `probe_ngdr_guest_assets.py`). Status stays
**`ACCESS_RESTRICTED`** (manifest `GEO-02`):

- **Product confirmed from official documents.** GSI Data Sharing and Accessibility Policy
  2019, §7.1 (PDF on `www.geodataindia.gov.in`, sha256 `5ca1cd39…f175c3`): the 1:50K
  (or 1:63,360) mapping was **compiled to a seamless lithology + structure product with a
  unified legend across India**; §7.1.2 WMS/WFS public services; §7.1.3 "maximum of 29
  layers as per the 1:50K geodatabase … placed in public domain", GIS-format downloads via
  BHUKOSH; §7.1.4 **free of charge to registered users**; Annexure IV requires an online
  undertaking for Bhukosh downloads. NGDR brochure (Ministry of Mines, sha256
  `05cfe121…2016743`): "**Standard Geological Map (1:50K) — Area: 32.7 lakh sq km
  (TS: 5087)**". Tier table: guest = VISUALIZATION only; **DOWNLOAD requires a registered
  account**.
- **Reachability today.** `bhukosh.gsi.gov.in`: 443 connect timeout on `/` and
  `/Bhukosh/Public`, re-confirmed from a second network path (fetch service) — still down
  for us. `bhusanket.gsi.gov.in` ArcGIS REST (v11.2): now open, but folders `GSI`, `Hosted`,
  `Susceptibility`, `Sector_Map`, `Utilities` contain **only landslide and dashboard
  services — no geology layers**. `geodataindia.gov.in` (NGDR): reachable; anonymous
  `/api/datasets` → **401**; unauthenticated geoserver/arcgis paths → 404 or redirect to
  login; guest viewer bundles contain no anonymous service endpoints.
- **Coverage verdict.** The product is a national 1:50K compilation and Wayanad was
  systematically mapped at this scale historically (GSI Misc. Pub. No. 30 Pt IX, Kerala,
  bibliography: 1976 systematic mapping of Wynad taluks), but **Wayanad-specific
  full-district coverage could not be verified from files or metadata** without portal
  access. Per the standing rule, no tile/index/preview was treated as coverage proof; no
  data was downloaded; `GEO-02` remains `(not downloaded)`.
- **Distinct adjacent products, NOT geology (do not conflate).** KSDMA
  (`sdma.kerala.gov.in/hazard-maps/`, fetched 2026-10-28) hosts the **GSI 2022 landslide
  susceptibility zone shapefiles per district, including `Wayanad.zip`** — a
  susceptibility product from GSI's NLSM programme (1:50K macro-scale), not a geological
  map; it was not downloaded in this run (out of scope). The only 1:50K geological
  information on disk remains the **map plates inside the held GSI report PDFs**
  (14767/14768/14999) — reference only, not analysis-ready.

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

- Report index: `https://bhusanket.gsi.gov.in/json/LandslideReport/LandslideReport.json` — 1,188 reports total, **10 relate to Wayanad** (the phase-1 count of 8 came from a narrower title filter; the full enumeration is in `docs/SOURCE_DISCOVERY_REPORT.md`).
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

### 1.9 Landslide inventory — phase 2 additions

Phase 2 returned to the same publishers but asked a different question: not "what exists?"
but "what is on disk that has never been parsed?" That re-read produced more than the
downloads did.

| Source | Endpoint / access route | Result |
|---|---|---|
| **GSI 14115** Landslide Inventory of Kerala (FS 2007-2010) | already on disk from phase 1; Wayanad table pp.135-148 | **35 records**, arc-second coordinates, per-event dates 1961–2009, lithology, morphometry, impacts |
| **GSI PDLS 2024** (`gsi_PDLS_2024_51817.pdf`) | `.../Kerala/Post%20Disaster%20Studies/PDLS_2024_51817.pdf` | 4.9→15.1 MB, 1 Wayanad 42-point datasheet (Mundakkai-Chooralmala) |
| **GSI PDLS 2025** (`gsi_PDLS_2025_61074.pdf`) | same pattern | 22.5 MB, 1 Wayanad 42-point datasheet (Meenakshi Bridge, June 2024) |
| **GSI 14336 / 12272 / 12236** | same pattern | 12.7 MB; 12236 is image-only (no text layer) |
| **2018 Kerala monsoon inventory** (Hao, van Westen et al.) | `doi:10.17026/dans-x6c-y7x2`, DANS Dataverse, CC-BY-4.0 | 15.2 MB; 4,728 points statewide → **331 in Wayanad** |
| **KSDMA Meppadi PDNA 2024** | `sdma.kerala.gov.in/wp-content/uploads/2025/10/...` | 19.8 MB, 647 pp |
| **KSDMA Memorandum 17082024** | `sdma.kerala.gov.in/wp-content/uploads/2025/07/...` | 4.1 MB, 35 pp — event timing, rainfall, crown-to-village distances |
| **KSDMA October 2021 event report** | `sdma.kerala.gov.in/wp-content/uploads/2022/05/...` | 10.7 MB, 115 pp — **verified to contain no landslide inventory** (SEOC daily log) |
| **GFLD supplementary tables** t01–t03 | `nhess.copernicus.org/articles/18/2161/2018/` | 0.02 MB — **classification scheme only, no event database** |
| **PMC12290006 / PMC12749052** full text | NCBI efetch `db=pmc` | 0.3 MB JATS XML; event tables extracted |

Two phase-2 source classes were **closed rather than pursued**:

- **GFLD** does not redistribute its event database. The supplementary tables are the trigger
  taxonomy and summary statistics. It can contribute no Wayanad records.
- **KSDMA per-year pages** lead to needs assessments and memoranda, not inventories. They are
  excellent for verifying a known event and useless for discovering unknown ones.

See `docs/INVENTORY_VERIFICATION_REPORT.md` for what these records show.

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
| Kerala ILDM (`ildm.kerala.gov.in`) | **UNAVAILABLE** | TLS handshake fails for every path including `/`, over both https and http. Host-level failure, not a 404. |
| FABDEM (`data.bris.ac.uk`) | **ACCESS_RESTRICTED** | Connect timeout. |
| GSI 2019-20 "post-disaster studies in Wayanad and Kannur" (Sulal et al. 2020) | **UNAVAILABLE** | Cited in GSI's own 2025 bibliography but **absent from the public 1,188-report index** (verified by enumerating all 62 Kerala reports). This is why Puthumala 2019 is `SECONDARY_SOURCE_ONLY`. |
| `easy-migration.zip` (Dataverse export) | Failed | `ConnectionError` from `objectstore.surf.nl`. A Dataverse export artefact, not data — nothing of analytical value is missing. |

---

## 3. What was deliberately *not* done

- No attempt to bypass Earthdata, ArcGIS tokens, or portal logins.
- No global SRTM granule download (the earlier "Download All" trap).
- No reprojection, resampling, mosaicking, or clipping of the DEM/land-cover/rainfall rasters.
- No training table, no background/negative sampling, no model, no metrics.

Phase-2 specifics:

- **No silent merging.** The eight inventory sources are kept as eight separate files. Where
  records were judged to describe one landslide, that judgement is recorded in
  `duplicate_crosswalk.csv` with the measured separation and the basis, and expressed in the
  data only as a shared `event_group_id`. No coordinate, date or locality was overwritten.
- **No coordinate was snapped, rounded or relocated** to make a boundary or duplicate test pass.
  Records outside the district are flagged with their measured distance, not moved.
- **No date was invented.** GSI 14337 and 14768 place sites without dating them; those records
  remain `SITE_UNDATED` and are excluded from every event count rather than assigned a year.
- **No event year assigned by inference.** Where a source names two dates at one site
  (e.g. "1982 & June 2007"), the earlier occurrence is preserved in `date_text` and the
  in-window occurrence is used for coverage.

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
  landslide_inventory/kerala_2018_dans/   2018 statewide shapefile (phase 2)
  landslide_inventory/ksdma/              PDNA, Memorandum, Oct-2021 report (phase 2)
  landslide_inventory/gfld/               GFLD t01-t03 (phase 2)
  literature_events/                      PMC XML full texts (phase 2)
  additional/{hydrorivers/, osm_roads_wayanad.geojson}
data/interim/      text extracts, per-source inventory CSVs (not merged)
  gsi_pdf_text/                  one .txt per PDF, page-delimited
  inventory_extracts/            per-source CSV extracts
data/processed/    clipped copies only (geology, rivers, roads)
  inventory/                     consolidated records, events, crosswalk, coverage
docs/              manifest, this log, quality report, acquisition report,
                   source discovery report, inventory verification report
scripts/           every acquisition and validation script, re-runnable
```

Every raw file's SHA-256 is in `data/file_inventory.csv` (431 files, 7,808.5 MB as at the end of phase 2).
