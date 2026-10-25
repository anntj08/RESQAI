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
| Elevation range in district | 165–1,849 m | 158–1,856 m |
| Voids | none flagged | 0 cells equal to −32768 |
| Registration | — | agrees with Copernicus, r = 0.9997 |

**Cross-DEM agreement:** 2,085 random points inside the district, all valid.
Mean difference (Copernicus − SRTM) = −1.44 m, MAD = 3.41 m, p95|Δ| = 8.50 m, max |Δ| = 54.9 m,
one point above 50 m. This is the expected signature of two independent 30 m DEMs over steep terrain, and it
also confirms the Skadi mirror is a faithful SRTM 1" copy rather than a resampled lower-resolution product.

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
| `mt` / `mtam__` | Metamorphic (amphibolite-facies) | 57.81% |
| `pa` / `pa____` | Plutonic, acidic (granitoid/charnockite family) | 26.45% |
| `mt` / `mt____` | Metamorphic, undifferentiated | 12.57% |
| `pb` / `pb____` | Plutonic, basic | 3.14% |
| `pa` / `pa__mt` | Plutonic acidic with metamorphic overprint | 0.03% |

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
| Agreement | — | 0.36% area difference |

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
   Every layer except land cover must be upsampled to a common grid; the choice of 30 m as the working grid is
   defensible but must be stated, and categorical layers must use nearest-neighbour, never bilinear.
2. **CRS:** all acquired layers are EPSG:4326 except GLiM (Eckert IV, already reprojected for the clip).
   A metric CRS (UTM 43N, EPSG:32643) is required for slope, distance and area calculations.
3. **NoData conventions differ:** −9999 (CHIRPS, undeclared), 0 (WorldCover class nodata), −32768 (SRTM HGT),
   absent (Copernicus, SoilGrids). A single harmonisation rule is needed before any stack is built.
4. **Registration:** SRTM HGT point-registered vs GeoTIFF area-registered — half-pixel shift if mixed naively.
5. **Spatial autocorrelation:** 371 in-window event groups in 2,121 km², but 339 are the 2018 monsoon and
   332 resolve only to a year. The *independent* time spread is much smaller than the record count suggests.
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
| Inventory (GSI + KER2018 + literature) | Yes | **Conditional** | 83 undated; 44 at ~1.1 km; 332 year-only; 2020–2023 missing |
| Roads / rivers | Yes | Fair | Proxies, uneven completeness |

**Nothing in this report is a model result.** No performance metric has been produced and none should be quoted
until a model is trained and spatially validated.
