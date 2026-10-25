# Inventory Verification Report — Wayanad landslide records 2000–2026

**Phase:** 2 (acquisition-gap recovery and inventory verification)
**Date:** 2026-10-25
**Base commit:** `b148ad7`
**Products:** `data/processed/inventory/*.csv`, `data/interim/inventory_extracts/*.csv`
**Reproduce with:** `python scripts/build_consolidated_inventory.py && python scripts/assemble_inventory.py`

> **Scope limit, stated up front.** This report verifies *records*, not landslides.
> Every statement below is about a source row and what that source says. No field
> campaign was conducted, no satellite footprint was digitised and no accuracy figure
> is reported. Nothing here estimates *when* a slope will fail; susceptibility work has
> not begun and must not be inferred from this document.

---

## 1. Counting rules

These are stated first because the headline numbers are meaningless without them, and
because two of these counts are frequently conflated in landslide-database work.

| Term | Definition used here |
|---|---|
| **Source record** | One row in one source dataset. Two sources describing the same physical landslide are **two source records**. |
| **Dated record** | A source record whose own text states a year, month or day. |
| **Undated site record** | A source record that places a landslide *site* but states no date. Never counted as an event. |
| **Event group** | A set of source records judged to describe one physical landslide, on explicit recorded evidence. Only dated records receive a group. |
| **In-window** | Event date 2000-01-01 to 2026-12-31. |
| **Included** | Passed the GADM boundary check *and* not assigned to another district. |

**Source records ≠ events.** 468 source records do not mean 468 landslides. The
2018 inventory alone contributes 331 mapped points for one monsoon season, and 35 GSI
14337 rows repeat the same investigation sites as GSI 14115 at coarser precision.

---

## 2. Source-record counts

**468 source records from 8 sources.**

| Source | Records | Dated | Undated | In-window included | Attribution |
|---|---:|---:|---:|---:|---|
| `KER2018` Hao/van Westen 2018 Kerala inventory | 331 | 331 | 0 | 331 | composite (NRSC + GSI + new mapping) |
| `GSI14768` 1:50,000 susceptibility, Mananthavady–Kalpetta–S.Bathery | 46 | 0 | 46 | 0 | GSI field survey, undated |
| `GSI14115` Landslide Inventory of Kerala (FS 2007-2010) | 35 | 33 | 2 | 27 | GSI field investigation |
| `GSI14337` hazard zonation, Kasaragod/Kannur/Wayanad | 35 | 0 | 35 | 0 | GSI field survey, undated |
| `NASA_GLC` Global Landslide Catalog | 9 | 9 | 0 | 2 | secondary, media-derived |
| `GSI2018` June-2018 Wayanad post-disaster note | 8 | 8 | 0 | 8 | GSI field investigation |
| `GSI_PDLS` 2024 and 2025 post-disaster volumes | 2 | 2 | 0 | 2 | GSI field investigation |
| `LIT2025` Sreekumar et al. 2025 Table 1 | 2 | 2 | 0 | 2 | peer-reviewed compilation |

Totals: **385 dated** (379 in-window, 6 pre-2000) and **83 undated site records**.

The 83 undated records are not failures. GSI 14337 and 14768 record *where* terrain has
failed without recording *when*; converting them into events would require inventing
dates. They are retained as site evidence for the later susceptibility work and are
excluded from every event count.

---

## 3. Per-record verification status

Each of the 468 records carries exactly one status.

| Status | Count | Applied to |
|---|---:|---|
| `SOURCE_CONFIRMED` | 451 | A primary investigation record (GSI field survey, or the CC-BY 2018 shapefile) that states the locality and the date. |
| `NOT_APPLICABLE` | 12 | Boundary check placed the record outside Wayanad, so no Wayanad claim is made. |
| `SECONDARY_SOURCE_ONLY` | 3 | Only a compilation reports the event; no primary record obtained. |
| `NEEDS_REVIEW` | 1 | Coordinate fails a documented internal-consistency test. |
| `CORROBORATED` | 1 | Two independent sources agree on locality, date **and** location within 500 m. |

### The four records that are not simply confirmed

**`NEEDS_REVIEW` — GSI 14115 row 17, "Karimani, Valamkode", 2007-06-29.**
The printed longitude is `76°56'58"E`. That places the site roughly 77 km east of the
district, in Tamil Nadu. The value is retained exactly as printed and flagged; it has
**not** been "corrected" to `75°56'58"E` even though that is the obvious typographic
candidate. Correcting it silently would manufacture a coordinate the source never
published. Consequence: this record must be dropped from any distance- or
slope-based analysis until the printed page is re-examined against a survey sheet.

**`SECONDARY_SOURCE_ONLY` × 3.**
- Puthumala, Kalladi, Vythiri, 2019-08-08 (`LIT2025`). GSI's 2019-20 Wayanad
  post-disaster report — cited in GSI's own 2025 bibliography — is **absent from the
  public index** (see gap G1 in `SOURCE_DISCOVERY_REPORT.md`). Nothing primary is
  reachable, so the event is real but its record is second-hand.
- NASA GLC/101, 2007-06-25 — district-level coordinate only.
- NASA GLC/10011, Highway 766, 2017-06-27 — a road-blocking event known only from the
  catalogue.

**`CORROBORATED` — Mundakkai-Chooralmala, 2024-07-30 (`LIT2025`).** Section 6 gives the
measurements.

---

## 4. Coordinate precision

Precision is reported as printed by each source, never rounded up. The stored
`coord_precision_deg` is the angular resolution the source actually supports.

| Source | Printed precision | Approx. ground resolution | Records |
|---|---|---:|---:|
| `GSI14115` | DMS, whole or decimal seconds | 0.3–31 m | 35 |
| `GSI_PDLS` | DMS whole second | ~31 m | 2 |
| `LIT2025` | DMS whole second | ~31 m | 2 |
| `KER2018` | decimal degrees, 5 dp | ~1 m (file precision) | 331 |
| `GSI2018` | decimal degrees, 4 dp | ~11 m | 8 |
| `GSI14768` | decimal degrees, 4–3 dp | 11–111 m | 46 |
| `GSI14337` | decimal degrees, **2 dp** | **~1.1 km** | 35 |
| `NASA_GLC` | decimal degrees, 2 dp | ~1.1 km | 9 |

Two things follow and both are load-bearing for later phases:

1. **44 of 468 records (GSI 14337 + NASA GLC) carry no usable site coordinate.** At two
   decimal places the point is a village centroid, not a landslide. Treating these as
   inventory points would inject ~1.1 km of positional error into any distance-to-ridge
   or slope statistic.
2. **The KER2018 5-dp values are file precision, not survey precision.** The shapefile
   stores many digits but its mapped positions are only as good as the source mapping
   behind each polygon. The stored precision must not be read as accuracy.

### Precision improvement achieved

GSI 14337's 35 two-decimal rows appear to duplicate GSI 14115's arc-second rows. The
crosswalk measures this rather than assuming it (Section 5). Where a match holds, the
14115 coordinate supersedes the 14337 coordinate for spatial use, which upgrades that
site from ~1.1 km to sub-30 m. This is the single largest coordinate-precision gain in
the phase and it required no new download — only parsing a report already on disk.

---

## 5. Duplicate reconciliation

`data/processed/inventory/duplicate_crosswalk.csv` holds **45 candidate pairs**. Every
pair carries the measured separation, the basis for comparing them, a decision and a
confidence. Confidence is derived from evidence, not asserted: separation sets a
baseline, and agreement on the stated date raises it.

| Pair | Pairs | Separation | Decision |
|---|---:|---|---|
| GSI 14337 → GSI 14115 | 35 | min 127 m, **median 471 m**, max 16,579 m | Same GSI investigation site; 14115 coordinate supersedes |
| GSI 2018 → KER2018 | 8 | 361–1,453 m, median 793 m | Same monsoon cluster, **no confirmed duplicate** |
| GSI PDLS 2024 → LIT2025 | 1 | **495 m**, same stated date | **Same event** — merged into one group |
| NASA GLC 2007 → GSI 14115 | 1 | 12,708 m | No match |

**GSI 14337 → GSI 14115: 33 of 35 rows are within 1,500 m**, against a 1.1 km rounding
uncertainty on the 14337 side. 7 pairs are within 300 m. The 2 outliers are the
impossible-longitude row (16,579 m, Section 3) and one border site. This is strong
evidence that the two GSI products describe the same 35 sites, and it is why the 14337
coordinate is subordinated rather than deleted.

**GSI 2018 → KER2018: zero duplicates confirmed.** The eight 42-point datasheets sit
361–1,453 m from the nearest mapped 2018 point. At that separation, on a hillslope with
kilometre-scale debris flows, coincidence cannot be distinguished from adjacency. They
are therefore kept as **separate events** and flagged as *candidate* duplicates in the
crosswalk. Merging them on proximity alone would be exactly the mistake the brief
prohibits.

**A nearest-neighbour match is not a duplicate proof.** Several 2018 slides map to the
same nearest KER2018 point while being 700–1,450 m from each other. The crosswalk
records this as "candidate only"; it does not collapse the records.

---

## 6. July 2024: the coordinate question, resolved

The central verification question of this phase was whether GSI's published coordinate
for the 30 July 2024 Mundakkai-Chooralmala landslide is a transcription error.

| Point | Latitude, Longitude | Source |
|---|---|---|
| GSI 2024 first information report | 11.462778, 76.134167 | GSI PDLS 2024, p.95 |
| Independent publication | 11.466944, 76.135833 | Sreekumar et al. 2025, Table 1 |
| Mundakkai village (settlement) | 11.470171, 76.150676 | OSM/Nominatim |
| Chooralmala village (settlement) | 11.499232, 76.159871 | OSM/Nominatim |

Measured separations (EPSG:32643):

| From → To | Distance |
|---|---:|
| GSI → independent publication | **495 m** |
| GSI → Chooralmala settlement | **4.91 km** |
| GSI → Mundakkai village | **1.98 km** |
| Independent publication → Chooralmala | 4.43 km |
| Independent publication → Mundakkai | 1.66 km |

**Verdict: `CORROBORATED`. The coordinate is a genuine source-area location, not an
error.** Three independent lines support this:

1. Two unrelated sources agree to within 495 m — smaller than the runout of the event
   (≈7 km) by more than an order of magnitude, so they are locating the same feature.
2. KSDMA's Memorandum describes the crown as "approximately 3 km from Mundakkai and
   5 km from Chooralmala villages". GSI's point sits **1.98 km from Mundakkai and
   4.91 km from Chooralmala** — consistent with the stated geography, not displaced by
   10 km as a digit transposition would be.
3. The point lies upslope in the source area, which is what a 42-point datasheet records.

The Wikipedia infobox coordinate remains **unusable** and is not used anywhere.

### Event facts recorded from primary government documents

| Fact | Value | Source |
|---|---|---|
| Failure time | ~01:15 on 2024-07-30 | KSDMA Memorandum 17082024 |
| Location | Punchiri Mattam Hill, Meppadi GP, Vythiri Taluk | KSDMA Memorandum |
| Rainfall, Kalladi | 200.2 mm (29-07), 372.6 mm (30-07) | KSDMA Memorandum |
| Source elevation | 1544 m | KSDMA Memorandum |
| Runout | ~7 km | GSI PDLS 2024 |
| Movement | Debris flow, extremely rapid, retrogressive, multiple lobes | GSI PDLS 2024 |
| Deaths | ~107 as at 17:30 30-07-2024 (interim) | GSI PDLS 2024 |
| Deaths | ~336 dead, 78 missing (later) | Sreekumar et al. 2025 |

The two fatality figures are **not** a contradiction to be averaged: they are the same
disaster counted at different times. Both are recorded with their as-at dates.

**Second 2024 event.** The 2025 GSI volume's only Wayanad record is `KER/WYD/58A03/2025/01`,
Meenakshi Bridge — a 90 m² road-cut rotational slide whose declared history dates it to
**June 2024**, reported 21.05.2025. It is grouped as a 2024 event, not a 2025 event. This
is why the 2025 row of the coverage table is zero despite a "2025" report existing.

---

## 7. Year-by-year coverage, 2000–2026

Included records only. `distinct_event_groups` is the event-level count; the record count
is higher wherever several sources describe one landslide.

| Year | Records | Event groups | Verified | Unresolved | Secondary-only | Best date precision |
|---:|---:|---:|---:|---:|---:|---|
| 2000 | 0 | 0 | 0 | 0 | 0 | — |
| 2001 | 0 | 0 | 0 | 0 | 0 | — |
| 2002 | 0 | 0 | 0 | 0 | 0 | — |
| 2003 | 0 | 0 | 0 | 0 | 0 | — |
| 2004 | 0 | 0 | 0 | 0 | 0 | — |
| 2005 | 0 | 0 | 0 | 0 | 0 | — |
| 2006 | 2 | 2 | 2 | 0 | 0 | day |
| 2007 | 18 | 18 | 16 | 1 | 1 | day |
| 2008 | 1 | 1 | 1 | 0 | 0 | year |
| 2009 | 7 | 7 | 7 | 0 | 0 | day |
| 2010 | 0 | 0 | 0 | 0 | 0 | — |
| 2011 | 0 | 0 | 0 | 0 | 0 | — |
| 2012 | 0 | 0 | 0 | 0 | 0 | — |
| 2013 | 0 | 0 | 0 | 0 | 0 | — |
| 2014 | 0 | 0 | 0 | 0 | 0 | — |
| 2015 | 0 | 0 | 0 | 0 | 0 | — |
| 2016 | 0 | 0 | 0 | 0 | 0 | — |
| 2017 | 1 | 1 | 0 | 0 | 1 | day |
| 2018 | 339 | 339 | 339 | 0 | 0 | day |
| 2019 | 1 | 1 | 0 | 0 | 1 | day |
| 2020 | 0 | 0 | 0 | 0 | 0 | — |
| 2021 | 0 | 0 | 0 | 0 | 0 | — |
| 2022 | 0 | 0 | 0 | 0 | 0 | — |
| 2023 | 0 | 0 | 0 | 0 | 0 | — |
| 2024 | 3 | 2 | 3 | 0 | 0 | day |
| 2025 | 0 | 0 | 0 | 0 | 0 | — |
| 2026 | 0 | 0 | 0 | 0 | 0 | — |
| **Total** | **372** | **371** | **368** | **1** | **3** | |

### Date precision across the 372 in-window records

| Precision stated by source | Records |
|---|---:|
| Year only | 332 |
| Day | 30 |
| Month | 8 |
| Multi-event (source names two dates at one site) | 2 |

**332 of 372 records resolve only to a year**, almost entirely because the 2018 inventory
records a season rather than per-event dates. That is a property of the source, not a
defect introduced here.

### Reading the zeros correctly

Nineteen of twenty-seven years are empty. **This is an observation gap, not evidence that
no landslides occurred.** The zeros cluster where the source landscape has no coverage:

- **2000–2005, 2010–2016, 2020–2023** — no GSI post-disaster volume exists for these
  years in the public index, and no other found source records them.
- **2025** — the "2025" GSI report exists but its Wayanad record is a June 2024 event.
- **2026** — the year is incomplete at execution time (2026-10-25).

Two structural facts explain most of the shape: the 2018 monsoon dominates because a
statewide mapped inventory exists for it, and 2006–2009 dominates the pre-2018 period
because GSI 14115 happened to survey Wayanad in that field season.

### Multi-event records

Three GSI 14115 rows name two failures at one site. The in-window occurrence is used for
year coverage; the earlier occurrence is preserved in `date_text` and never discarded.

| Record | Site | Dates | Used for coverage |
|---|---|---|---|
| 14115 Sl.3 | Kattunaicken Colony | 1982 & June 2007 | 2007-06 |
| 14115 Sl.6 | Aakollikunnu | 1988 & July 2007 | 2007-07 |
| 14115 Sl.8 | Pullinjal Survey no.622/1A | 1991-06-19 & 1991-07-01 | pre-2000, outside window |

---

## 8. Boundary decisions

Point-in-polygon against GADM 4.1 Wayanad (the working boundary). GADM area measured in
EPSG:32643 is **2,121.0 km²**, matching the published figure.

| Decision | Count | Meaning |
|---|---:|---|
| `INCLUDED` | 445 | Inside the polygon; no qualification |
| `INCLUDED_BOUNDARY_REVIEW` | 10 | Outside the polygon by **< 5 km**; flagged `review_before_spatial_use` |
| `EXCLUDED_OUT_OF_DISTRICT` | 12 | Outside the polygon by ≥ 5 km, or a named other district |
| `INCLUDED_FLAGGED` | 1 | Impossible printed coordinate; retained as published |

### Why the rule is a measured distance, not a judgement

23 of 468 points fall outside the polygon. Treating them as one group would have been
wrong at both ends of the range:

- **212 m outside** (KER2018/No.2303) is a boundary-generalisation artefact. GADM's
  outline is simplified; discarding a mapped landslide for a 200 m gap would lose real data.
- **17.4 km outside** (GSI 14768, Vazhikkadavu) is a different district. The 14768 report
  is titled for the "Mananthavady–Kalpetta–Sulthan Bathery–**Vazhikkadavu**" corridor,
  which extends west beyond Wayanad. Vazhikkadavu is a Malappuram-district locality.

The split is therefore made at 5 km, a threshold comfortably outside GADM's
generalisation error and comfortably inside a wrong-district displacement. The measured
distance is written into every outside record as `dist_outside_boundary_m`.

### The 12 exclusions

| Records | Locality | Distance outside | Basis |
|---:|---|---:|---|
| 5 | Vazhikkadavu (GSI 14768 Table 4, Sl.25–29) | 17.1–17.4 km | Beyond the report's Wayanad coverage; Malappuram district |
| 1 | GLC/100 Kozhikode | 32.7 km | Named other district |
| 1 | GLC/5200 Nilgiris, Tamil Nadu | 38.5 km | Named other state |
| 1 | GLC/1213 Puddipadi, Kozhikode | 3.4 km | Named other district |
| 1 | GLC/1212 Balussery, Kozhikode | 17.9 km | Named other district |
| 1 | GLC/4984 Gudalur, Nilgiris | 15.7 km | Named other state |
| 1 | GLC/1172 Nilambur, Malappuram | 21.4 km | Named other district |
| 1 | GLC/4468 Pulloorampara, Kozhikode | 9.5 km | Named other district |

The seven GLC exclusions are a **correction of a query artefact**: the Global Landslide
Catalog was queried on a bounding box, which necessarily returns neighbouring districts.
Excluding them is not a data-quality judgement about the catalogue.

The five GSI 14768 records were previously carried as `INCLUDED_BOUNDARY_REVIEW`. The
measured distance showed that was too generous, so they were reclassified. All five are
undated site records, so **no event or year count changed** as a result.

### The 10 retained-but-flagged records

| Records | Locality | Distance outside |
|---:|---|---:|
| 1 | KER2018/No.2303 | 212 m |
| 3 | KER2018/No.2198, 2261, 2262 | 568–648 m |
| 1 | GSI 14768 Table 4 Sl.1 Muppankuzhi Pudupadi | 672 m |
| 4 | GSI 14768 Table 5 Sl.13–16 Moopankuzhi / Valliyad | 710–1,112 m |
| 1 | GSI 14115 Sl.15 Thachankolli colony | 2,836 m |

Thachankolli colony is the one genuinely ambiguous case: 2.8 km outside, which is too far
to dismiss as generalisation and too close to assert a different district without a
gazetteer check. It is kept, flagged, and excluded from spatial use until checked.

**No coordinate was snapped, moved or deleted to make a boundary test pass.**

---

## 9. Geology status

| Requirement | Status |
|---|---|
| Vector lithology for Wayanad | **GLiM 1:3.75 M only** — effective detail ~4 km |
| GSI 1:50,000 geology as vector | **NOT OBTAINED** — Bhukosh unreachable, REST token-gated |
| GSI 1:50,000 geology as raster plates | **ON DISK** inside `gsi_14767`, `gsi_14768`, `gsi_14999` PDFs |
| Per-record lithology from inventory sources | **45 records**, all with lithology text |

Per-record lithology is recorded verbatim from the inventory sources, because it describes
the actual failure site rather than a regional polygon:

| Stated lithology | Records |
|---|---:|
| Gneiss/Charnockite | 20 |
| Charnockite gneiss | 18 |
| Charnockite | 3 |
| Garnetiferous Biotite Gneiss, Charnockite | 1 |
| Schistose rock | 1 |
| Schistose/Phyllitic | 1 |
| One long descriptive entry (Hornblende-biotite gneiss…) | 1 |

**This is not a substitute for a geology layer.** It is site-level evidence that can later
be used to *validate* a vector geology layer at 45 points, which is worth more than the
layer alone. GLiM remains the only usable vector geology and is coarse enough that it
should be treated as a weak covariate, not a controlling one.

---

## 10. Validation checks actually run

Every check below executed against the files on disk. None is a claim about a URL.

| # | Check | Result |
|---|---|---|
| 1 | GSI Bhusanket index fully enumerated | 1,188 reports; 62 Kerala; exactly 10 Wayanad-related; all 10 PDFs present |
| 2 | GSI 14115 coordinate-line spine | 35 coordinate lines found; assertion `== 35` passed |
| 3 | GSI 14115 printed serial numbers | 35 records under **34** distinct printed numbers (Sl. 21 duplicated) — source defect recorded |
| 4 | GSI 14115 spot checks against printed pages | **13/13** area and length values match |
| 5 | GSI 14115 geology coverage | 35/35 rows populated (6 recovered from the page cited) |
| 6 | 42-point datasheet DMS parse | Both sheets parsed with `fullmatch` patterns that raise on mismatch — no silent mis-read |
| 7 | Degraded-glyph coordinates | 2024 `11027'46"` and 2025 `76' 08' 8.34"` parsed by dedicated validators, not a loose regex |
| 8 | Point-in-polygon boundary test | 445/468 inside GADM Wayanad; 23 outliers each individually explained |
| 9 | Crosswalk index integrity | assertion that every matched label belongs to the B mask (added after a positional-index bug was found and fixed) |
| 10 | Re-projection for distances | EPSG:32643 metric; distances computed after reprojection, not in degrees |
| 11 | Distance sanity | no pair reports a physically impossible separation; GSI2018↔KER2018 range 361–1,453 m |
| 12 | 2024 coordinate corroboration | 495 m between independent sources; 4.91 km to Chooralmala |
| 13 | CSV round-trip | all 4 processed products and 3 extracts reload with the `csv`/pandas readers without error |
| 14 | Manifest regeneration | 28 datasets, 16 columns, parses cleanly |
| 15 | Boundary area sanity | GADM Wayanad = **2,121.0 km²** in EPSG:32643, matching the published district area |

---

## 11. Defects retained, not corrected

Each is preserved exactly as the source published it, with a flag. Nothing was repaired
silently.

| Defect | Where | Handling |
|---|---|---|
| Printed longitude `76°56'58"E` (~77 km east, in Tamil Nadu) | GSI 14115 Sl.17 | Retained as printed; `NEEDS_REVIEW`; excluded from spatial use |
| Printed Sl. No. 21 used twice | GSI 14115 table | Both rows kept; 35 records vs 34 serial numbers reported separately |
| 2 undated rows (Chempra; Thariyodu reservoir-induced) | GSI 14115 rows 22, 28 | Kept as site records; never counted as events |
| Degree glyph lost, printed as `0` (`11027'46"`) | GSI PDLS 2024 | Parsed by a validator that requires the exact degraded form |
| Minute glyph where degree belongs (`76' 08' 8.34"`) | GSI PDLS 2025 | Parsed and documented in `coord_text_verbatim` |
| "2020-21" is a field season, not an event year | GSI 15990 | Report dates the Plamoola subsidence to **13–17 August 2018** |
| "2025" report, June 2024 event | GSI PDLS 2025 | Grouped as a 2024 event |
| No per-event dates | KER2018 | Recorded as year precision (332 records) |
| Location fields absent for many rows | KER2018 | Left blank; not imputed |
| 2-decimal coordinates | GSI 14337, NASA GLC | Precision recorded; subordinated to better coordinates where a match exists |

---

## 12. What remains unverifiable

| Item | Blocker | Consequence |
|---|---|---|
| Puthumala 2019 primary record | GSI 2019-20 Wayanad report absent from the public index | Stays `SECONDARY_SOURCE_ONLY` |
| 2020–2023 Wayanad events | No GSI post-disaster volume exists for these years | Year coverage is 0; **not** evidence of absence |
| Vector 1:50,000 geology | Bhukosh TCP timeout; REST `499 Token Required` | GLiM only; site lithology for 45 records |
| Bare-earth DEM | FABDEM timeout; SRTMGL1 auth-gated | GLO-30 DSM remains primary |
| Kerala ILDM 2024 report | TLS handshake fails at host level | Not obtained |
| 2024 event footprint polygon | Not published openly | Point + narrative runout only |

No authentication, access control or licence restriction was bypassed. Each blocker is
recorded with the exact observed failure mode.

---

## 13. Products

| File | Rows | Contents |
|---|---:|---|
| `data/processed/inventory/inventory_source_records.csv` | 468 | Every source record with inclusion decision, event group, verification status |
| `data/processed/inventory/inventory_events_2000_2026.csv` | 385 | Dated records, event-level view |
| `data/processed/inventory/duplicate_crosswalk.csv` | 45 | Candidate pairs, measured separation, basis, decision, confidence |
| `data/processed/inventory/coverage_2000_2026.csv` | 27 | Per-year record and event counts, with exclusions shown |
| `data/processed/inventory/inventory_all_source_records.csv` | 468 | Pre-decision assembly with boundary test |
| `data/processed/inventory/2024_corroboration.json` / `.csv` | — | 2024 coordinate evidence |
| `data/interim/inventory_extracts/inventory_gsi14115_wayanad.csv` | 35 | GSI 14115, arc-second, reviewed dates |
| `data/interim/inventory_extracts/inventory_gsi_pdls_wayanad.csv` | 2 | GSI 2024/2025 42-point datasheets |

---

## 14. Summary

- **468 source records** from 8 sources; **385 dated**, **83 undated sites**.
- **372 in-window included records → 371 event groups.** 6 pre-2000 records kept outside the window.
- **368 of 372** in-window records are source-confirmed or corroborated; 3 secondary-only, 1 needs review.
- **19 of 27 years have no record**, explained by source coverage rather than absence of landslides.
- **2018 dominates** (339 records) because a statewide mapped inventory exists for that season.
- **July 2024 coordinate resolved**: `CORROBORATED` at 495 m agreement against an independent publication.
- **33/35 two-decimal GSI records tied to arc-second records**, upgrading their usable precision.
- **Vector geology remains the weakest input**: GLiM 1:3.75 M is the only option, with site lithology for 45 records as a partial check.

**No preprocessing, training table, synthetic event, model or performance metric has been
produced. Susceptibility mapping has not started.**
