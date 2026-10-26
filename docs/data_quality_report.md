# RESQAI — Data Quality Report

**Date:** 2026-10-25 · **Study area:** Wayanad, Kerala (2,121 km²)
**Stage:** post-acquisition validation. Nothing here is a model result.

## Verification standard used

`VERIFIED` means **all** of the following were checked on the actual file:
byte-level integrity, readable format, declared coordinate reference system, stated/derived resolution,
geographic coverage of the full district, and a plausibility check on the values (histogram, range, or
cross-comparison). It does **not** mean the dataset is scientifically ideal for landslide susceptibility — that
is recorded separately under *Fitness*.

`DOWNLOADED_NOT_FULLY_VALIDATED` means the file is readable and the content matches what the source document
claims, but the record-level accuracy cannot be confirmed from the file alone (typically: rounded coordinates,
missing dates, no field check).

---

## 1. Terrain (DEM)

| Check | Copernicus GLO-30 | SRTM 1" (Skadi) |
|---|---|---|
| Files readable | 2/2 | 2/2 |
| Size / shape | 3600×3600, float32, deflate, tiled | 3601×3601, int16 |
| CRS / resolution | EPSG:4326, 0.0002778° (1″) | EPSG:4326, 0.0002778° (1″) |
| Coverage of district | 100.00% | 100.00% |
| Elevation range in district | 165–1,849 m ~~(superseded — see §11.1)~~ | 158–1,856 m ~~(superseded)~~ |
| Voids | none flagged | 0 cells equal to −32768 |
| Registration | — | agrees with Copernicus, r = 0.9997 |

**Cross-DEM agreement:** 2,085 random points inside the district, all valid.
Mean difference (Copernicus − SRTM) = −1.44 m, MAD = 3.41 m, p95|Δ| = 8.50 m, max |Δ| = 54.9 m,
one point above 50 m. This is the expected signature of two independent 30 m DEMs over steep terrain, and it
also confirms the Skadi mirror is a faithful SRTM 1" copy rather than a resampled lower-resolution product.
Phase 3 repeated this exhaustively at every shared node (2,280,319 nodes): mean −1.27 m, MAD 3.42 m,
p95 8.74 m, max 147.0 m, 447 nodes above 50 m. The random sample under-counted steep-face disagreements;
the exhaustive figures in §11.2 supersede these.

**Fitness caveats**
- Copernicus GLO-30 is a **DSM**: it includes canopy and built structures. SRTM C-band also partly reflects
  canopy. In a district that is 89.6% "tree cover" per WorldCover, both will over-state ground elevation under
  dense forest by amounts that vary spatially. Slope derived from either is therefore a *canopy* slope in those
  areas — acceptable for regional susceptibility, not for engineering-scale stability analysis.
- Vertical datum is EGM2008 (orthometric); SRTM HGT is also EGM96/EGM2008-referenced. They are mutually
  consistent, so no correction is needed while both stay in the same family.
- The HGT grid is **point-registered** (3601 samples), while GeoTIFF tiles are **area-registered** (3600 cells).
  Mixing them without accounting for the half-pixel shift will produce a systematic ~15 m offset. Must be handled
  at mosaic time, not silently.

  **Corrected by Phase 3 measurement — see §11.3.** These specific files are all tagged
  `AREA_OR_POINT=Point` and share one node grid; the half-pixel shift described above does not apply
  to them, and applying it would introduce the offset it warns about.

---

## 2. Land cover (ESA WorldCover 2021 v200)

- 36,000×36,000 uint8, 0.0000833° (~10 m), EPSG:4326, 11 classes, values 10–95 (integer class codes).
- Coverage of district: 100.00%.
- Class composition inside the district (% of valid pixels):

| Code | Class | Share |
|---|---|---|
| 10 | Tree cover | 89.63% |
| 30 | Grassland | 5.90% |
| 40 | Cropland | 2.95% |
| 50 | Built-up | 0.91% |
| 80 | Permanent water bodies | 0.58% |
| 60 | Bare / sparse vegetation | 0.02% |
| 90 | Herbaceous wetland | <0.01% |
| 20 | Shrubland | <0.01% |

**This distribution is the single most important land-cover caveat.** Wayanad's economy is dominated by
shade-grown coffee, tea, rubber and cardamom. WorldCover's 10 m classifier maps most of that canopy as
**Tree cover**, so "forest" and "plantation" collapse into one class. For a landslide model this matters:
plantation slopes are managed, periodically cleared, and often cut for roads — they do not behave like closed
forest. Treating class 10 as homogeneous will blur a real physical distinction.

**Also:** land cover is a 2021 snapshot. The inventory contains events from 2006–2018. Land cover at the time of
those events is not observed; a 2021 map is a proxy with unknown error back to ~2006 (a 15-year gap in a district
with active plantation conversion).

---

## 3. Rainfall (CHIRPS v2.0 monthly)

- 312/312 months present (2000-01 → 2025-12), 4.55 GB; every gzip stream reads cleanly end-to-end.
- Grid 7,200×2,000, 0.05° (~5.5 km), EPSG:4326, float32, **nodata stored as −9999 but not declared in the
  GeoTIFF tag** — any naive `read()` will pull −9999 into means. Must be masked explicitly.
- Wayanad-window climatology computed as a sanity check: **2,526 mm/yr** (2000–2025), JJAS mean 420 mm/month.
  2024 = 2,601 mm/yr. These are consistent with published Western Ghats rainfall (≈2,000–3,000 mm/yr).
- Monthly June 2018 window mean 483 mm, July 2024 mean 631 mm — consistent with the two major event years.

**Fitness caveats**
- Monthly resolution cannot represent the rainfall intensity that actually triggers a landslide (hours).
  It supports *antecedent-condition* predictors (e.g. 30/60/90-day totals, monsoon anomaly), not trigger timing.
- 0.05° ≈ 5.5 km means roughly 12×18 pixels cover the district. Orographic gradients across the Western Ghats
  escarpment are much sharper than that; CHIRPS is known to smooth them.
- CHIRPS is a gauge–satellite blend, not a dense local gauge network. No IMD station data was obtainable
  (login-gated), so there is no independent local check on these values.

---

## 4. Geology (GLiM / LiMW 2015)

- 1,235,259 polygons globally; 29 in the Wayanad bbox, 16 intersecting the district.
- Native CRS World Eckert IV (`ESRI:54012`); reprojected to EPSG:4326 for the clip only.
- Lithology classes intersecting Wayanad:

| GLiM code | Meaning | Share of district |
|---|---|---|
| `mtam__` | Metamorphic (amphibolite-facies) | 57.81% |
| `pa____` | Plutonic, acidic (granitoid/charnockite family) | 26.45% |
| `mt____` | Metamorphic, undifferentiated | 12.57% |
| `pb____` | Plutonic, basic | 3.14% |
| `pa__mt` | Plutonic acidic with metamorphic overprint | 0.03% |

  *(The code column previously printed two codes per row, which read as though `mt` meant both
  "amphibolite facies" and "undifferentiated". The classes are the five above; the shares are
  unchanged.)*

- **Phase 3 correction — the Phase 1 clip is not a district layer.** `glim_wayanad_clip.gpkg` is a
  **bounding-box** clip (district bbox + 0.05° pad). It holds 29 polygons, of which only 16
  intersect the district; the other 13 belong to Malappuram, Kozhikode and Karnataka. It is kept
  unmodified and the district intersection is a separate file. See §11.5.

**This is the weakest dataset in the collection.** GLiM's average source scale is **1:3.75 million** — effective
detail on the order of kilometres, not the 1:50,000 GSI maps that the source GSI reports themselves used.
For a 2,121 km² district it yields five classes, with the dominant class covering 58%. Any model given this layer
can learn at most a very coarse lithological contrast, and it cannot represent the charnockite/gneiss/migmatite
boundaries that local landslide studies rely on.

GSI Bhukosh (which would carry 1:50,000 geology) was unreachable, and the Bhusanket ArcGIS services are
token-gated. **A better geology layer remains an open acquisition gap**, not a solved problem.

---

## 5. Soil (ISRIC SoilGrids 250 m)

- 14 GeoTIFFs, all on an identical grid: 420×314, 0.00226°×0.00239° (~250 m), EPSG:4326, int16.
- Values are **scaled integers**, not physical units: clay/sand/silt ×10 (g/kg → %), bdod ×100 (cg/cm³),
  soc ×10 (dg/kg), cec ×10 (mmol(c)/kg), cfvo ×10 (cm³/100cm³). Dividing by the documented factor is required;
  this is a conversion trap if the rasters are consumed raw.
- nodata is not declared; some cells are 0, which for bdod/soc may be genuine or may be masked ocean/edge cells.
  Flagged for inspection at preprocessing time.
- Two depths retained (0–5 cm, 15–30 cm) because shallow translational slides in Kerala typically fail within
  the top 1–3 m; the 0–5 cm layer alone would miss the rooting-depth control.

**Fitness caveats:** SoilGrids is a global prediction (machine-learned from sparse profiles), not a soil survey.
Its published uncertainty at 250 m in the Western Ghats is substantial, and it does not represent regolith
thickness — which the GSI reports explicitly used as a stability input. No local soil map was obtainable.

---

## 6. Boundary

| Check | GADM 4.1 | OSM/Nominatim |
|---|---|---|
| Geometry | MultiPolygon, valid | MultiPolygon, valid |
| Area (UTM 43N) | 2,121.0 km² | 2,128.6 km² |
| Bounds | 75.7722–76.4356 E, 11.4427–11.9706 N | 75.7731–76.4435 E, 11.4514–11.9787 N |
| Agreement | — | 0.36% area difference ~~(superseded — see §11.4)~~ |
| Outline separation | — | **median 744 m (GADM→OSM) / 771 m (OSM→GADM)**, p90 ~1.1 km, max 1,579 m |
| Symmetric difference | — | **8.75% of the district** (89.05 + 96.6 km² of unique area) |

**The 0.36% area agreement does not mean the outlines agree.** Phase 3 sampled both outlines
every 50 m: the median separation is ~750 m and the symmetric difference is 8.75% of the
district. Two polygons can enclose nearly the same area while disagreeing almost everywhere
along the edge. Area agreement is therefore not evidence of positional agreement, and only the
outline measurement supports the ±0.75 km boundary uncertainty carried into §11.4.

Neither is an official Survey of India / Kerala Government boundary. They agree closely enough to be used
interchangeably for acquisition and rough clipping, but **the final study-area definition should be replaced by
an official boundary if one can be obtained**. GADM is adopted as the working boundary because it is stable,
versioned, and citable.

---

## 7. Landslide inventory — the critical uncertainty

**Extracted, per source, without merging:**

| Source | Records | Inside district | Coordinate precision | Dates |
|---|---|---|---|---|
| GSI 14337 (Annexure-1) | 35 Wayanad | 35/35 | 2 decimals (~1.1 km) | generally absent |
| GSI 14768 Table 4 (archival) | 29 | 23/29 | 0.1–1 arc-sec (~3–30 m) | absent |
| GSI 14768 Table 5 (field) | 17 | 13/17 | 1 arc-sec (~30 m) | absent |
| GSI 2018 post-disaster | 8 | 8/8 | 4 decimals (~11 m) | 14–16 June 2018 |
| **Total extracted** | **89** | **79** | mixed | mostly undated |

**Overlap is substantial and unresolved.** Nearest-neighbour comparison in UTM 43N:

- 10/29 of the 14768 archival records lie within 500 m of a 14337 record; 22/29 within 1 km.
- 8/17 of the 14768 field records lie within 500 m of an archival record.
- The 2018 records do not duplicate the older ones (0/8 within 500 m).

So the **effective number of distinct events is materially below 89** — plausibly in the 55–65 range, but that
cannot be asserted without resolving which records refer to the same slope. This is the main reason the
inventories were kept separate rather than concatenated.

**Why the 2-decimal coordinates matter.** At 11.5°N, 0.01° ≈ 1.11 km in latitude and ≈ 1.09 km in longitude.
The 14337 points can therefore be up to ~780 m from the true failure (half a cell diagonal), which is **26 times
the 30 m DEM cell**. Sampling terrain predictors at those coordinates will frequently read the wrong slope facet.
Any model built on them will have label noise that no algorithm can remove. Mitigations exist (snap to the
nearest ridge-cut or to a mapped scar, widen the label to a neighbourhood), but they are preprocessing decisions
that must be made and documented explicitly — not silently.

**Temporal problems.**
- Most records are undated, so no event-window rainfall can be attached to them.
- The catalogues stop in 2018. The **30 July 2024 Punjarimattom/Chooralmala landslide**, the largest in the
  district's recent history, is **not** in any acquired inventory. A Wayanad susceptibility dataset that omits it
  is not representative of the current hazard. Acquiring 2019–2025 events is an open gap.
- 14768's archival table covers a study area extending beyond the district (6 points fall outside the GADM
  polygon, in Malappuram/Kozhikode). Those must be dropped or re-assigned deliberately, not by accident.

**Inventory completeness is unknown.** No source states a detection probability or a mapping completeness for
Wayanad. Absence of a record is not absence of a landslide, which is exactly why background/negative sampling
must be designed rather than assumed.

### 7.1 Phase 2 update — supersedes the paragraphs above where they conflict

The phase-1 text above describes 89 records from 4 GSI extracts. Phase 2 added four more sources and resolved
several of the open questions. Full detail: `docs/INVENTORY_VERIFICATION_REPORT.md`.

| Source | Records | Dated | Coordinate precision | Status |
|---|---:|---:|---|---|
| KER2018 (Hao/van Westen 2018 Kerala inventory) | 331 | 331 (year only) | 5 dp | `VERIFIED`, composite (NRSC+GSI) |
| GSI 14768 Tables 4+5 | 46 | 0 | 0.1–1 arc-sec | `DOWNLOADED_NOT_FULLY_VALIDATED` |
| GSI 14115 Wayanad table | 35 | 33 | arc-second | `VERIFIED` (13/13 spot checks) |
| GSI 14337 Annexure-1 | 35 | 0 | 2 dp (~1.1 km) | `DOWNLOADED_NOT_FULLY_VALIDATED` |
| NASA GLC | 9 | 9 | 2 dp | `VERIFIED` |
| GSI 2018 post-disaster | 8 | 8 | 4 dp | `DOWNLOADED_NOT_FULLY_VALIDATED` |
| GSI PDLS 2024 + 2025 | 2 | 2 | arc-second | `VERIFIED` |
| Sreekumar et al. 2025 Table 1 | 2 | 2 | whole-second DMS | `DOWNLOADED_NOT_FULLY_VALIDATED` |
| **Total** | **468** | **385** | mixed | **83 undated site records** |

**Overlap is now measured, not estimated.** 45 candidate pairs in `duplicate_crosswalk.csv`:

- **33/35 GSI 14337 rows are within 1.5 km of a GSI 14115 row**, median separation **471 m**, 7 within 300 m.
  These are the same investigation sites, so the 14115 coordinate supersedes the 2-decimal one.
- **8 GSI 2018 slides are 361–1,453 m from any mapped 2018 point** — same monsoon cluster, **no duplicate
  confirmed**. Keeping them separate is deliberate.
- The July 2024 GSI record and an independent publication agree to **495 m**.

**The 2-decimal problem is partly solved.** 44 of 468 records remain at 2 dp (GSI 14337 + NASA GLC), down
from "35 of 89" in proportional terms. Where a 14115 match exists, usable precision improves from ~1.1 km to
sub-30 m. The remaining 44 rows must still not be used as point labels without widening or snapping, exactly
as the phase-1 caveat says.

**Temporal problems — partly resolved.**
- 385 records now carry a date; **332 of the 372 in-window records resolve only to a year**, so antecedent
  event-window rainfall still cannot be attached to most of them.
- The **30 July 2024 Mundakkai-Chooralmala** event is now recorded (GSI PDLS 2024) and its coordinate
  corroborated. It is no longer a gap.
- **2020–2023 still have no records**, because no GSI post-disaster volume exists for those years. That is an
  observation gap and must be treated as such.
- The 6 GSI 14768 archival points outside the GADM polygon were resolved by a measured distance rule:
  **5 at Vazhikkadavu are 17.1–17.4 km outside** and are now excluded; the rest sit within 1.2 km of the
  boundary and are retained with a flag. See `INVENTORY_VERIFICATION_REPORT.md` §8.

---

## 8. Additional layers

| Layer | Volume | Main caveat |
|---|---|---|
| HydroRIVERS (1,298 segments, 3,195 km) | 90.5 MB (Asia) | Modelled network; headwater streams below threshold absent; no flow accumulation/order filtering yet |
| OSM roads (13,169 segments, 5,968 km) | 6.1 MB | Crowd-sourced, rural completeness uneven; "road present" ≠ "cut slope present" |

Both are usable as distance-to-feature predictors, with the caveat that distance-to-road is a proxy for
anthropogenic slope disturbance, not a physical trigger.

---

## 9. Cross-cutting alignment issues (for the preprocessing phase)

1. **Resolution spread:** 10 m (land cover) → 30 m (DEM) → 250 m (soil) → 5.5 km (rainfall) → 1:3.75 M (geology).
   ~~Every layer except land cover must be upsampled to a common grid; the choice of 30 m as the working grid is
   defensible but must be stated, and categorical layers must use nearest-neighbour, never bilinear.~~
   **Corrected by Phase 3:** the direction is not uniform. Land cover is *downsampled* 10 m → 30 m by
   **mode**; the DEM is already 30 m and is only reprojected; soil (250 m) and rainfall (5.5 km) are
   *upsampled* by bilinear and nearest respectively; geology is rasterised from polygons. Nearest is
   right for class codes and for a 5.5 km field, bilinear for genuinely continuous fields whose native
   cell is only a few times the grid. See `docs/PREPROCESSING_REPORT.md` §1.3.
2. **CRS:** all acquired layers are EPSG:4326 except GLiM (Eckert IV, already reprojected for the clip).
   A metric CRS (UTM 43N, EPSG:32643) is required for slope, distance and area calculations.
3. **NoData conventions differ:** −9999 (CHIRPS, undeclared), 0 (WorldCover class nodata), −32768 (SRTM HGT),
   absent (Copernicus, SoilGrids). A single harmonisation rule is needed before any stack is built.
   *Resolved in Phase 3:* every processed layer declares −9999 and every raw input was read with its own
   native convention retained; SoilGrids raw 0 and WorldCover 0 were mapped to nodata explicitly (§11.6).
4. **Registration:** ~~SRTM HGT point-registered vs GeoTIFF area-registered — half-pixel shift if mixed naively.~~
   **Corrected by Phase 3 measurement:** these four DEM files are all tagged `AREA_OR_POINT=Point` and sit
   on one shared node grid. No half-pixel shift applies, and imposing one would create the error it warns
   about. See §11.3.
5. **Spatial autocorrelation:** 371 in-window event groups in 2,121 km², but 339 are the 2018 monsoon and
   332 resolve only to a year. The *independent* time spread is much smaller than the record count suggests.
   *Phase 3 re-measured this on the 364 in-window records that are usable point labels:
   **335 (92.0%) are 2018** and **328 resolve only to a year** (8 month, 26 day, 2 multi-event).
   The 332 in §7.1 is over all 372 in-window records; the two counts differ only by denominator,
   and the 364-record figures are the ones the readiness verdict uses.*
   Records cluster in a few villages (Kottapadi, Muppainadu, Vythiri, Thirunelly). Random train/test splits
   will leak. Any validation must be spatially blocked (or grouped by landslide cluster). This is a design
   constraint on the *next* phase, recorded now so it is not forgotten.
6. **Class balance:** the count of independently dated, precisely located events is far below 371. Background
   sampling and any performance estimate must reflect that; a metric from a handful of clusters will have
   wide confidence intervals and should be reported as such — or the inventory expanded first.

---

## 10. Fitness summary

| Dataset | Verified | Fit for Wayanad susceptibility | Main risk |
|---|---|---|---|
| DEM (Copernicus + SRTM) | Yes | Good | DSM/canopy bias on slopes |
| Land cover (WorldCover) | Yes | Fair | Plantation ≙ forest; 2021 vs 2006 events |
| Rainfall (CHIRPS) | Yes | Fair | Monthly, 5.5 km, no event timing |
| Geology (GLiM) | Yes | **Poor** | 1:3.75 M scale for a 2,121 km² district |
| Soil (SoilGrids) | Yes | Fair | Global prediction, no regolith depth |
| Boundary (GADM) | Yes | Good | Not an official boundary |
| Inventory (GSI + KER2018 + literature) | Yes | **Conditional** | ~~83 undated; 44 at ~1.1 km; 332 year-only; 2020–2023 missing~~ → **408 usable point labels, 60 records outside them; 92% of labels are 2018; 2020–2023 missing** (see §11.8) |
| Roads / rivers | Yes | Fair | Proxies, uneven completeness |

**Nothing in this report is a model result.** No performance metric has been produced and none should be quoted
until a model is trained and spatially validated.

---

## 11. Phase 3 corrections and additions

*Added 2026-10-26. Phase 3 built the analysis grid, transformed every layer onto it, and audited
the result. Nine statements in §1–§10 did not survive that audit. Superseded text above is struck
through and points here. Method and per-layer audit: `docs/PREPROCESSING_REPORT.md`. Verdicts:
`docs/DATA_READINESS_REPORT.md`. Every value below is read from a machine-readable validation file
under `data/processed/`, not restated from memory.*

### 11.1 District elevation range is 117–2,230 m, not 165–1,849 m

| Statistic | Value (district, full raster) |
|---|---|
| Pixels | 2,356,538 |
| Minimum | **116.96 m** |
| p01 | 501.75 m |
| Median | 803.83 m |
| Mean | 854.59 m |
| p99 | 1,606.06 m |
| Maximum | **2,230.27 m** |
| Std | 179.89 m |

The Phase 1 range came from **2,085 random sample points** inside the polygon. A random sample of
0.09 % of 2.36 M pixels cannot be expected to hit the extremes: only **0.196 %** of the district
lies below 300 m and **0.065 %** above 2,000 m, so the true minimum and maximum sit in tails a
sample almost never reaches. The low values are narrow southern valleys where the GADM outline
descends the Western Ghats escarpment. SRTM independently records them and the cross-DEM
difference at those nodes is not anomalous, so they are treated as real terrain — but they are
not representative, and they carry the district's extreme slope values (max 67.77°).

The SRTM figure in the §1 row (158–1,856 m) came from the same sample and is superseded in the
same way; the exhaustive comparison in §11.2 is its replacement evidence.

**Consequence:** any elevation threshold or class break derived from 165–1,849 m is wrong at both
ends. Slope, aspect and curvature are unaffected outside those tails.

*Evidence:* `data/processed/dem/dem_validation.json` → `dem_district_stats`, `elevation_range_note`.

### 11.2 Cross-DEM agreement: same centre, much heavier tail

| Metric | Phase 1 (2,085 random points) | Phase 3 (every shared node) |
|---|---|---|
| n | 2,085 | **2,280,319** |
| Mean difference (Coper. − SRTM) | −1.44 m | −1.27 m |
| MAD | 3.41 m | **3.42 m** |
| p95 absolute difference | 8.50 m | 8.74 m |
| Max absolute difference | 54.9 m | **147.03 m** |
| Nodes differing by > 50 m | 1 | **447** (0.020 %) |
| Pearson r | 0.9997 | 0.9997 |

The central agreement reproduces to 0.01 m. That is the useful part, and it is what licenses the
claim that the Skadi mirror is a faithful copy of SRTM 1″ rather than a resampled product.

The tail does **not** reproduce, and could not: 447 of 2.28 M pixels is 0.020 %, so a 2,085-point
sample expects 0.4 such nodes. The large differences cluster on steep southern faces where the
2000 radar surface and the 2021 surface genuinely differ. The Phase 1 sentence "one point above
50 m" therefore understated the disagreement by a factor of ~450 and made a systematic
steep-face effect look like a single outlier.

Same algorithm, two independent DEMs: slope mean **11.53°** (GLO-30) vs **10.69°** (SRTM),
MAD **2.24°**, p95 5.96°, r 0.943. That is the honest uncertainty band on the slope covariate —
disagreement between products, not error against truth, since both can share a bias.

*Evidence:* `dem_validation.json` → `cross_dem`, `cross_dem_slope`.

### 11.3 The DEM files are point-registered and already co-registered

| File | Shape | Stored x origin | First sample | Last sample |
|---|---|---|---|---|
| Copernicus E075 | 3600 × 3600 | 74.999861 | 74.999861 | 75.999583 |
| Copernicus E076 | 3600 × 3600 | 75.999861 | 75.999861 | 76.999583 |
| SRTM E075 `.hgt` | 3601 × 3601 | 74.999861 | 74.999861 | 75.999861 |
| SRTM E076 `.hgt` | 3601 × 3601 | 75.999861 | 75.999861 | 76.999861 |

All four are tagged `AREA_OR_POINT=Point`, have pixel size exactly 1/3600°, the same stored *y*
origin (12.000139) and *x* origins exactly 1° apart. **The mosaic of the two Copernicus tiles needs
no resampling:** E075's last centre (75.999583) and E076's first (75.999861) are exactly one
1/3600° step apart — contiguous, no gap, no duplicated sample. The `.hgt` mirror **does** repeat
the tile-edge node (E075's index-3600 sample is at 75.999861, the same coordinate as E076's first),
so an `.hgt` mosaic must drop **one duplicated column per join plus the outer southern edge row**
(3601 → 3600). That is asserted in code, not assumed.

Matching tags are not proof of matching ground samples, so the alignment was measured: SRTM was
resampled at offsets of −1.0 to +1.0 pixel in both axes and its MAD against Copernicus compared
over 325,760 district samples.

| Offset (px) | MAD (m) | Offset (px) | MAD (m) |
|---|---|---|---|
| **0, 0** | **3.42** | 0, ±0.5 | 3.95 / 4.26 |
| ±0.5, 0 | 3.82 / 4.07 | 0, ±1.0 | 5.42 / 5.87 |
| ±1.0, 0 | 5.02 / 5.43 | −0.5, −0.5 | 4.22 |

The minimum is exactly at zero and the MAD rises in every direction. A half-pixel
misregistration would cost ~+0.4 m MAD and a whole-pixel shift ~+1.6 m, so the test is sensitive
enough to detect the error it was looking for. **No half-pixel correction is applied, because none
is needed.**

What this proves: the two products are co-registered relative to each other as stored, so
cross-DEM comparison and mixing are on one lattice. What it does not prove: absolute geolocation.
That rests on the four town checks, which are only sensitive to ~50 m.

This supersedes the caution that GeoTIFF DEMs are area-registered while `.hgt` is point-registered.
Both are tagged `Point` here, so the stated dichotomy does not describe these files. `AGENTS.md`
has been amended.

*Evidence:* `dem_validation.json` → `same_node_grid`, `srtm_extra_edge_nodes`, `registration_shift_test`.

### 11.4 A 0.36 % area agreement hides ~750 m of outline disagreement

Both outlines were sampled every 50 m and the separation measured:

| Metric | GADM edge → OSM | OSM edge → GADM |
|---|---|---|
| Samples | 5,187 | 5,560 |
| Median separation | **744.1 m** | **770.7 m** |
| p90 | 1,078.2 m | 1,148.2 m |
| p99 | 1,319.0 m | 1,390.3 m |
| Maximum | 1,462.3 m | 1,578.6 m |
| Within 100 m | 4.78 % | 4.57 % |
| Within 500 m | 29.05 % | 28.17 % |

The symmetric difference is **8.75 % of the district** — 89.05 km² present only in GADM and
96.6 km² only in OSM. The largest single patches are 42.18 km² around 75.956 E / 11.559 N
(GADM-only) and **56.56 km²** around 76.120 E / 11.849 N (OSM-only).

Two polygons can enclose almost the same area while differing along nearly their whole boundary.
The 0.36 % area figure in §6 therefore says nothing about positional agreement, and the earlier
sentence "agree closely enough to be used interchangeably for acquisition and rough clipping"
must be read with this in mind: interchangeable for area totals, **not** for deciding whether a
point 500 m from the GADM edge is in Wayanad.

**Consequence.** A ±0.75 km band around the district edge is boundary-ambiguous, and
disagreements reach 1.6 km. Of the 23 inventory records outside GADM, **4 fall inside OSM**
(212–648 m outside GADM, 221–828 m inside OSM) — all KER2018. They were **not** reclassified and
not promoted to point labels, because relabelling them would silently change published record
counts. Ten records carry `review_boundary_uncertain`, spanning 212.3–2,836.1 m outside GADM.
Nine of those are inside the 1.6 km disagreement envelope; the tenth, `14115/p140/row15` at
2,836 m, is **not** explained by the boundary choice at all — it inherits a Phase 2 review flag
and is deliberately left unresolved rather than quietly relabelled or dropped.

*Evidence:* `data/processed/grid/boundary_diagnostics.json`,
`data/processed/inventory/inventory_spatial_suitability.csv`.

### 11.5 The Phase 1 geology clip is a bounding box, not a district layer

`glim_wayanad_clip.gpkg` is a **bbox clip** (district bbox + 0.05° pad) holding **29 polygons**, of
which only **16 intersect** the district. The other 13 belong to Malappuram, Kozhikode and
Karnataka. Treating that file as a district layer would have put neighbouring districts' geology
inside Wayanad. It is kept unmodified; Phase 3 writes a proper intersection alongside it:
16 polygons, 5 classes, 2,121.0 km² = **100.0 %** of GADM, 0 invalid or empty geometries.

The native CRS is `ESRI:54012` (World Eckert IV). `EPSG:54012` **does not exist** —
`pyproj.CRS.from_epsg(54012)` raises `CRSError` — so the identifier must be read from the file.

| GLiM code | Meaning | Area (km²) | Share |
|---|---|---|---|
| `mtam__` | Metamorphic, amphibolite facies | 1,226.1 | 57.81 % |
| `pa____` | Plutonic, acidic | 561.0 | 26.45 % |
| `mt____` | Metamorphic, undifferentiated | 266.6 | 12.57 % |
| `pb____` | Plutonic, basic | 66.7 | 3.14 % |
| `pa__mt` | Plutonic acidic with metamorphic overprint | 0.6 | 0.03 % |

**Local usefulness was tested, not assumed.** 45 inventory records carry GSI field lithology; 43
fall inside a GLiM polygon. The 39 described as charnockite–gneiss split **22 / 14 / 1** across
plutonic-acidic, metamorphic-amphibolite and plutonic-basic (2 fall outside any polygon). One rock
population, three GLiM classes: the layer cannot resolve local lithology. Median distance from a
site to the nearest class boundary is **1,063 m** (p90 4,623 m, min 8 m); mean polygon area
132.6 km²; source scale 1:3.75 M.

*Evidence:* `data/processed/geology/geology_validation.json`, `glim_lithology_shares.csv`,
`site_lithology_vs_glim.csv`.

### 11.6 Soil: raw 0 is an undeclared nodata mask, and all 14 masks agree

§5 said the zeros "may be genuine or may be masked" and flagged them for inspection. Inspected:
every one of the 14 rasters contains exactly **8,312** zero cells, and the zero footprints are
**identical across all 14 independent properties** (min = max = 8,312 per file; 8,312 cells where
any file is zero, 8,312 where all are). 8,262 of those lie outside the district — the shape of the
acquisition crop — leaving **50 cells (3.1 km², 0.15 % of the district)**.

That coincidence across 14 unrelated soil properties is conclusive: a genuine clay = 0 % and a
genuine bdod = 0 g/cm³ would not share a mask, and bdod = 0 is physically impossible. So **raw 0
is treated as nodata for all 14 rasters**. The cost is explicit: a genuine cfvo = 0 % cannot be
distinguished from a masked cell and is discarded rather than guessed. Resulting nodata on the
study grid: **3,657 pixels = 0.155 %**.

Two further checks were added. Texture closure — clay + sand + silt = **100.0 %** (median 100.0,
p05 99.94, p95 100.06, 100 % of 2,352,881 cells within 1 pp) — proves the ×10 conversion factors
are all correct, since the identity breaks if any one divisor is wrong. And no value falls outside
a plausible physical range in any property at either depth.

*Evidence:* `data/processed/soil/soil_validation.json` → `checks`, `nodata_decision`,
`texture_closure`; `soil_properties.csv`.

### 11.7 `GSI_PDLS/p95` precision was overstated ~100×

The Phase 2 table stored `coord_precision_deg = 2.778 × 10⁻⁶` (0.01 arc-second; it displays
as 0.000003) for the 2024 Mundakkai
record. The source prints whole-second DMS (`11027'46"N / 76008'03"E`), which supports 1
arc-second = **0.000278°**, a factor of 100. Using the stored value, the coordinate radius came
out at 0.15 m, and the 10 m accuracy floor hid the defect entirely; the corrected radius is
**15.47 m**, giving a modelled uncertainty of **15.5 m**. Still precision class A, so no label
changes — but the earlier number was not supportable.

The correction is applied in `inventory_spatial_suitability.csv`
(`coord_precision_deg_verified`, `precision_correction_note`) and the Phase 2 CSV is left
untouched so published figures stay reproducible. A first version of the Phase 3 script keyed the
correction on the Phase 2 working label (`GSI_PDLS/p95`) rather than the actual
`source_record_id`, so it reported the correction in the summary while applying it to **no row**.
That was caught by adding an assertion that every correction key matches exactly one record; the
assertion now fails the build if a correction silently becomes a no-op.

*Evidence:* `inventory_suitability_summary.json` → `precision_corrections`;
`inventory_spatial_suitability.csv` (the corrected row).

### 11.8 The "44 two-decimal records" are 44 records, not 44 events — and none is a point label

The 44 are **35 undated GSI 14337 site rows + 9 NASA GLC rows**, and 7 of the 9 GLC rows are
outside the district. Only **2 are dated in-window**, and of those:

- `GLC/101`, locality "Wayanad" — a **district centroid**, not a site (`exclude_district_centroid`);
- `GLC/10011`, "Highway 766" — usable only with a widened label (`review_widen_label`).

The 44 split as 36 `review_widen_label`, 7 `exclude_not_in_district`, 1
`exclude_district_centroid`. **Zero are `point_label_ok`.** Reporting "44 events with ~1.1 km
coordinates" was wrong in both numerator and interpretation.

The structure of the 2-decimal population matters as much as its size:

- The 35 GSI 14337 rows occupy only **28 unique coordinates**; 12 rows share a coordinate with
  another row. They are village-level site descriptions, not 35 distinct points.
- The 33 accepted 14337 → 14115 crosswalk pairs (≤ 1.5 km) map onto only **26 distinct 14115
  sites**. Two pairs were rejected at **7,428.8 m** and **16,579.0 m** — a 2-decimal village
  centroid cannot be resolved to a specific site at those distances. The 33 accepted rows are
  therefore not 33 new locations.

The usable-label population is therefore **408 = 364 in-window + 38 undated sites + 6 pre-2000**,
from 371 event groups (363 with a usable label). Undated and pre-2000 records are usable as *site
evidence* — this slope has failed — never as dated events.

*Evidence:* `inventory_suitability_summary.json` → `two_decimal_records`,
`crosswalk_resolution`, `event_groups`; `event_group_point_status.csv`.

### 11.9 A 10 m cell is 83.75 m², not 100 m²

At 11.5 N one 10 m cell measures **83.75 m²** on the ellipsoid, not 100 m². Counting the WorldCover
district window with a flat 100 m² assumption would report **2,533.7 km²** — **19.4 % too large**.
The geodesic row-wise area gives **2,121.9 km²**, which agrees with the GADM polygon (2,121.0 km²)
to 0.04 % and independently confirms both the tile and the mask. The 30 m mask — pixel-centre
rasterisation at 900 m² per UTM cell — gives 2,120.9 km², 0.005 % below the polygon.

This is why the land-cover class shares in §2.2 were computed on geodesic pixel area rather than
pixel counts: at this latitude a raw pixel count overstates area by 19.4 %, and although that
factor varies only ~0.2 % between the north and south of the district, class comparisons should be
area-weighted rather than counted.

*Evidence:* `landcover_validation.json` → `native_area`; `grid_spec.json` →
`district_mask_area_km2`, `district_mask_area_10m_km2`.

### 11.10 Net effect on the fitness summary

| Dataset | What changed | Does the fitness judgement change? |
|---|---|---|
| DEM | Range corrected to 117–2,230 m; tail of cross-DEM disagreement quantified | No — still **Good**, with DSM/canopy caveat and ±2.2° slope uncertainty |
| Land cover | True cell area and class shares recomputed on geodesic area | No — still **Fair**; built-up loss now quantified (−17 % relative) |
| Rainfall | 312/312 files verified, series complete, no −9999 inside the district | No — still **Fair** (monthly, 5.5 km, no trigger) |
| Geology | Phase 1 clip found to be a bbox clip; district layer built; resolution limit measured | No — still **Poor**, now with evidence (22/14/1 split) |
| Soil | Zero → nodata resolved by identical-footprint test; factors proven by closure | No — still **Fair**; 0.155 % nodata, 250 m effective |
| Boundary | ~750 m median outline disagreement quantified | Slightly worse than stated — **Good for area, ambiguous within ±0.75 km of the edge** |
| Inventory | 408 usable labels, not 468 records; 0 of the 44 two-decimal records usable as points; 92 % of labels are 2018 | Still **Conditional**, with a sharper statement of *why* |
| Roads / rivers | Clip completeness measured (0 roads lost, 40/1,298 rivers truncated) | No — still **Fair** as proxies |

No dataset improved to unconditional fitness, and none was rejected. What changed is that every
caveat is now a measured number rather than an expectation.

Phase 3 therefore concludes: **preprocessing is complete and every predictor is usable at its
stated resolution**, but **modelling is not permitted yet**. Two decisions gate it, and neither can
be resolved from the data on disk: how "not a landslide" is represented (no absence or background
sample exists), and whether the target is 2018-conditioned or general susceptibility (92 % of
labels are 2018). See `docs/DATA_READINESS_REPORT.md` §4.
