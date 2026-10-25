# AGENTS.md — RESQAI working conventions

Read this before touching the repository. It records decisions that were expensive to establish and
should not be silently reversed.

## Project

**RESQAI** — Resilient Emergency Intelligence Platform. Long-term: disaster decision intelligence
(synthetic scenarios, landslide/flood risk, GIS maps, decision support, apps, multi-agent coordination).
**Current scope:** Wayanad district, Kerala — landslide *susceptibility* mapping only.

**Hard rule:** susceptibility mapping estimates *where* terrain and environmental conditions favour
failure. It does **not** predict *when* a landslide will occur. Never describe output as a forecast,
warning, or timing prediction.

## Current phase

Dataset acquisition and validation. **Complete as of 2026-10-25** for 8 categories; see
`docs/ACQUISITION_REPORT.md`.

**Do not start modelling** until the user explicitly moves the project to the modelling phase. Do not
report accuracy, AUC, F1, or any performance number — none has been produced.

## Verification vocabulary (do not blur these)

- `VERIFIED` — file integrity, format, CRS, resolution, full district coverage and a value plausibility
  check were all confirmed on the actual file.
- `DOWNLOADED_NOT_FULLY_VALIDATED` — file is readable and matches the source's claims, but record-level
  accuracy is unconfirmed (rounded coordinates, missing dates, no field check).
- `IDENTIFIED_NOT_DOWNLOADED` / `ACCESS_RESTRICTED` / `UNAVAILABLE` — see `docs/data_manifest.csv`.

A download URL is not evidence. A preview image is not a dataset. A tile name is not a coverage proof.

## Data layout

```
data/raw/          originals exactly as downloaded — never edit in place
data/interim/      derived text/CSV extracts, per-source, not merged
data/processed/    clipped/reprojected working copies
docs/              manifest, sources, quality report, phase reports
scripts/           acquisition + validation, one concern per script, re-runnable
```

Raw data is **not** committed to git (see `.gitignore`). Docs, scripts and manifests are.

## Known facts that must not be re-derived wrongly

- Wayanad spans 75.7722–76.4356 E / 11.4427–11.9706 N. It **straddles 76°E**: one SRTM/Copernicus 1°
  tile covers only 71.5% of the district. Two tiles (E075 + E076) are required.
- The two DEMs (Copernicus GLO-30, SRTM 1″ mirror) agree at r = 0.9997, MAD 3.41 m.
- NASA SRTMGL1 V003 is auth-gated; Copernicus GLO-30 is the primary terrain source by decision.
- GADM 4.1 is the working boundary (2,121.0 km²), cross-checked against OSM (2,128.6 km²).
- GLiM geology is 1:3.75 M — coarse; GSI 1:50,000 remains missing.
- Inventory: 89 records extracted across 4 sources, with heavy overlap (22/29 of 14768 within 1 km of
  14337). Effective distinct events ≈ 55–65, not 89.
- 35/89 inventory records have ~1.1 km coordinate uncertainty.
- No inventory contains the July 2024 Wayanad landslides.

## Required care in later phases

1. **Never** interpolate categorical rasters (land cover, lithology, soil class) with bilinear/bicubic.
2. SRTM `.hgt` is point-registered (3601 samples); GeoTIFF DEMs are area-registered (3600 cells).
   Naive mixing shifts data by half a pixel (~15 m).
3. CHIRPS stores nodata as −9999 **without declaring it** in the GeoTIFF tag. Mask explicitly.
4. SoilGrids values are scaled integers (clay ×10, bdod ×100, soc ×10, cec ×10, cfvo ×10).
5. Use a metric CRS (EPSG:32643, UTM 43N) for slope, distance, and area. Keep EPSG:4326 for storage.
6. Validation must be **spatially blocked** (or grouped by landslide cluster). Random train/test splits
   on clustered points inflate performance through spatial autocorrelation.
7. Preserve per-record provenance and coordinate precision through any merge. Do not silently snap,
   round, or deduplicate inventory points.
8. Synthetic events, if ever generated, must be labelled as synthetic and never evaluated as real.

## Style

- Beginner-friendly explanations when the user is doing UI work; precise technical language in docs.
- Separate confirmed facts from assumptions and recommendations.
- One dataset at a time when the user drives the workflow.
