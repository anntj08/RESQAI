# RESQAI — Phase 3 Preprocessing Report

**Phase:** 3 (geospatial preprocessing and data-readiness audit)
**Date:** 2026-10-26
**Base commit:** `c5e2c42` (Phase 2 complete)
**Scope:** Wayanad district, Kerala, India — landslide *susceptibility* covariates
**Reproduce with:** the scripts listed in §3, in order (see `docs/PHASE3_PROGRESS.md`)

> **What this document is.** A record of every transformation applied to the acquired data,
> with the measured cost of each one. Every number below was read out of the machine-readable
> validation files under `data/processed/*/…_validation.json`, `data/processed/qa/` and
> `data/processed/grid/`, not restated from an earlier report.
>
> **What this document is not.** It is not a model result. No training table was built, no
> model was fitted, and no accuracy, AUC or F1 figure exists anywhere in this project.
> Nothing here estimates *when* a slope will fail. Susceptibility = where terrain and
> environmental conditions favour failure.

---

## 0. Standing constraints honoured in this phase

| Constraint | How it was met |
|---|---|
| `data/raw/` must never be modified | All work reads raw files read-only; a pre-phase metadata snapshot (`data/interim/p3/inputs_metadata.json`) records every input's size, dimensions, CRS, transform, nodata and tags so drift is detectable. |
| Categorical rasters must never be interpolated | Land cover and lithology are handled as class codes only: mode aggregation, nearest for alignment, no bilinear anywhere near a class value. |
| Metric, never degree-based, measurement | All area, length, distance and buffer operations use EPSG:32643. Degrees are used only for storage and for reading native CHIRPS/SoilGrids geometry. |
| No silent inventory edits | The Phase 2 tables are byte-identical after this phase (SHA-256 compared). Suitability judgements live in new columns in a new file. |
| No fabricated dates, rainfall or validation | The rainfall series ends 2025-12 and 2026 is absent from every statistic. No date was imputed. No record was promoted from undated to dated. |
| Unrecorded cells are not negatives | Nothing in this phase produces a background/absence sample. That decision is explicitly deferred (§7). |
| Manifest is generated, never hand-edited | `docs/data_manifest.csv` is written only by `scripts/build_manifest.py`. |

---

## 1. Decisions taken before any file was touched

### 1.1 Working CRS — EPSG:32643 (WGS 84 / UTM zone 43N)

Wayanad spans **75.7722–76.4356 E**, entirely inside UTM zone 43N (72–78 E), and sits
1.77° west of the zone's central meridian (75 E). Inside a single zone the scale error is
below ~0.1 % across the district, and — critically — the district does **not** straddle a zone
boundary, so no point in Wayanad needs a zone exception. A metric CRS is mandatory because
slope, curvature, distance-to-feature and the 1,000 m terrain buffer are all meaningless in
degrees: one degree of longitude at 11.5 N is 109.3 km, one degree of latitude is 110.6 km,
and a "square degree" cell is not square.

EPSG:4326 is retained for storage of the native products and for anything that is handed to
another system. The projection is a working projection, not a datum change.

### 1.2 Grid and extent

| Property | Value |
|---|---|
| CRS | EPSG:32643 |
| Cell size | **30 m** (= 1 arc-second, the native support of the terrain source) |
| Origin | `x0 = 583110`, `y0 = 1264170` — floor of (district bounds − 1,000 m) to a multiple of 30 m |
| Dimensions | **2480 × 2013** pixels |
| Extent | 583110–657510 E / 1264170–1324560 N |
| Transform | `(30, 0, 583110, 0, −30, 1324560)` |
| Total pixels | 4,992,240 |
| District pixels | **2,356,538** |
| Mask area | **2,120.9 km²** |

Three deliberate choices:

1. **30 m, not 10 m.** The primary terrain source is 30 m. Building a 10 m grid would produce
   100 m² cells containing one third of a DEM sample, i.e. a grid finer than the information
   feeding it. That is a visual improvement and a scientific regression: it invites models to
   learn interpolation artefacts.
2. **Origin snapped to a 30 m multiple.** The grid is therefore reproducible from the GADM
   polygon alone, without carrying a magic coordinate forward, and every layer built on it is
   pixel-identical by construction rather than by luck.
3. **1,000 m buffer around the district.** Slope, aspect and curvature need a full 3×3
   neighbourhood. Without the buffer, every district-edge pixel has an incomplete neighbourhood.
   The buffer is applied in metres in EPSG:32643 and the products are clipped back to the
   district afterwards (§2.1).

The mask is produced with a **pixel-centre** rule (`all_touched=False`). Its area, 2,120.9 km²,
is 0.005 % below the GADM polygon's 2,121.0 km²; the same mask rasterised at 10 m gives
2,121.0 km². The 30 m rasterisation therefore does not distort the district outline.

### 1.3 Resampling rules

One rule per data type, and the effective resolution is written into the output tags so a later
consumer cannot mistake an upsampled layer for a native one:

| Data type | Rule | Applies to | Why |
|---|---|---|---|
| Categorical | **mode** (aggregate) / **nearest** (align) | land cover, lithology | Bilinear/bicubic would manufacture class codes that do not exist in the legend. Mode discards minority classes but never invents one. |
| Continuous, native cell ≤ ~10× grid cell | **bilinear** | DEM (30 m), soil (250 m) | Interpolating between neighbouring *measurements* of a continuous field is interpolation, not invention. Nearest would inject terracing into slope. |
| Continuous, native cell ≫ grid cell | **nearest** | CHIRPS (5.5 km) | A 5.5 km cell upsampled to 30 m has no internal gradient to interpolate; bilinear would fabricate smooth spatial structure across 180 grid cells that the source does not contain. |
| Vector → raster | rasterise, pixel-centre | geology, mask | Consistent with every other layer's footprint rule. |

**No layer claims a resolution better than its source.** The 30 m grid is a common *storage*
geometry; it is not a claim of 30 m information for soil (250 m), rainfall (5.5 km) or geology
(~1–4.6 km polygon scale).

### 1.4 Boundary — GADM 4.1, with a measured caveat

GADM 4.1 remains the working boundary. The cross-check against OSM/Nominatim is retained and
its result changes how the edge of the district must be interpreted.

The two polygons agree on **area** to 0.36 % (GADM 2,121.0 km², OSM 2,128.6 km²) — which is
exactly why area agreement alone is not evidence. Sampled every 50 m along each outline:

| Metric | GADM edge → OSM | OSM edge → GADM |
|---|---|---|
| Samples | 5,187 | 5,560 |
| Median separation | **744.1 m** | **770.7 m** |
| p90 | 1,078.2 m | 1,148.2 m |
| p99 | 1,319.0 m | 1,390.3 m |
| Maximum | 1,462.3 m | 1,578.6 m |
| Share within 100 m | 4.78 % | 4.57 % |
| Share within 500 m | 29.05 % | 28.17 % |

The symmetric difference is **8.75 % of the district** (89.05 km² present only in GADM,
96.6 km² present only in OSM). The largest single disagreement is a 42.2 km² patch around
75.956 E / 11.559 N and a 56.6 km² patch around 76.120 E / 11.849 N.

**Consequence, stated plainly:** a ±0.75 km band around the district edge is boundary-ambiguous,
and disagreements reach 1.6 km. District membership within that band is a boundary-definition
question, not a coordinate error. Four of the 23 inventory records lying outside GADM (all
KER2018, 212–648 m outside) fall **inside** OSM. Their Phase 2 `INCLUDED_BOUNDARY_REVIEW` label
is therefore supported by the cross-check — and it was **not** upgraded, because reclassifying
them would silently change published record counts. They stay flagged as boundary-uncertain
throughout Phase 3.

No official Survey of India / Kerala boundary is available to this project, so this uncertainty
cannot currently be reduced. It is carried forward as a documented limitation, not resolved.

### 1.5 DEM registration — a measured correction

All four DEM files carry `AREA_OR_POINT=Point`, pixel size exactly 1/3600°, the same stored
*y* origin 12.000139, and *x* origins exactly 1° apart:

| File | Shape | Stored x origin | First sample | Last sample |
|---|---|---|---|---|
| Copernicus E075 | 3600 × 3600 | 74.999861 | 74.999861 | 75.999583 |
| Copernicus E076 | 3600 × 3600 | 75.999861 | 75.999861 | 76.999583 |
| SRTM E075 `.hgt` | 3601 × 3601 | 74.999861 | 74.999861 | 75.999861 |
| SRTM E076 `.hgt` | 3601 × 3601 | 75.999861 | 75.999861 | 76.999861 |

**Mosaicking the two Copernicus tiles needs no resampling at all.** E075's last centre
(75.999583) and E076's first (75.999861) are exactly one 1/3600° step apart: contiguous, no gap,
no duplicated sample. The measured join spacing is 0.0002777778° = 1/3600° as expected.

**The `.hgt` mirror does repeat the tile-edge node.** E075's last sample (index 3600, at
75.999861) is the same coordinate as E076's first sample. The assertion in `p3_dem.py` checks
this rather than assuming it, and the mosaic drops **one duplicated column per join**, plus the
outer southern edge row (3601 → 3600). Nothing else.

**Identical tags are not proof of identical ground samples** — a 3600-centre tile and a
3601-node tile are different conventions even when both say `Point`. So the alignment was
measured directly: SRTM was resampled at offsets from −1.0 to +1.0 pixel in both axes (325,760
district samples) and the MAD against Copernicus compared.

| Offset | MAD (m) | | Offset | MAD (m) |
|---|---|---|---|---|
| **0, 0** | **3.42** | | 0, ±0.5 | 3.95 / 4.26 |
| ±0.5, 0 | 3.82 / 4.07 | | ±1.0, 0 | 5.02 / 5.43 |
| 0, ±1.0 | 5.42 / 5.87 | | −0.5, −0.5 | 4.22 |

The minimum sits exactly at (0, 0) and the MAD rises monotonically in every direction. A
half-pixel misregistration would have cost ~+0.4 m MAD and a one-pixel shift ~+1.6 m, so the
test is sensitive enough to detect the error it was looking for. **No half-pixel correction is
applied, because none is needed.**

What this proves: the two products are co-registered *relative to each other* as stored, so
cross-DEM comparison and any mixing are on one lattice. What it does not prove: absolute
geolocation. That rests on the four town checks in §2.1, which are only sensitive to ~50 m.

This supersedes the caution recorded in `AGENTS.md` that GeoTIFF DEMs are area-registered and
that naive mixing shifts data by half a pixel. The files are tagged `Point`, so the stated
dichotomy does not describe them, and the measurement above shows no relative offset exists.
`AGENTS.md` has been amended accordingly.

---

## 2. Information-preservation audit

### 2.1 Terrain (DEM and derivatives)

**Before → after**

| | Native Copernicus | Mosaic (4326) | Study grid, buffered | Study grid, district |
|---|---|---|---|---|
| Dimensions | 2 × 3600×3600 | 3600 × 7200 | 2013 × 2480 | 2013 × 2480 |
| Resolution | 1 arc-second | 1 arc-second | 30 m | 30 m |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 | EPSG:32643 |
| Valid pixels | 25,920,000 | 25,920,000 | 4,992,240 | 2,356,538 |
| Nodata | none declared | 0 after NaN check | 0 | 0 |
| Value range (m) | −9.97 … 2,632.65 | −9.97 … 2,632.65 | 1.3 … 2,230.27 | **116.96 … 2,230.27** |
| Mean / median (district, m) | — | — | — | 854.59 / 803.83 |
| std (district, m) | — | — | — | 179.89 |

The negative minimum (−9.97 m) is sea level in the tile margin, outside the district mask;
411 mosaic pixels are below zero and none is inside Wayanad (`elev_positive_pct` = 100.0).

**Why the range changed.** Phase 1 reported a district elevation range of 165–1,849 m, derived
from 2,085 random sample points inside the polygon. The full raster gives **117–2,230 m**. The
random sample missed the highest southern peaks and the lowest southern valley floors. The
Phase 1 figure was a sampling artefact and is superseded. Of the district, 0.196 % lies below
300 m and 0.065 % above 2,000 m; the low values sit in narrow southern valleys where the GADM
outline descends the Western Ghats escarpment. Both DEMs independently record them, so they are
treated as real rather than as artefacts — but they are not representative district terrain and
they carry the extreme slope values.

**Registration and georeferencing validation**

| Check | Result | Interpretation |
|---|---|---|
| Cross-DEM elevation, shared nodes in district | n = 2,280,319; mean diff −1.27 m; **MAD 3.42 m**; p95 8.74 m; max 147.03 m; **r = 0.9997** | Two independent products agree. Reproduces the Phase 1 figure (MAD 3.41 m). |
| Nodes differing by > 50 m | 447 (0.020 %) | Concentrated on steep southern faces where SRTM's 2000 radar surface and Copernicus's 2021 surface genuinely differ. |
| Round trip native → UTM → native | MAD 0.88 m; p99 4.03 m; max 15.98 m | Reprojection is close to lossless; residual is bilinear interpolation at 30 m, not a georeferencing error. |
| Sub-pixel alignment test (SRTM shifted −1…+1 px) | Minimum MAD at (0, 0) = 3.42 m; ±0.5 px gives 3.82–4.26 m; ±1 px gives 5.02–5.87 m | No relative misregistration exists between the two DEMs; see §1.5. |
| Ground check, four towns | Kalpetta 750.1 m (−29.9); Mananthavady 769.5 (−30.5); Sulthan Bathery 892.4 (−7.6); Vythiri 768.3 (−31.7) | All four return the expected town altitude within ~50 m. A transposed, mirrored or half-pixel-shifted mosaic fails this test. The consistent −30 m offset is the EGM2008 geoid — a vertical-datum difference, not a horizontal error. |

**Derivative validation**

| Derivative | Algorithm | Range | Mean | Nodata in district |
|---|---|---|---|---|
| Slope | Horn (1981), 3×3 | 0 – 67.77° | 11.53° (median 9.46°, p99 39.15°) | 0 |
| Aspect | Horn (1981), downslope, cw from N | 0 – 360° | 177.89° | 11,380 px (0.483 %) = flat ground, aspect undefined |
| Profile curvature | Zevenbergen & Thorne (1987) | −0.0459 … +0.0625 m⁻¹ | −0.000247 | 0 |
| Plan curvature | Zevenbergen & Thorne (1987) | −0.0511 … +0.0422 m⁻¹ | −0.000253 | 0 |

- **Aspect nodata is meaningful, not missing.** 11,380 district pixels (0.48 %) are genuinely
  flat (|∇z| below 1e-12). Their aspect is undefined; storing 0° would assert "due north" for a
  flat surface and inject a false signal. They are stored as nodata.
- **Same algorithm on the independent DEM:** slope mean 11.53° (GLO-30) vs 10.69° (SRTM),
  **MAD 2.24°**, p95 5.96°, r = 0.943. That ±2° is the honest uncertainty on the slope
  covariate. It is not a validation of correctness — both products can share a bias — but it
  bounds the disagreement between two independent acquisitions.
- **Plausibility guards:** maximum slope 67.8° (no impossible values); 0.011 % of pixels above
  60°; 6.656 % below 2°; no |curvature| above 1 m⁻¹.
- **Buffer necessity, measured:** of the 15,514 district pixels in the outer two-cell ring,
  **10,873 (70.09 %) would have no valid 3×3 neighbourhood** if derivatives were computed after
  clipping to the district. Among the 4,641 ring pixels that remain computable either way, the
  buffered and unbuffered values are **exactly identical** (max absolute difference 0.0), as
  they must be, since the neighbourhood is the same. The buffer adds coverage; it does not
  change any value.

**Deliberately not produced: TRI and TPI.** On a 30 m **DSM**, fine-scale roughness is dominated
by canopy and building texture rather than ground relief. TRI/TPI at this support would encode
land-cover noise as terrain. Profile and plan curvature at the 3×3 scale carry a defensible
geomorphological meaning; roughness indices do not, on this product.

**Standing caveat.** Copernicus GLO-30 is a **Digital Surface Model**. It includes canopy, and
Wayanad is 90 % tree cover. Elevation and slope are therefore surface values; under closed
canopy they sit several metres above and smoother than bare earth. This is not correctable
without a bare-earth DEM (FABDEM and SRTMGL1 are both unavailable to this project — see §8).

### 2.2 Land cover (ESA WorldCover 2021 v200)

**Before → after**

| | Native | District window (10 m) | Study grid (30 m) |
|---|---|---|---|
| Dimensions | 36,000 × 36,000 | 6,815 × 8,441 | 2013 × 2480 |
| Resolution | 10 m (1/12000°) | 10 m | 30 m (mode) |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 |
| District pixels | — | 25,337,122 | 2,356,538 |
| District area | — | **2,121.9 km²** (geodesic) | 2,120.9 km² (mask) |
| Nodata inside district | — | 0 | 0 |
| Classes present | 8 | 8 | 7 |

The true pixel area at 11.5 N is **83.75 m²**, not 100 m². A flat 100 m² assumption would have
reported the district as 2,533.7 km² — 19 % too large. The geodesic row-wise area (2,121.9 km²)
agrees with the GADM polygon to 0.04 %, which independently confirms the tile and the mask.

**Class composition: native 10 m vs produced 30 m**

| Code | Class | Native px | Grid px | Native % | Grid % | Change (pp) |
|---|---|---|---|---|---|---|
| 10 | Tree cover | 22,709,461 | 2,123,810 | 89.629 | 90.124 | **+0.495** |
| 20 | Shrubland | 1 | 0 | 0.000 | 0.000 | −0.000 |
| 30 | Grassland | 1,494,714 | 131,464 | 5.899 | 5.579 | −0.321 |
| 40 | Cropland | 748,243 | 69,307 | 2.953 | 2.941 | −0.012 |
| 50 | Built-up | 231,361 | 17,967 | 0.913 | 0.762 | **−0.151** |
| 60 | Bare / sparse | 4,932 | 243 | 0.019 | 0.010 | −0.009 |
| 80 | Permanent water | 147,298 | 13,654 | 0.581 | 0.579 | −0.002 |
| 90 | Herbaceous wetland | 1,112 | 93 | 0.004 | 0.004 | −0.000 |

Maximum absolute share change is **0.495 pp**. Mode-resampled and nearest-resampled grids
disagree on **1.21 %** of district pixels, which is the concrete benefit of using mode rather
than a naive nearest reduction.

**What the downsample cost.** Of all 30 m-equivalent native blocks, **8.62 % are not class-pure**
— they contain at least one differing neighbour at 10 m. In every such block the mode operation
discards the minority class. The visible casualties are exactly the small-area classes:

- **Built-up loses 0.151 pp** (0.913 % → 0.762 %, a 17 % relative reduction). Settlement edges
  are narrow relative to a 30 m cell; this is the class a landslide-susceptibility model is most
  likely to want as an anthropogenic-disturbance proxy.
- **Bare / sparse vegetation loses 46.7 % relative** (0.019 % → 0.010 %), from 4,932 native
  pixels to 243 grid cells.
- **Shrubland disappears entirely**: one native pixel, no grid cell. It is retained in the legend
  with zero area rather than deleted, so the loss is visible.

Corrective action taken: none at the pixel level — a mode reduction cannot preserve a
sub-cell class without inventing area — but the loss is quantified here, and the built-up class
is flagged in the readiness report as under-represented at 30 m. Any model that uses built-up as
a predictor inherits this bias.

**Temporal caveat.** WorldCover 2021 is a single-year snapshot. It is used as a present-day
land-cover covariate, not as the land cover at the time of each 2006–2024 landslide. No
historical land-cover product covering 2000–2026 exists on disk, and none was fabricated.

### 2.3 Rainfall (CHIRPS v2.0 monthly)

**Before → after**

| | Native monthly file | Padded window | Study grid |
|---|---|---|---|
| Dimensions | 7200 × 2000 (global 50S–50N) | 34 × 32 | 2013 × 2480 |
| Resolution | 0.05° (~5.5 km) | 0.05° | 30 m (nearest) |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 |
| **Declared nodata** | **none** (`nodata=None`) | — | −9999 |
| Stored sentinel | −9999 | −9999 present | masked |
| Files verified | **312 / 312** | — | — |

**Verification is exhaustive, not sampled.** All 312 gzip archives were streamed through CRC
verification, parsed as TIFFs, and read in full — ~18 GB of decompressed raster. Assertions on
every file: identical shape (7200×2000), identical transform, parse success. Result: the
sequence 2000-01 → 2025-12 is **complete and ordered, 0 duplicates, 0 missing, 0 unexpected**.

**The undeclared sentinel.** CHIRPS stores −9999 but does not declare it in the GeoTIFF tag. It
appears in all 312 files (10.48–10.49 M pixels each, ~73 % of the global grid). Inside the
0.5° padded window it is present in all 312 files, because the window reaches the Arabian Sea to
the west. **Inside the cells that actually overlap Wayanad it appears in 0 files.** The first
version of the check conflated the two and failed; the assertion was corrected to test the
district-overlapping cells specifically, which is the only thing district statistics depend on.
This distinction matters: a masked mean over the padded window would have been contaminated,
while the district mean is clean.

**Area weighting.** 97 native cells overlap the district, equivalent to 68.985 whole cells after
cos(lat) weighting. District values are area-weighted by the sub-cell overlap fraction
(10 × 10 subcells per 0.05° cell) times cos(lat). A pixel-centre mean over ~143 cells would
have biased the total, because the district crosses cell boundaries unevenly.

**District series (mm)**

| Statistic | Value |
|---|---|
| Monthly min / mean / max | 5.82 / 203.26 / 976.56 |
| Annual mean | **2,439.1** (std 351.0) |
| Driest year | 1,571.0 (2016) |
| Wettest year | 3,128.0 (2007) |
| JJAS mean | 1,601.1 = **65.6 %** of annual |
| Driest-month mean (Jan–Mar) | 19.4 |
| Wettest month | **July, 554.0** |

**Plausibility check, not validation.** The KSDMA Memorandum records 200.2 mm at Kalladi on
2024-07-29 plus 372.6 mm on 2024-07-30 (572.8 mm in two days). CHIRPS gives a district mean of
698.8 mm for July 2024 and a window maximum monthly value of 1,574.0 mm. That is the right order
of magnitude for a month containing two extreme days. It is **not** a validation of event
rainfall: a monthly 5.5 km field cannot represent the hours-scale trigger, and no monthly value
is attached to any individual landslide.

**Outputs and effective resolution.** Annual mean, JJAS mean and a 12-band monthly climatology
are written on the study grid by nearest-neighbour, with the effective resolution recorded in
the tags as 0.05° (~5.5 km). The 30 m grid carries 5.5 km values; the upsampling creates no
detail. Pixel counts: 2,356,538 valid, 0 nodata, in every band.

**Deliberately absent: 2026.** The acquired series ends 2025-12. No 2026 value was invented, and
no statistic in this report extends past 2025.

### 2.4 Soil (SoilGrids 250 m)

**Before → after**

| | Native | Native converted | Study grid |
|---|---|---|---|
| Files | 14 (7 properties × 2 depths) | 14 | 14 |
| Dimensions | 420 × 314 | 420 × 314 | 2013 × 2480 |
| Resolution | ~250 m (0.0022619° × 0.0023885°) | ~250 m | 30 m (bilinear) |
| dtype | int16, **scaled integers** | float32, physical units | float32 |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 |
| Valid native cells in district | 32,514 | 32,514 | 2,352,881 |
| Nodata | **none declared** | 0 → nodata | 3,657 px (**0.155 %**) |

**Scale factors applied.** SoilGrids stores integers. Using them raw is a factor-of-10 (or 100)
error that would still look plausible in a histogram:

| Property | Raw range | Factor | Unit | Physical range |
|---|---|---|---|---|
| bdod | 88–128 / 93–130 | ÷100 | g/cm³ | 0.88–1.28 / 0.93–1.30 |
| cec | 146–305 / 113–304 | ÷10 | cmol(c)/kg | 14.6–30.5 / 11.3–30.4 |
| cfvo | 89–256 / 90–278 | ÷10 | % vol | 8.9–25.6 / 9.0–27.8 |
| clay | 211–379 / 263–421 | ÷10 | % w | 21.1–37.9 / 26.3–42.1 |
| sand | 331–483 / 315–484 | ÷10 | % w | 33.1–48.3 / 31.5–48.4 |
| silt | 190–375 / 172–358 | ÷10 | % w | 19.0–37.5 / 17.2–35.8 |
| soc | 205–1184 / 99–688 | ÷10 | g/kg | 20.5–118.4 / 9.9–68.8 |

**Texture closure proves the factors are right.** After conversion, clay + sand + silt = 100.0 %
exactly (median 100.0, p05 99.94, p95 100.06, 100 % of 2,352,881 cells within 1 pp of 100).
That identity only holds if all three divisors are correct; a wrong factor on any one of them
would break it immediately.

**The undeclared nodata decision.** Every one of the 14 rasters contains exactly **8,312 zero
cells**, and the zero footprints are **identical across all 14 independent properties**
(`zero_footprint_identical_across_all_14: true`; min = max = 8,312 per file; 8,312 cells where any
file is zero and 8,312 where all are zero). 8,262 of those lie outside the district — the shape
of the acquisition crop's mask. A genuine clay = 0 % and a genuine bdod = 0 g/cm³ would not
coincide across 14 independent properties, and bdod = 0 g/cm³ is physically impossible.

Therefore **raw 0 is treated as nodata for all 14 rasters.** The cost is explicit: a genuine
cfvo = 0 % (coarse-fragment-free soil) is indistinguishable from a masked cell and is discarded
rather than guessed. 50 cells inside the district (3.1 km², 0.15 % of area) are lost this way.
This is the conservative choice — it removes data rather than fabricating it.

**No plausibility violations** in any property at either depth.

**Effective resolution.** Eight 30 m cells fall inside one 250 m prediction. The nominal cell is
also slightly anisotropic (246 m east–west, 265 m north–south at 11.5 N). Bilinear was used
because the native cell is only ~8× the grid cell, so interpolating between adjacent predictions
is meaningful; nearest would have produced blocky 8×8 plateaus that a model could mistake for
real structure. The effective resolution (250 m) is written into every output tag.

### 2.5 Geology (GLiM / LiMW 2015)

**Before → after**

| | Native GDB | Phase 1 product | District intersection | Study grid |
|---|---|---|---|---|
| Features | 1.23 M polygons (global) | 29 polygons (bbox clip) | **16 polygons** | 2013 × 2480 |
| CRS | **ESRI:54012** (World Eckert IV) | EPSG:4326 | EPSG:32643 | EPSG:32643 |
| Classes | — | 16 intersect the district | **5** | 5 |
| Area | — | — | 2,121.0 km² = **100.0 %** of GADM | 0 nodata |

**CRS correction.** The native identifier is `ESRI:54012`. `EPSG:54012` does not exist —
`pyproj.CRS.from_epsg(54012)` raises `CRSError`. The CRS must be read from the file, never typed
from memory.

**Clip correction.** The Phase 1 product is a **bounding-box** clip (district bbox + 0.05° pad)
containing 29 polygons, of which 16 intersect the district. It is kept unmodified and a proper
district intersection is written alongside it. Treating the Phase 1 file as a district layer
would have included 13 polygons of Malappuram, Kozhikode and Karnataka.

**Composition**

| Index | GLiM code | Description | Area (km²) | Share |
|---|---|---|---|---|
| 1 | mtam__ | Metamorphic, amphibolite facies | 1,226.1 | **57.81 %** |
| 2 | pa____ | Plutonic, acidic (granitoid / charnockite family) | 561.0 | 26.45 % |
| 3 | mt____ | Metamorphic, undifferentiated | 266.6 | 12.57 % |
| 4 | pb____ | Plutonic, basic | 66.7 | 3.14 % |
| 5 | pa__mt | Plutonic acidic with metamorphic overprint | 0.6 | 0.03 % |

**Is the layer local enough? — measured, not asserted.** 45 inventory records carry GSI field
lithology. All 45 fall inside the district; 43 fall inside a GLiM polygon. Comparing the GSI
outcrop description with the GLiM class under the same point:

| GSI family (field) | GLiM pa | GLiM mt | GLiM pb | outside |
|---|---|---|---|---|
| charnockite–gneiss (39) | 22 | 14 | 1 | 2 |
| charnockite (3) | 0 | 3 | 0 | 0 |
| gneiss (1) | 1 | 0 | 0 | 0 |
| schist / phyllite (2) | 1 | 1 | 0 | 0 |

The 39 records GSI describes as charnockite–gneiss split 22 / 14 / 1 across three GLiM classes.
That is measured proof that GLiM cannot resolve local lithology: it assigns a single point
population of charnockitic gneiss to both "plutonic acidic" and "metamorphic amphibolite".

**Scale.** Median distance from an inventory point to the nearest GLiM class boundary is
**1,063 m** (p90 4,623 m, min 8 m); mean polygon area 132.6 km². At 1:3.75 M, one millimetre on
the map is ~3.75 km on the ground. The 30 m raster carries polygon-scale classes; it does not
imply 30 m geological detail, and its tags say so.

GSI 1:50,000 geology remains undownloaded and is still the correct source for this covariate.

### 2.6 Roads and rivers

**Roads**

| | Raw OSM | In-district | Metric copy |
|---|---|---|---|
| Features | 24,063 | 13,169 | 13,169 |
| Vertices | 433,111 | 226,651 | 226,651 |
| Length | 11,758.5 km (includes outside) | **5,968.2 km** | 5,968.2 km |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 |
| Invalid / empty / null / zero-length / duplicate | 0 / 0 / 0 / 0 / 0 | same | same |

Clipping is an intersection, not a "within" filter: **0 features lost entirely**, and
**100.0 %** of the length that lies inside the polygon is retained (5,968.2 of 5,968.2 km).
attribute completeness is uneven and matters: `highway` 100 %, but `surface` 10.8 %, `ref` 3.9 %,
`name` 8.3 %. Class breakdown is dominated by `residential` (5,789) and `unclassified` (3,225);
`trunk` is 83 segments.

**Rivers**

| | Raw HydroRIVERS (Asia) | District clip | Metric copy |
|---|---|---|---|
| Features | 1,428,959 | 1,298 | 1,298 |
| Length | — | 3,195.5 km geometry | 3,195.5 km |
| Attribute length total | — | 3,384.4 km | — |
| CRS | EPSG:4326 | EPSG:4326 | EPSG:32643 |
| Stream orders | — | 1:673, 2:322, 3:178, 4:84, 5:41 | — |

The 189 km gap between geometry length and attribute `LENGTH_KM` total is expected and is not
data loss: each segment is cut at the district edge, so measured length is shorter than the
source's full-segment length. **40 segments (3.08 %)** have their `NEXT_DOWN` outside the clip —
the network is topologically truncated at the boundary. Flow routing would therefore require the
unclipped Asia network; the clipped layer is spatial context only. 0 duplicate `HYRIV_ID`.

**Deliberately not produced: distance-to-road and distance-to-river rasters.** Deriving them is a
modelling decision, not a preprocessing one. It requires a stated proxy rationale (road = cut
slope / anthropogenic disturbance; river = basal erosion / undercutting) and, for rivers, a
defensible stream-order threshold. Producing them now would prejudge the model design. The
validated metric line layers are in place for when that decision is taken.

### 2.7 Inventory preparation

The Phase 2 tables were **not modified**. This was verified by rebuilding them from source and
comparing SHA-256 hashes of all seven products: `build_consolidated_inventory.py` then
`assemble_inventory.py` reproduced every file **bit-for-bit identical** to what Phase 2
committed (`data/interim/p3/inventory_hashes_before.json`; pre-rebuild backup in
`data/interim/p3/inventory_backup/` — a local copy, not committed, as with all derived data).

A separate file, `inventory_spatial_suitability.csv` (468 rows), adds one auditable judgement per
source record. The original fields — `source_record_id`, coordinates, dates, `coord_precision_deg`,
`verification_status`, `event_group_id` — are carried through unchanged.

**Uncertainty model**

```
precision_radius_m       = 0.5 × printed_step_deg × 111320        (half a last printed digit)
precision_radius_diag_m  = precision_radius_m × √2                (conservative)
positional_uncertainty_m = max(precision_radius_m, source_accuracy_floor_m)
```

The per-source floors (GSI14115 10 m, KER2018 30 m, GSI14768 50 m, GSI14337 and NASA_GLC 0 m) are
**assumptions** about achievable plotting accuracy, not measured errors, and are labelled as
assumptions in `accuracy_floor_basis` on every row.

**Roles and uses**

| Label role | Count | Spatial use | Count |
|---|---|---|---|
| EVENT_POINT_IN_WINDOW (2000–2026, dated) | 372 | point_label_ok | **408** |
| SITE_EVIDENCE_UNDATED | 78 | review_widen_label | 36 |
| EXCLUDED_NOT_IN_DISTRICT | 12 | review_boundary_uncertain | 10 |
| HISTORICAL_PRE_2000 | 6 | exclude_not_in_district | 12 |
| | | exclude_district_centroid | 1 |
| | | exclude_until_corrected | 1 |

The 408 `point_label_ok` = 364 in-window + 38 undated sites + 6 pre-2000. Undated sites and
pre-2000 records are usable as *site evidence* (this slope has failed), never as dated events.

**Event groups.** 371 groups among the 372 in-window records; **363 groups have at least one
usable point label**, 8 do not. 339 groups are 2018, 32 are non-2018. Note that 372 records map
to 371 groups because `EV-2024-MUNDAKKAI` has two independent sources (GSI PDLS + the Sreekumar
2025 table) — corroboration, not duplication.

**Four findings that change how the inventory must be used**

1. **The "44 two-decimal records" are not 44 events, and almost none are in-window events.**
   They are 35 undated GSI 14337 site rows plus 9 NASA GLC rows, 7 of which are outside the
   district. Only **2 dated in-window records** carry a 2-decimal coordinate, and one of those
   two (`GLC/101`, locality "Wayanad") is a **district centroid**, not a site. The other
   (`GLC/10011`, "Highway 766") is usable only with a widened label. Reporting "44 events with
   ~1.1 km coordinates" would have been wrong in both numerator and interpretation.
2. **GSI 14337's 35 rows occupy only 28 unique coordinates**; 12 rows share a coordinate with
   another row. They are site descriptions at village-level precision, not 35 distinct points.
3. **The 33 accepted crosswalk pairs map onto only 26 distinct GSI 14115 sites.** 2 pairs were
   rejected outright (7,428.8 m and 16,579.0 m separation — a 2-decimal village centroid cannot
   be resolved to a specific site at those distances). The 33 accepted rows are therefore not 33
   independent new locations, and they must never be counted as such.
4. **A precision defect was found and corrected (in the new file only).** `GSI_PDLS/p95` prints
   whole-second DMS (`11027'46"N / 76008'03"E`) but stored `coord_precision_deg = 2.778 × 10⁻⁶`
   (0.01 arc-second; it displays as 0.000003). The printed coordinate supports 1 arc-second =
   **0.000278** — a factor of 100. The corrected value is written to
   `coord_precision_deg_verified`, taking the modelled uncertainty from 10 m (the accuracy floor,
   which hid the defect) to 15.5 m; the Phase 2 CSV is untouched so published numbers stay
   reproducible.

**What was explicitly not done:** no coordinate was snapped, relocated, rounded further or
deleted; no record was merged; `event_group_id` is preserved exactly as Phase 2 set it; no
undated record was promoted to an event; no date was imputed.

### 2.8 All 25 grid layers at a glance

Measured from `data/processed/qa/layer_inventory.csv` and `grid_alignment_report.json`.
All 25 share transform `(30,0,583110,0,−30,1324560)`, CRS EPSG:32643 and shape 2013×2480 —
**0 layers off-grid**.

| Layer | Bands | dtype | Valid px in district | Nodata % | min / median / max | Effective resolution |
|---|---|---|---|---|---|---|
| `district_mask_30m` | 1 | uint8 | 2,356,538 | 0.000 | 1 / 1 / 1 | 30 m |
| `dem_glo30_30m_district` | 1 | float32 | 2,356,538 | 0.000 | 117.0 / 803.8 / 2,230.3 m | 30 m (DSM) |
| `slope_deg_30m_district` | 1 | float32 | 2,356,538 | 0.000 | 0 / 9.46 / 67.77° | 30 m |
| `aspect_deg_30m_district` | 1 | float32 | 2,345,158 | **0.483** | 0 / 177.48 / 360.0° | 30 m |
| `profile_curv_30m_district` | 1 | float32 | 2,356,538 | 0.000 | −0.046 / −0.00011 / 0.062 m⁻¹ | 30 m |
| `plan_curv_30m_district` | 1 | float32 | 2,356,538 | 0.000 | −0.051 / −0.00021 / 0.042 m⁻¹ | 30 m |
| `landcover_…30m_district` | 1 | uint8 | 2,356,538 | 0.000 | classes 10–90 | 30 m (from 10 m) |
| 14 × `soil_…_30m_district` | 1 each | float32 | 2,352,881 | **0.155** | per property (§2.4) | **250 m** |
| `rainfall_annual_mean_30m` | 1 | float32 | 2,356,538 | 0.000 | 1,529.7 / 2,423.2 / 3,468.6 mm | **5.5 km** |
| `rainfall_jjas_mean_30m` | 1 | float32 | 2,356,538 | 0.000 | 792.0 / 1,630.3 / 2,457.7 mm | **5.5 km** |
| `rainfall_monthly_climatology_30m` | 12 | float32 | 2,356,538 | 0.000 | Jan 3.5–58.7 … Jul 211–822 mm | **5.5 km** |
| `geology_class_30m_district` | 1 | uint8 | 2,356,538 | 0.000 | classes 1–5 | **~1–4.6 km** |

Total nodata inside the district across all 24 predictor layers: aspect 0.483 %, soil 0.155 %,
everything else 0 %.

---

## 3. Transformation log

Every transformation, in execution order. Scripts are idempotent and can be re-run without
touching `data/raw/`.

**One input boundary matters here.** Phase 3 consumes four Phase 1 processed products and does
not re-derive them: `geology/glim_wayanad_clip.gpkg` and `geology/glim_wayanad_lithology_summary.csv`
(both from `scripts/clip_geology.py`) and `additional/osm_roads_wayanad_clip.gpkg` /
`additional/hydrorivers_wayanad_clip.gpkg`. Those two directories **mix Phase 1 and Phase 3
outputs**, so `data/processed/` must not be deleted wholesale — doing so removes inputs. The
runner checks these four and refuses to start without them. The roads clip in particular comes
from a live Overpass query and is **not** reproducible byte-for-byte by re-running its producer;
it is treated as a fixed input, not as a derived product.

| # | Operation | Input | Output | Script |
|---|---|---|---|---|
| 1 | Read-only metadata snapshot of every input | `data/raw/**` | `data/interim/p3/inputs_metadata.json` | `p3_inspect_inputs.py` |
| 2 | Select Wayanad feature; reproject GADM and OSM to EPSG:32643; compute grid extent and pixel-centre mask | GADM 4.1 JSON, OSM GeoJSON | `grid/wayanad_gadm_32643.gpkg`, `wayanad_osm_32643.gpkg`, `grid_spec.json`, `district_mask_30m.tif` | `p3_build_grid.py` |
| 3 | Sample both outlines at 50 m; measure separation, symmetric difference, and membership of the 23 outside-GADM records | boundaries + inventory | `grid/boundary_diagnostics.json` | `p3_boundary_diagnostics.py` |
| 4 | Mosaic 2 Copernicus tiles (no resampling); mosaic 2 `.hgt` (drop 1 duplicated column + 1 edge row); cross-DEM comparison at shared nodes | 2 + 2 DEM tiles | `dem/dem_glo30_mosaic_4326.tif` | `p3_dem.py` |
| 5 | Reproject mosaic to study grid, bilinear; keep buffered copy | mosaic | `dem/dem_glo30_30m_buf.tif` | `p3_dem.py` |
| 6 | Clip buffered DEM by district mask | buffered DEM | `dem/dem_glo30_30m_district.tif` | `p3_dem.py` |
| 7 | Horn 3×3 slope, aspect (downslope, cw from N); Z&T profile and plan curvature; pad edges; mark flat as nodata aspect; clip | buffered DEM | 4 derivative rasters | `p3_dem.py` |
| 8 | Round-trip check, ground check, buffer test, sub-pixel alignment test, cross-DEM slope | — | `dem/dem_validation.json` | `p3_dem.py` |
| 9 | Mode aggregation 10 m → 30 m; nearest control; native class census on geodesic pixel area | WorldCover tile | `landcover/landcover_worldcover2021_30m_district.tif`, legend CSV, validation JSON | `p3_landcover.py` |
| 10 | Stream 312 gzip archives through CRC + TIFF parse; build 34×32 window; subcell area-weight mask | 312 CHIRPS files | in-memory cube | `p3_rainfall.py` |
| 11 | Area-weighted district monthly series; annual and JJAS totals; 12-month climatology | cube | 3 CSVs | `p3_rainfall.py` |
| 12 | Native 4-band summary + 3 study-grid rasters (nearest) | cube | 4 GeoTIFFs | `p3_rainfall.py` |
| 13 | Apply ×10/×100 scale factors; map raw 0 → nodata; reproject bilinear | 14 SoilGrids files | 14 native + 14 grid GeoTIFFs, properties CSV | `p3_soil.py` |
| 14 | Texture closure, zero-footprint identity, plausibility | outputs | `soil/soil_validation.json` | `p3_soil.py` |
| 15 | Read native ESRI:54012; overlay with GADM; class-index rasterisation; site lithology cross-check | GLiM GDB + Phase 1 clip + inventory | GPKG, 2 CSVs, 1 GeoTIFF, validation JSON | `p3_geology.py` |
| 16 | Geometry validation on roads/rivers; clip-completeness and connectivity accounting; metric reprojection | OSM roads, HydroRIVERS | 2 GPKGs + validation JSON | `p3_additional.py` |
| 17 | Rebuild Phase 2 inventory and diff SHA-256 | Phase 2 scripts | hash comparison | (verification step) |
| 18 | Per-record suitability, uncertainty model, crosswalk resolution, event-group rollup | `inventory_source_records.csv` + crosswalk | `inventory_spatial_suitability.csv`, `event_group_point_status.csv`, summary JSON | `p3_inventory_suitability.py` |
| 19 | Grid alignment, nodata accounting, point coverage, clustering | all 25 layers + suitability | `qa/layer_inventory.csv`, `qa/grid_alignment_report.json`, `qa/readiness_metrics.json` | `p3_verify_processed.py` |

---

## 4. Feature lineage

Raw source → derived product → grid layer(s). Every row is reproducible from the script in §3.

| Source dataset (manifest ID) | Raw path | Derived product | Grid layer(s) | CRS path |
|---|---|---|---|---|
| DEM-01 Copernicus GLO-30 | `data/raw/dem/copernicus_glo30/` | `dem_glo30_mosaic_4326.tif` → `dem_glo30_30m_buf.tif` | `dem_glo30_30m_district`, `slope`, `aspect`, `profile_curv`, `plan_curv` | 4326 → 32643 |
| DEM-03 SRTM 1″ mirror | `data/raw/dem/srtm_1arcsec_skadi/` | cross-check only (slope) | none — validation only | 4326 → 32643 |
| LC-01 WorldCover 2021 | `data/raw/landcover/` | mode aggregation | `landcover_worldcover2021_30m_district` | 4326 → 32643 |
| RF-01 CHIRPS monthly | `data/raw/rainfall/chirps_v2_monthly/` | district series CSVs, native summary | `rainfall_annual_mean`, `rainfall_jjas_mean`, `rainfall_monthly_climatology` | 4326 → 32643 |
| SOIL-01 SoilGrids 250 m | `data/raw/soil/soilgrids250m/` | 14 × `_native250m` | 14 × `soil_*_30m_district` | 4326 → 32643 |
| GEO-01 GLiM / LiMW | `data/raw/geology/glim/` | `glim_wayanad_district_32643.gpkg` | `geology_class_30m_district` | ESRI:54012 → 4326 → 32643 |
| BND-01 GADM 4.1 | `data/raw/boundary/gadm41_IND_2/` | `wayanad_gadm_32643.gpkg` | `district_mask_30m` | 4326 → 32643 |
| BND-02 OSM boundary | `data/raw/boundary/osm_nominatim_wayanad.geojson` | `wayanad_osm_32643.gpkg` | none — cross-check | 4326 → 32643 |
| ADD-01 HydroRIVERS | `data/raw/additional/hydrorivers/` | `hydrorivers_wayanad_district_32643.gpkg` | none this phase | 4326 → 32643 |
| ADD-02 OSM roads | `data/raw/additional/osm_roads_wayanad.geojson` | `roads_wayanad_district_32643.gpkg` | none this phase | 4326 → 32643 |
| INV-01 … INV-16 | `data/raw/landslide_inventory/`, `data/raw/literature_events/` | Phase 2 tables (unchanged) + `inventory_spatial_suitability.csv` | sample points only | 4326 → 32643 |

---

## 5. Detected information loss and corrective action

| # | Loss or distortion | Magnitude (measured) | Cause | Corrective action | Residual risk |
|---|---|---|---|---|---|
| 1 | Built-up class under-represented at 30 m | 0.913 % → 0.762 % (−0.151 pp, −17 % relative) | mode aggregation discards sub-cell minority classes | quantified, flagged in readiness report | settlement-edge signal attenuated; any built-up predictor is biased against small clusters |
| 2 | Bare / sparse vegetation under-represented | 0.019 % → 0.010 % (−47 % relative); 4,932 px → 243 cells | mode aggregation | quantified | rare class; low weight in any model |
| 3 | Shrubland class lost entirely | 1 native px → 0 grid cells | mode aggregation | retained in legend with zero area so the loss is visible; not deleted | none material |
| 4 | Soil: 50 genuine cells lost inside district | 3.1 km² (0.15 %) | raw 0 mapped to nodata to avoid a false value | documented; conservative direction (data removed, not invented) | cells with true cfvo = 0 are dropped; 0.155 % of district nodata |
| 5 | Rainfall spatial detail | 5.5 km support carried on a 30 m grid | source resolution; upsampled by nearest | effective resolution written into tags and reported | 30 m appearance must not be read as 30 m information; hours-scale trigger not represented |
| 6 | Geology detail | polygon scale, median 1,063 m to a class boundary; 1:3.75 M | source scale | measured against 45 GSI field records; flagged as weak covariate | cannot resolve charnockite vs gneiss (22/14/1 split) |
| 7 | Land cover is present-day only | single 2021 snapshot vs 2006–2024 events | no historical LC product acquired | stated as a proxy, not a historical condition | mismatched land cover for older events |
| 8 | Elevation is surface, not bare earth | 90 % tree cover | GLO-30 is a DSM | labelled DSM in every output tag and doc | under-canopy slope under-estimated; no bare-earth DEM available |
| 9 | River network topologically truncated | 40 / 1,298 segments (3.08 %) | district clip cuts the network | counted; documented | no flow routing from the clipped layer |
| 10 | Roads are a 2026 snapshot | 0 features lost in clip, but no temporal depth | OSM has no historical state | stated as present-day proxy | roads built after an event are counted for it |
| 11 | No full 3×3 neighbourhood at district edge without buffer | 70.09 % of outer ring would be nodata | clipping before derivation | 1,000 m buffer; verified difference exactly 0 among computable pixels | none inside the district |
| 12 | Boundary position uncertain | median 744–771 m, max 1,579 m disagreement | GADM vs OSM generalisation; no official boundary | retained GADM; 10 records flagged `review_boundary_uncertain` | edge-adjacent labels and predictors ambiguous within ~±0.75 km |
| 13 | Horizontal precision of inventory | 408 usable labels, 2 in-window records at 300–800 m | source printing precision | classified A/C; 36 records flagged for widened labels | sub-100 m work not supportable for those records |
| 14 | 2026 absent | 312 months, 2000-01 → 2025-12 | acquisition window ends 2025-12 | no value invented | any 2026 event is outside the rainfall record |
| 15 | DEM vertical datum | −30 m consistent offset at all four ground checks | EGM2008 geoid vs orthometric town altitudes | documented; horizontal registration validated independently | elevation is relative to EGM2008; irrelevant for slope/curvature, relevant if absolute elevation is used |

---

## 6. Corrections to previously published project claims

These are measured corrections, not reinterpretations. Each is recorded so the earlier claim is
not silently reused.

| Earlier claim | Where | Measured now | Evidence |
|---|---|---|---|
| District elevation range 165–1,849 m | Phase 1 quality report | **117–2,230 m** | full-raster min/max; Phase 1 figure came from 2,085 random sample points (`dem_validation.json`) |
| GeoTIFF DEMs are area-registered; naive mixing shifts data by half a pixel | `AGENTS.md`, Phase 1 | These files are **point-registered** on one shared node grid | `AREA_OR_POINT=Point` on all four tiles; identical origin; measured join spacing exactly 1/3600° |
| GADM and OSM agree to 0.36 % | Phase 1/2 | area agrees to 0.36 % but the **outlines differ by 744–771 m median**, 8.75 % symmetric difference | `boundary_diagnostics.json` |
| Phase 1 geology clip is a district layer | Phase 1 | it is a **bbox clip** (29 polygons; 16 intersect) | `geology_validation.json` |
| "44 records have ~1.1 km coordinates" | Phase 2 report | 44 records *are* 2-decimal, but only **2 are dated in-window**, one of which is a district centroid | `inventory_suitability_summary.json` |
| SoilGrids nodata is undeclared with no evidence of where | Phase 1 | zero footprint is **identical across all 14 properties**, 8,312 cells each | `soil_validation.json` |
| `GSI_PDLS/p95` coordinate precision 2.778 × 10⁻⁶ ° | Phase 2 CSV | printed text supports **0.000278°** (factor 100) | verbatim printed DMS in the new suitability table |
| 100 m × 100 m ≈ one 10 m cell area unit | implicit in any area count | true cell area is **83.75 m²** at 11.5 N | geodesic row-wise area; naive assumption would inflate district area by 19 % |

---

## 7. Deliberately not produced, and why

| Not produced | Why |
|---|---|
| Training table / feature matrix | Out of scope for this phase. Sampling predictors at labels happened only to count coverage; values were discarded and never written. |
| Any model, split, or performance metric | No model exists. No accuracy figure may be reported. |
| Background / absence sample | Choosing pseudo-absences is a modelling decision with a large effect on results. Unrecorded cells are **not** assumed to be stable slopes, and nothing here treats them as such. |
| Distance-to-river, distance-to-road rasters | Requires a stated proxy rationale and a stream-order threshold. Premature. |
| TRI / TPI | On a 30 m DSM these encode canopy roughness, not ground relief. |
| Any 2026 rainfall | The series ends 2025-12. Inventing a value would violate the project's data rules. |
| Historical land cover | No product covering 2000–2026 is available to this project. |
| Bare-earth DEM | FABDEM (`data.bris.ac.uk`) and NASA SRTMGL1 both unreachable from this machine (§8). |
| Any polygon landslide footprint | No source on disk provides footprint geometry; all inventories are point or text records. |

---

## 8. Residual limits and blockers

**Carried into the modelling phase as known limitations**

1. Copernicus GLO-30 is a DSM. Under 90 % tree cover, slope is a surface slope.
2. Land cover, roads and rivers are present-day (2021 / 2026) proxies, not conditions at event time.
3. GLiM is 1:3.75 M and demonstrably cannot resolve local lithology. GSI 1:50,000 is missing.
4. Rainfall is monthly at 5.5 km. It supports antecedent-condition covariates, not triggers.
5. District boundary position is uncertain by ~0.75 km median; 10 records are flagged
   boundary-uncertain and were not reclassified.
6. 92.0 % of usable event labels come from 2018. Any model fitted on this inventory will learn
   2018's monsoon, not Wayanad's general susceptibility.

**Still blocked (unchanged from Phase 2)**

| Source | Failure |
|---|---|
| GSI Bhukosh | TCP connect timeout on 443, repeatedly |
| GSI Bhusanket ArcGIS REST | `499 Token Required` |
| GSI 2019-20 Wayanad/Kannur post-disaster report | absent from the public 1,188-report index |
| Kerala ILDM (`ildm.kerala.gov.in`) | TLS handshake fails on every path including `/` |
| FABDEM (`data.bris.ac.uk`) | connect timeout |
| NASA SRTMGL1 V003 | Earthdata Login required |
| KSDI, OneGeology WFS | connection timeout |
| Official Survey of India boundary | not available to this project |

**None of these blocks the readiness verdict in `docs/DATA_READINESS_REPORT.md`**, which is
derived from the data actually on disk. They do bound how far the resulting susceptibility map
can be trusted.

---

## 9. Reproducibility and verification

Added by the verification pass. Method details and the four defects it caught are in
`docs/PHASE3_PROGRESS.md` ("Recovery, verification and reproducibility").

### 9.1 Reproducibility was measured, not asserted

| Test | Method | Result |
|---|---|---|
| Raw inputs unmodified | re-hash all 431 files against the acquisition-time SHA-256 manifest `data/file_inventory.csv` (git-tracked, unmodified) | **431/431 match**, 7,808.5 MB, 0 size and 0 hash mismatches |
| Phase 2 products unmodified | re-hash the 7 inventory products against `inventory_hashes_before.json` **and** the on-disk backup | **7/7 byte-identical** |
| Determinism | run all 11 stages twice, compare generation A vs generation B | **68 byte-identical**, 6 content-equal, **0 failures** |
| Effect of the verification edits | compare outputs against the pre-recovery baseline | 68 byte-identical, 5 content-equal, **1 declared additive** (3 evidence keys in `rainfall_validation.json`), 0 failures |

The six content-equal files are GeoPackages (the container rewrites internal offsets, but
features, attributes, CRS and geometry compare equal) and the rainfall JSON, whose only
difference is the volatile `elapsed_s`. Byte identity was not accepted as the only standard and
size equality was never accepted as evidence: every non-identical file is parsed by type.

Comparison tolerances, stated rather than implied: raster pixels `atol 1e-6`, transform
precision `1e-9`, GeoPackage geometry `1e-12`, CSV numerics `1e-9`. Rasters are compared on
shape, CRS, transform, dtype, nodata, band count **and** pixel arrays; a container-level match
is never inferred from dimensions.

### 9.2 One verification script per class of claim

```
python scripts/p3_verify_all.py   # runs all six gates, writes data/interim/p3/verify_all.json
```

| Gate | Script | What it proves |
|---|---|---|
| 1 | `p3_verify_raw_immutable.py` | 431 raw files unchanged, by SHA-256 |
| 2 | `p3_verify_phase2_untouched.py` | 7 Phase 2 products unchanged, by SHA-256 |
| 3 | `p3_verify_processed.py` | 25 layers on one grid, nodata accounted for |
| 4 | `p3_check_consistency.py` | 470 doc-vs-data assertions |
| 5 | `p2_check_consistency.py` | 68 Phase 2 inventory invariants |
| 6 | `compare_rebuild.py` | 74 outputs reproduce from the pipeline |

Current state: **6/6 gates pass.**

### 9.3 What reproducibility does *not* cover

- The OSM roads clip is a live Overpass snapshot. It is a **fixed input**, hashed and treated
  like raw data, not a reproducible derivation. Re-running `acquire_osm_roads.py` would yield a
  different extract.
- `p3_inspect_inputs.py` samples value ranges for large rasters rather than scanning all of
  them; its snapshot is an identity check on sizes, dimensions, CRS, transforms, tags and
  sampled values — not a full content hash. Gate 1 supplies the content hash.
- Determinism is established on this machine, one Python/GEOS/GDAL stack. Byte identity across
  a different PROJ or GDAL version is not claimed.
