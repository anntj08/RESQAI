# RESQAI — Resilient Emergency Intelligence Platform

Final-year engineering project. Long-term: AI-driven disaster decision intelligence (synthetic scenarios,
landslide/flood risk, GIS risk maps, decision support, authority & citizen interfaces).

**Current scope:** landslide *susceptibility* mapping for Wayanad district, Kerala, India.
Susceptibility = where conditions favour failure. Not a timing forecast.

## Status (2026-10-25)

| Phase | State |
|---|---|
| Dataset acquisition | Done — 8 categories, 404 raw files, 7.7 GB |
| Dataset validation | Done for raster/vector layers; inventory validated at record level only |
| Preprocessing | Not started |
| Training table | Not built |
| Model / metrics | None. No accuracy figure exists. |

## Read first

- `AGENTS.md` — conventions and hard rules
- `docs/ACQUISITION_REPORT.md` — what was obtained, what was blocked and why
- `docs/data_quality_report.md` — validation evidence and caveats per dataset
- `docs/data_manifest.csv` — 16 datasets with source, version, CRS, status
- `docs/data_sources.md` — every endpoint tried, including failures

## Data

Raw downloads live under `data/raw/` and are git-ignored. Checksums for all 404 raw files are in
`data/file_inventory.csv`. Per-source inventory extracts are in `data/interim/inventory_extracts/`
and are deliberately **not merged**.

Acquisition is reproducible via the scripts in `scripts/` (each is idempotent; existing files are skipped).

## Known gaps

- GSI 1:50,000 geology (Bhukosh unreachable; ArcGIS services token-gated) — GLiM 1:3.75 M used instead
- Post-2019 landslide events, including July 2024 — absent from all acquired inventories
- Event dates for most historical records — missing
- Official Survey of India district boundary — not obtained; GADM 4.1 used
