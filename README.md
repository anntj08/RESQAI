# RESQAI — Resilient Emergency Intelligence Platform

Final-year engineering project. Long-term: AI-driven disaster decision intelligence (synthetic scenarios,
landslide/flood risk, GIS risk maps, decision support, authority & citizen interfaces).

**Current scope:** landslide *susceptibility* mapping for Wayanad district, Kerala, India.
Susceptibility = where conditions favour failure. Not a timing forecast.

## Status (2026-10-25)

| Phase | State |
|---|---|
| Dataset acquisition | Done — 8 categories, phase 2 added the event inventory sources |
| Dataset validation | Done for raster/vector layers; inventory validated per record |
| Landslide inventory (2000–2026) | Done — 468 source records, 372 in-window, 371 event groups |
| Preprocessing | Not started |
| Training table | Not built |
| Model / metrics | None. No accuracy figure exists. |

## Read first

- `AGENTS.md` — conventions and hard rules
- `docs/INVENTORY_VERIFICATION_REPORT.md` — record counts, precision, duplicates, year coverage
- `docs/SOURCE_DISCOVERY_REPORT.md` — source landscape and the ranked gap register
- `docs/ACQUISITION_REPORT.md` — what was obtained, what was blocked and why
- `docs/data_quality_report.md` — validation evidence and caveats per dataset
- `docs/data_manifest.csv` — 28 datasets with source, version, CRS, status
- `docs/data_sources.md` — every endpoint tried, including failures
- `docs/PHASE2_PROGRESS.md` — resumable checkpoint log

## Data

Raw downloads live under `data/raw/` and are git-ignored. Checksums for every raw file are in
`data/file_inventory.csv`. Per-source inventory extracts are in `data/interim/inventory_extracts/`
and are deliberately **not merged**.

Consolidated inventory products are in `data/processed/inventory/`:

| File | Contents |
|---|---|
| `inventory_source_records.csv` | 468 records with inclusion decision, event group, verification status |
| `inventory_events_2000_2026.csv` | 385 dated records, event-level view |
| `duplicate_crosswalk.csv` | 45 candidate pairs with measured separations and decisions |
| `coverage_2000_2026.csv` | per-year record and event counts |

Acquisition and assembly are reproducible via the scripts in `scripts/` (each is idempotent; existing files
are skipped). Regenerate the manifest with `python scripts/build_manifest.py`, never by hand-editing the CSV.

## Inventory at a glance

- **468 source records from 8 sources**; 385 dated, 83 undated site records.
- **372 in-window records (2000–2026) → 371 distinct event groups.**
- 2018 dominates (339 records) because a statewide mapped inventory exists for that monsoon.
- 19 of 27 years have no record — an **observation gap**, not evidence of absence.
- Source-record counts are always reported separately from distinct-event counts.

## Known gaps

- GSI 1:50,000 geology (Bhukosh unreachable; ArcGIS services token-gated) — GLiM 1:3.75 M used instead
- Puthumala 2019 primary record — GSI's 2019-20 Wayanad report is absent from the public index;
  the event is `SECONDARY_SOURCE_ONLY`
- 2020–2023 events — no GSI post-disaster volume exists for those years
- Event dates — 332 of 372 in-window records resolve only to a year
- Official Survey of India district boundary — not obtained; GADM 4.1 used

**No preprocessing, training table, synthetic event, model or performance metric has been produced.**
