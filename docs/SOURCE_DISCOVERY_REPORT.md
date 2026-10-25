# Source Discovery Report — Wayanad landslide data

**Phase:** 2 (acquisition-gap recovery and inventory verification)
**Date of discovery work:** 2026-10-25
**Base commit:** `b148ad7`
**Scope:** Wayanad district, Kerala. Historical landslide events 2000-01-01 to 2026-12-31,
plus the conditioning datasets (geology, terrain, rainfall, land cover) needed later.

This report records what was searched, what was found, what was actually obtained, and
what remains blocked. It deliberately separates *identified* from *downloaded* from
*verified*. A catalogue entry, a search hit or a working URL is not evidence that a
dataset exists on disk or that its content is correct.

---

## 1. How the search was done

Four discovery routes were used, in this order:

1. **Publisher indexes, enumerated exhaustively.** The GSI Bhusanket `LandslideReport.json`
   index (1,188 reports) was parsed and filtered by state, season, project type and title
   keyword. This is a closed list that can be counted, so the claim "GSI's public index
   contains exactly 10 Wayanad-related reports" is checkable rather than impressionistic.
2. **Reference-chaining from acquired documents.** The 2025 GSI post-disaster volume cites
   its own predecessors in its bibliography. Following those citations is what exposed the
   missing 2019-20 Wayanad report (Section 5, gap G1) and the 1:50,000 susceptibility
   reports covering Wayanad toposheets.
3. **State-level publisher traversal.** KSDMA (`sdma.kerala.gov.in`) organises material by
   disaster year. Its per-year landslide pages were fetched and every document link on them
   extracted, which is how the Meppadi PDNA and the 2024 Memorandum were found.
4. **Literature and repository search.** DANS/Dataverse, NHESS supplements, PMC open-access
   full text, OSM/Nominatim gazetteer, NASA GLC. Used for both event records and
   independent coordinate checks.

Search terms were not restricted to the names already in the repository. Queries were run
on place names (Mundakkai, Chooralmala, Puthumala, Meppadi, Vellarimala, Attamala,
Kottapadi, Muppainadu, Noolpuzha), on toposheet numbers (58A/03, 58A/02, 49M/14, 49M/13),
on publisher names, and on event years.

---

## 2. Source landscape and evaluation

Status vocabulary is the one defined in `AGENTS.md` and the phase-2 brief.

### 2.1 Landslide event inventories

| # | Source / publisher | Content | Coverage | Status | Independence | Value |
|---|---|---|---|---|---|---|
| 1 | **GSI 14115**, Landslide Inventory of Kerala (FS 2007-2010) | 35 Wayanad records, 1961-2009, arc-second coordinates, dates, lithology, land use, morphometry, causes, impacts | Wayanad district table, pp. 135-148 | `VERIFIED` (extracted) | Primary GSI field investigation | **Highest.** The only source in the project giving arc-second coordinates *and* dates for the 2006-2009 events |
| 2 | **GSI PDLS 2024** | 15 slide records statewide, 1 in Wayanad (Mundakkai-Chooralmala) | 2024 monsoon | `VERIFIED` | Primary | **Highest.** Only official per-event record of the July 2024 disaster |
| 3 | **GSI PDLS 2025** | 16 slides statewide, 1 in Wayanad (Meenakshi Bridge) | reported May 2025; event June 2024 | `VERIFIED` | Primary | High. Fills a 2024 sub-event the 2024 volume missed |
| 4 | **Hao/van Westen 2018 Kerala inventory** (DANS `doi:10.17026/dans-x6c-y7x2`) | 4,728 points statewide, 331 in Wayanad, with area, type, land use 2010/2018, building/road/agriculture impact | 2018 monsoon | `VERIFIED` | **Composite** — built from NRSC + GSI plus new mapping | **Highest for volume.** Turns one 2018 record into 331; but not independent of GSI |
| 5 | GSI 14337 hazard zonation (2012-13) | 35 Wayanad records | pre-2012 | `DOWNLOADED_NOT_FULLY_VALIDATED` (phase 1) | Same GSI lineage as #1 | Low now superseded: coordinates are 2-decimal |
| 6 | GSI 14768 1:50,000 susceptibility (2015-16) | 29 archival + 17 field records | undated | `DOWNLOADED_NOT_FULLY_VALIDATED` (phase 1) | Same GSI lineage | Medium. Adds 17 field-surveyed sites not in 14115 |
| 7 | GSI June-2018 Wayanad post-disaster note | 8 slides, 42-point datasheets | 2018-06-14 to 16 | `DOWNLOADED_NOT_FULLY_VALIDATED` (phase 1) | Primary | High detail per record, low count |
| 8 | GSI 15990 Plamoola subsidence (FS 2020-21) | Site study of a subsidence dated **13-17 Aug 2018** | 2018 | `DOWNLOADED_NOT_FULLY_VALIDATED` | Primary | Medium. Corrects a likely misreading: the "2020-21" is the field season, not the event year |
| 9 | NASA Global Landslide Catalog | 9 records in the district bounding box, **2 actually inside Wayanad** | 1997-2016 | `VERIFIED` (phase 1) | Secondary, media-derived | Low but non-zero: contributes a 2007 fatal event and a 2017 road-block event; catalogue ends 2016 |
| 10 | Sreekumar et al. 2025, Sci Rep Table 1 | 6 Kerala events, 2 in Wayanad (Mundakkai 2024, Puthumala 2019) | 2018-2024 | `DOWNLOADED_NOT_FULLY_VALIDATED` | Independent publication | **High for verification**, not for volume. Provides the only accessible coordinate for Puthumala 2019 |
| 11 | KSDMA Meppadi PDNA 2024 | 647-pp post-disaster needs assessment | 2024 event | `DOWNLOADED_NOT_FULLY_VALIDATED` | Government, partially derived from GSI FIR | Medium. Impact/recovery evidence, not an event list |
| 12 | KSDMA Memorandum 17082024 | Event narrative, timeline, rainfall, crown-to-village distances | 2024 event | `DOWNLOADED_NOT_FULLY_VALIDATED` | Government | **High for verification** of the 2024 location |
| 13 | KSDMA October 2021 event report | SEOC daily log, 115 pp | Oct 2021 | `DOWNLOADED_NOT_FULLY_VALIDATED` | Government | **Nil for inventory** — verified to contain no landslide inventory; Wayanad appears only in rainfall-alert lists |
| 14 | GFLD (Froude & Petley 2018) | 3 supplementary tables | 2004-2016 | `DOWNLOADED_NOT_FULLY_VALIDATED` | Independent, Durham | **Nil.** Supplements hold only the trigger classification scheme and summary statistics; the event database is not redistributed |
| 15 | GSI 14336, 12272, 12236 | Miscellaneous Kerala studies, 1990s Wayanad geology | pre-2000 | `DOWNLOADED_NOT_FULLY_VALIDATED` | Primary | Low for inventory, some use as geology context. 12236 is image-only (no text layer) |

### 2.2 Conditioning datasets

| # | Source | Content | Status | Assessment |
|---|---|---|---|---|
| 16 | GSI 14767 / 14768 / 14999 | 1:50,000 landslide susceptibility reports covering TS 49M/14, 58A/3, 58A/1-11, 49M/13 | On disk (phase 1) | **The best geology available for Wayanad at 1:50,000 — but only as raster map plates inside PDFs.** No vector geology exists in the project better than GLiM |
| 17 | GSI Bhukosh portal | Vector geology, geomorphology, structure | `ACCESS_RESTRICTED` | `bhukosh.gsi.gov.in` refused TCP connections on 443 on repeated attempts; Bhusanket ArcGIS REST returns `499 Token Required` |
| 18 | GLiM 1:3.75 M | Lithology polygons | `VERIFIED` (phase 1) | Coarse; ~4 km effective detail; retained as the only usable vector geology |
| 19 | Copernicus GLO-30 | 30 m DSM | `VERIFIED` (phase 1) | Retained as primary terrain |
| 20 | FABDEM | 30 m bare-earth DEM | `ACCESS_RESTRICTED` | `data.bris.ac.uk` connect timeout |
| 21 | NASA SRTMGL1 V003 | 30 m bare-earth | `ACCESS_RESTRICTED` | Earthdata Login required (unchanged) |
| 22 | Kerala ILDM 2024 Wayanad report | 142-pp state landslide report | `UNAVAILABLE` | TLS handshake fails for `ildm.kerala.gov.in` on every path including `/`, over both https and http |
| 23 | KSDI, OneGeology WFS | Boundary/geology web services | `UNAVAILABLE` | Connection timeout |

---

## 3. What was actually acquired in phase 2

Only items newly downloaded in this phase; phase-1 holdings are unchanged.

| Item | Size | Location |
|---|---|---|
| 2018 Kerala inventory, 12 files (shp/dbf/shp components + metadata) | 15.2 MB | `data/raw/landslide_inventory/kerala_2018_dans/` |
| GSI `gsi_14115.pdf` | 4.9 MB | `data/raw/landslide_inventory/gsi_bhusanket/pdf/` |
| GSI `gsi_PDLS_2024_51817.pdf` | 15.1 MB | same |
| GSI `gsi_PDLS_2025_61074.pdf` | 22.5 MB | same |
| GSI `gsi_14336.pdf`, `gsi_12272.pdf`, `gsi_12236.pdf` | 12.7 MB | same |
| KSDMA Meppadi PDNA 2024 | 19.8 MB | `data/raw/landslide_inventory/ksdma/` |
| KSDMA Memorandum 17082024 | 4.1 MB | same |
| KSDMA October 2021 event report | 10.7 MB | same |
| KSDMA G.O. Ms 6 DMD-GSI | 0.2 MB | same |
| GFLD supplementary tables t01-t03 | 0.02 MB | `data/raw/landslide_inventory/gfld/` |
| Two PMC open-access full texts | 0.3 MB | `data/raw/literature_events/` |
| OSM locality checks, 10 place names | 0.01 MB | `data/interim/locality_checks_osm.json` |

One download failed and is documented rather than retried indefinitely:
`easy-migration.zip` (20 KB) from `objectstore.surf.nl` — `ConnectionError`. It is a
Dataverse export artefact, not part of the inventory, so nothing of analytical value is
missing.

---

## 4. Ranked acquisition-gap register

Ranked by the eight criteria in the brief: Wayanad relevance, scientific authority,
likelihood of genuinely new information, precision/temporal gain, compatibility with the
eventual susceptibility study, accessibility, independence, and known limitations.

| Rank | Gap | Why it matters | Status after this phase |
|---|---|---|---|
| **G1** | **GSI 2019-20 "post-disaster studies in Wayanad and Kannur Districts, Kerala"** (Sulal et al. 2020), cited in the bibliography of GSI PDLS 2025 | It is the primary field record of the **August 2019 Puthumala** landslide (11 deaths, 6 missing) and any other 2019 Wayanad failures. Without it, 2019 can only ever be `SECONDARY_SOURCE_ONLY` | **BLOCKED — not in the public index.** Confirmed by enumerating all 62 Kerala reports: the seasons present are 2018-19 (Kozhikode/Kannur/Wayanad June-2018 notes), 2019-20 (**Nilambur and Ernakulam taluks only**), then 2024-25. No 2019-20 Wayanad report is published |
| **G2** | **2020, 2021, 2022, 2023 Wayanad events** | Four consecutive years with zero dated records is almost certainly an observation gap, not an absence of landslides | **PARTIALLY BLOCKED.** No GSI post-disaster volume exists for 2020-2023 in the index. KSDMA's 2021 page yields only a SEOC log with no inventory. The 2021 literature hit (Irumbakachola) is **Palakkad district**, not Wayanad, and was excluded |
| **G3** | **GSI 1:50,000 geology/geomorphology as vector data** | GLiM at 1:3.75 M is too coarse for slope-failure reasoning | **BLOCKED** (Bhukosh unreachable, token-gated REST). The 1:50,000 information exists only as map plates in reports already held — usable for reference, not for analysis without digitisation |
| **G4** | **Bare-earth DEM** (FABDEM or SRTMGL1) | Copernicus GLO-30 is a DSM; canopy height biases slope in forested Western Ghats terrain | **BLOCKED** (FABDEM host timeout; Earthdata login). The phase-1 SRTM Skadi mirror remains the only bare-earth cross-check |
| **G5** | Karala ILDM 2024 Wayanad landslide report | State-level synthesis, 142 pp | **BLOCKED** (TLS failure at host level) |
| **G6** | Digital event footprints (polygons) for 2024 | Point records cannot express a 7 km runout debris flow | **NOT FOUND OPENLY.** Only the GSI point and narrative runout are available |
| **G7** | Pre-2000 Wayanad records | Historical context for recurrence | **PARTLY MET.** GSI 14115 supplies 8 pre-2000 records (1961-1994); 6 of the 35 records are pre-2000 dated. Sufficient for context, no further pursuit justified |
| **G8** | Sentinel-1/2 change detection to *derive* new events | Would fill 2020-2023 | **DELIBERATELY NOT DONE.** That is image analysis, not acquisition, and belongs to a later phase |

---

## 5. Key discovery findings

1. **GSI's public report index is exhausted for Wayanad.** Exactly 10 of the 1,188 reports
   relate to Wayanad, and all 10 PDFs are now on disk. This bounds what GSI can contribute
   without a Bhukosh account.
2. **The single biggest inventory gain is not a new download but a re-read.** GSI 14115 was
   already in the repository from phase 1 but its Wayanad table had never been parsed. It
   contains 35 dated, arc-second records where the rest of the project had 2-decimal,
   largely undated ones.
3. **GSI's own bibliography points at a report GSI does not publish.** Following it
   established gap G1 with evidence rather than assumption.
4. **KSDMA publishes by disaster year, not by event inventory.** The per-year pages lead to
   needs assessments and memoranda, which are excellent for verification and impact and
   useless as inventories. This is worth knowing so the same pages are not re-mined later.
5. **The GFLD is not openly redistributed at event level.** Phase 1 listed it as a target;
   it can now be closed as a source of Wayanad records.
6. **The 2018 Kerala dataset is composite, not independent.** It is the largest single
   source (331 records) but shares GSI/NRSC lineage. Its `GSI` and `NRSC` flags make this
   auditable per record, and the verification report uses them.

---

## 6. Reproducibility

Discovery is re-runnable through:

```
scripts/p2_gsi_index_search.py       # enumerate GSI Wayanad reports
scripts/p2_gsi_index_search2.py      # confirm the count and check the PDFs on disk
scripts/p2_ksdma_discover.py         # enumerate KSDMA per-year documents
scripts/p2_probe_remaining.py        # record blockers with evidence
scripts/p2_locate_gfld.py            # locate GFLD supplements
scripts/p2_fetch_pmc_tables.py       # pull open-access event tables
scripts/p2_locality_check.py         # OSM place-name checks
```

No authentication, access control or licence restriction was bypassed. Every blocked
source is recorded with the exact failure mode observed, not a guess.
