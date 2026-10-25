# RESQAI — Phase 2 Progress Log

**Scope:** source discovery, acquisition-gap recovery, landslide inventory verification (2000–2026).
**Started:** 2026-10-25. **Base commit:** b148ad7.

Checkpoints are appended as work proceeds. If interrupted, resume from the last DONE marker.

## Stage 1 — Inspect existing work
- [x] Repo state confirmed: clean tree, 1 commit, no running python processes
- [x] 404 raw files / 7.7 GB intact
- [x] docs read: manifest (16 datasets), sources, quality, acquisition report
- [x] inventory extracts inventoried: 35 / 29 / 17 / 8 / 9 = 98 rows raw
- [x] gap register (see `docs/SOURCE_DISCOVERY_REPORT.md`)

## Stage 2 — Source discovery — DONE
- [x] GSI Bhusanket report index fully enumerated: 1,188 reports, 62 Kerala
- [x] Confirmed GSI's public index holds exactly **10** Wayanad-related reports, all 10 now on disk
- [x] Enumerated KSDMA (sdma.kerala.gov.in) per-year landslide pages + document links
- [x] Enumerated DANS/Dataverse (2018 Kerala inventory), NHESS (GFLD), PMC (2025 papers),
      OSM/Nominatim (place-name checks)
- [x] Blockers recorded with evidence in the discovery report (Bhukosh, ILDM, FABDEM, KSDI)

## Stage 3 — Gap ranking — DONE
- [x] Ranked register written to `docs/SOURCE_DISCOVERY_REPORT.md`

## Stage 4 — Acquisition — DONE
- [x] 2018 Kerala monsoon inventory, 4,728 points statewide, CC-BY-4.0
- [x] 6 additional GSI PDFs (2024, 2025, 14115, 14336, 12272, 12236)
- [x] 4 KSDMA PDFs (Meppadi PDNA 2024, 2024 Memorandum, Oct-2021 event report, G.O.)
- [x] GFLD supplementary tables t01–t03
- [x] 2 PMC open-access full texts (2025 event papers)
- [x] OSM locality checks for 10 place names

## Stage 5 — Inventory build — DONE
- [x] GSI 14115 Wayanad table parsed: 35 records, 27 inside 2000–2026, arc-second coords
- [x] GSI 2024 + 2025 42-point datasheets parsed: 2 records
- [x] Consolidated 468 source records across 8 sources
- [x] Point-in-polygon boundary check: 445/468 inside GADM Wayanad
- [x] Duplicate crosswalk: 45 candidate pairs with measured separations
- [x] Event grouping: 372 in-window records -> 371 event groups

## Stage 6 — Verification — DONE
- [x] 2024 coordinate question resolved quantitatively (495 m agreement with an
      independent publication; 4.91 km from Chooralmala vs KSDMA's stated ~5 km)
- [x] 2-decimal GSI 14337 records tied to arc-second 14115 records (33/35 within 1.5 km, median 471 m)
- [x] Year-by-year coverage 2000–2026 produced

## Stage 7 — QA and documentation — DONE
- [x] `docs/SOURCE_DISCOVERY_REPORT.md`
- [x] `docs/INVENTORY_VERIFICATION_REPORT.md`
- [x] data_sources / manifest / acquisition report / quality report / README updated
- [x] `data/file_inventory.csv` regenerated (431 raw files, 7,808.5 MB)
- [x] `scripts/p2_check_consistency.py` — 60 assertions tying every number quoted in
      the docs to the CSVs on disk; all pass

## Stage 8 — Corrections found by the QA pass — DONE

The consistency pass was not a formality; it caught five real defects. Recorded because
each one changed a published number.

- [x] **Crosswalk paired the wrong records.** `gpd.GeoSeries(gpd.points_from_xy(...))`
  discards the source index and installs a 0..n-1 RangeIndex, so `idxmin()` returned a
  *position* that was then used as a *row label*. Distances were correct but some pair
  identities were not (e.g. `GSI_PDLS -> GSI14115` instead of `-> LIT2025`). Fixed by
  passing `index=A.index` / `index=B.index` explicitly, plus an assertion that every
  matched label belongs to the B mask. Crosswalk rebuilt: 45 pairs, `GSI2018 -> KER2018`
  now 8 pairs, `GSI_PDLS -> LIT2025` 1 pair at 495 m, confidence `high`.
- [x] **Boundary rule was a blanket "review".** All 23 outside points were treated alike.
  A measured distance showed 5 GSI 14768 rows at **Vazhikkadavu sit 17.1–17.4 km
  outside** — a different district, not a generalisation artefact. Replaced with a
  measured 5 km rule and a stored `dist_outside_boundary_m`. Result: 12 excluded,
  10 retained for review. No event count changed (all five were undated).
- [x] **7 dated out-of-district records were labelled `SITE_UNDATED`.** They had dates but
  never received an event group. Now every dated record gets a group; dated 385,
  undated 83 (was 378/90).
- [x] **GADM area was computed by scaling degrees** (`2,165.7 km²`). Re-measured in
  EPSG:32643: **2,121.0 km²**, matching the published figure.
- [x] **"20 of 27 empty years" was wrong.** 8 years carry records, so **19** are empty.

Also fixed: a spurious "Agent number" section in the discovery report, and crosswalk
confidence is now evidence-derived (agreement on stated date raises it) rather than
purely distance-derived.

## Open blockers (documented, not worked around)
- GSI Bhukosh: TCP connect timeout on 443 from this machine.
- GSI Bhusanket ArcGIS REST: `499 Token Required`.
- GSI 2019-20 "post-disaster studies in Wayanad and Kannur" (cited in GSI's own 2025
  bibliography) is absent from the public report index — the Puthumala 2019 record
  therefore cannot be SOURCE_CONFIRMED from GSI.
- Kerala ILDM host `ildm.kerala.gov.in`: TLS handshake fails for every path including `/`.
- FABDEM (`data.bris.ac.uk`): connect timeout.
- NASA SRTMGL1 V003: Earthdata Login required (unchanged from phase 1).
