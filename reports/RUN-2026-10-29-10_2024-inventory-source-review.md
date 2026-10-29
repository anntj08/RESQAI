# Run Report RUN-2026-10-29-10 — Official-source discovery review: a Wayanad inventory covering the July 2024 events

**Date:** 2026-10-29 · **Session goal:** establish whether a *publicly accessible official* source
exists that provides a **multi-event geospatial inventory** of the July 2024 Wayanad landslides
(beyond the two single-point 2024 records already in the Phase 4 inventory) — documentation/
research only; no inventory data downloaded/merged, no manifest or Phase 4/5 changes.
**Starting state:** commit `e6a8850` (RUN-08 complete); tree with this run's early evidence
already in progress. A **concurrent session** (see §5) occupied run number 09.
**End state:** work + this report committed (hash pinned in §6); tree clean; nothing pushed.

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | read AGENTS.md, PHASE5_PROGRESS, data_sources.md, INVENTORY_VERIFICATION_REPORT.md, manifest INV rows | baseline facts | inventory already carries 2 single-point 2024 records (PDLS 2024 Mundakkai; PDLS 2025 Meenakshi Bridge, June 2024) |
| 2 | on-disk PDLS 2024 text scan | what the GSI volume itself contains | FIR names **4** incidence locations (L3245: Chooralmala, Mundakkai, Attamalai, Vellarimala); only **1** Wayanad datasheet (Mundakkai, L258 ff., DMS coords L268–269); other datasheets = Vanimel panchayat (outside Wayanad) |
| 3 | `scripts/review_bhusanket_index_2024.py` → `index_review_log.txt` | catalogue review + live re-diff | on-disk index 1,188 reports; 66 Kerala (content match); 8 Wayanad-titled = exactly the 8 PDFs on disk; **live index unreachable** (ConnectionResetError 10054, then connect timeouts; also webfetch transport error — two independent paths) |
| 4 | `scripts/enumerate_bhusanket_kerala.py` | Kerala + late-FS enumeration | only Kerala FS 2024-25/2025-26 landslide entries: PDLS_2024_51817, PDLS_2025_61074 (both on disk), SRO-16730 (Kodassery, Thrissur), SRO-16693 (Kuttikkanam, Idukki) — **no Wayanad-2024 multi-event entry** |
| 5 | websearch integration | discovery aid | unavailable ("No search results found" for every query incl. trivial controls) → fell back to direct fetches |
| 6 | `scripts/probe_official_sources_2024.py` (+ `_round2/3/4/5`) → `official_sources_probe*.json` | reachability + link evidence, 26 URLs across 15 official hosts | KSDMA pages 200; gsi.gov.in 200; wayanad.gov.in 200; ndma.gov.in 200; dmsuite 200; bhuvan wrapper 200; bhusanket/bhukosh connect-timeout; nidm TLS hostname mismatch; Copernicus legacy URLs 404 |
| 7 | `scripts/assess_ksdma_2024_documents.py` → `ksdma_documents_assessment.json` | retrieve + first-pass scan of the two KSDMA 2024 documents not on disk | FPS2025.pdf 8,410,909 B / 17 pp; Environment-Committee-2025.pdf 531,775 B / 47 pp; go_ms6 = 2 pp, 0 chars, 1 image/page (**image-only scan** — closes the 44-byte-extract mystery) |
| 8 | `scripts/scan_ksdma_docs_text.py` → `ksdma_documents_deepscan.json` | EN+ML pattern scan, image-page check | FPS2025: latitude/longitude/gps/survey-number/inventory/annexure = 0 ('coordinate' ×2 prose), p17 image-only cover; Env-Committee: **all EN and ML patterns 0** (അക്ഷാംശം/രേഖാംശം/സർവേ നമ്പർ/വാർഡ്/ഇൻവെന്ററി/പട്ടിക), no image-only pages → both are **discussion reports, not inventories** |
| 9 | browser session on `mapping.emergency.copernicus.eu/activations/` + `scripts/query_cems_activations_api.py`, `scripts/cems_india_details.py` → `cems_api_*.json` | enumerate CEMS activations | public API found from grid network log; **q=Wayanad → 0; q=Kerala → 0**; q=India → 5 activations (EMSR049/054/057/104/357: 2013–2019 cyclones/floods, none landslide); controls q=Nepal → 3, q=landslide → 30 prove filters work → **verified negative** |
| 10 | `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md` written; `docs/data_sources.md` minimally updated; `.gitignore` addition | the deliverables | per-candidate table (16 candidates, A–P), verified-negative section, unresolved-access table, interpretation separated |
| 11 | `git checkout -- data/interim/p3/verify_all.json` | drop timing-only churn created by the concurrent session's p5_verify run | tree noise removed |
| 12 | p2/p3/p4 checkers + `git diff --check` | documentation gates | p2 pass; p3 **470/470**; p4 **116/116**; diff-check clean |
| 13 | commits + hash pin | capture | §6 |

## 2. Measured values (do not re-derive)

- **Bhusanket (GSI):** on-disk catalogue = 1,188 reports; 66 Kerala content-matches; 8 Wayanad-titled (= the 8 on-disk PDFs); live host unreachable 2026-10-29 (10054 reset + connect timeouts + webfetch transport error); last verified catalogue state 2026-10-25 shows **no Wayanad-2024 multi-event report entry**.
- **PDLS 2024 volume:** 4 named July-2024 incidence locations (FIR), 1 Wayanad datasheet (Mundakkai: 11.462778 N, 76.134167 E; DMS whole-second ≈ 31 m), all four locations stated as MSZ in the 2022 NLSM LSZ (L3281–3282).
- **KSDMA "Reports – Landslides 2024" page hosts exactly 4 documents:** Memorandum_17082024.pdf (on disk, INV-10), Meppadi PDNA (on disk, INV-09), FPS2025.pdf (17 pp; SRH response report by Family Planning Association India; zero geospatial structures), Environment-Committee-2025.pdf (47 pp; 15th KLA Committee on Environment 13th Report, "Wayanad Landslide 2024 – Independent study report", Malayalam, covers Chooralmala–Mundakkai **and** Vilangad/Kozhikode; zero EN+ML geospatial patterns; no image-only pages).
- **KSDMA hazard-maps landslide section** = GSI 2022 LSZ shapefiles only: 14 district zips uploaded 2025/08 incl. `Wayanad.zip`; summary PDF `Landslide_Susceptibility_Zones_Districts_FINAL.pdf` (2025/06). **No post-2024 Wayanad LSZ update; no inventory.**
- **KSDMA event-specific maps** = 2013–2020 only; **no 2024 event map**.
- **Wayanad DDMA `dm-orders` page** = administrative orders 2020–2026 (monsoon prep, dam operations, soil-excavation ban); **no 2024 landslide orders/reports** ('2024' hits: 1).
- **NDMA:** `Landslide_Atlas_2023.pdf` (60 MB, direct public download — **not downloaded**: pre-dates July 2024, cannot contain the events); "Landslide (42.5 MB)" page = awareness-resources landing page, **no dataset link exposed**.
- **Copernicus EMS:** legacy `emergency.copernicus.eu/mapping/*` URLs all 404 (portal migrated); new portal API `mapping.emergency.copernicus.eu/activations/api/activations/`: q=Wayanad **0**, q=Kerala **0**, q=India 5 (all 2013–2019, none landslide), controls q=Nepal 3 / q=landslide 30; `countries=` filter non-functional with `India` and `IND` (returns 0 even for detail-verified India activations — filter quirk, documented).
- **Unreachable/blocked:** bhusanket (TCP timeout), bhukosh (TCP timeout — matches standing GEO-02), nidm.gov.in (TLS hostname mismatch), NRSC Bhuvan + UNOSAT (JS-only, not enumerable statically; UNOSAT not probed — websearch down).
- **go_ms6 PDF:** 2 pages, 0 extractable chars, 1 image/page → image-only government-order scan.

## 3. Bugs caught and fixes

1. `review_bhusanket_index_2024.py` failed on the JS-prefixed catalogue (`LandslideReport = [ … // comments, trailing commas`) — fixed by reusing the phase-1 normalization recipe (`scripts/parse_bhusanket.py`) as `parse_index()`.
2. `show_*` display helpers crashed with `UnicodeEncodeError` (cp1252 console) on non-ASCII link text — fixed with `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`.
3. First context-extraction regex captured only the matched group instead of the full line — fixed in `scan_ksdma_docs_text.py` (full-match contexts).
4. CEMS `countries=India|IND` filter returns 0 even for detail-verified India activations — worked around with `q=` title search + detail endpoint; the quirk is documented in the discovery note.
5. PowerShell inline-python quoting collisions (3×) — all moved to script files per standing convention.
6. **Run-number collision:** a concurrent session had already written `reports/RUN-2026-10-29-09_phase5-demo-reproduction.md`; this run renumbered itself to **10** (note header, data_sources pointer, .gitignore comment) rather than renumbering or touching the other session's files.

## 4. Verification and gates

| Suite | Result |
|---|---|
| `p2_check_consistency.py` | pass |
| `p3_check_consistency.py` | **470/470** |
| `p4_check_consistency.py` | **116/116** |
| `git diff --check` | clean |
| `data/interim/p5/verify_p5.json` (from the concurrent demo session, corroborated this run) | 6/6 gates passed incl. byte-identical regeneration |

## 5. Concurrent session — Phase 5 demo reproduction (run 09)

While this review ran, a parallel session reran the Phase 5 pipeline (`scripts/p5_verify.py`,
**6/6 gates passed**, 14 outputs byte-identical), inspected the figures, wrote
`docs/PHASE5_LIVE_DEMO.md` + `reports/RUN-2026-10-29-09_phase5-demo-reproduction.md`, and
explicitly left this run's in-progress files untouched — but could not commit ("`.git` is
read-only in this workspace"), leaving both files untracked. Actions taken here:
`data/interim/p3/verify_all.json` timing churn from its verifier run was reverted; its two
documents were left byte-intact and committed separately with attribution (§6); its `09`
number was respected by renumbering this review to `10`. Its measured claims were spot-checked
against `verify_p5.json` (6 gates, all passed) before committing.

## 6. Outputs and current project state

**Created:** `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md` (per-candidate table A–P, CEMS
verified-negative §3, unresolved-access table §4, interpretation §5); 16 scripts in `scripts/`
(probes ×5 rounds, catalogue review/enumeration, document assessment/deep-scan, CEMS API
queries + details, NDMA page fetchers, display helpers); evidence in
`data/interim/inventory_source_review_2026-10-29/` (probe JSONs + logs, document assessments,
CEMS API JSONs + grid CSV, the two assessed PDFs — PDFs git-excluded via `.gitignore`).
**Updated:** `docs/data_sources.md` (§1.9 dated pointer; §2 rows: Bhusanket unreachable,
Copernicus retired-404, NIDM TLS, Bhukosh refresh note); `.gitignore` (evidence-PDF exclusion).
**Untouched, as instructed:** manifest statuses, inventory files, Phase 4/5 outputs, model, map.

**Conclusion:** no publicly accessible official multi-event geospatial inventory of the July
2024 Wayanad disaster exists (or is reachable today). The inventory's 2024 coverage remains
the two PDLS single-point records. Commit of this run's work + report: **pinned below**;
the concurrent session's two documents committed separately; tree clean; nothing pushed.

## 7. Next-step handoff (prompt material)

- **Decisions for the user:**
  1. Whether to pursue **non-public official channels** (a direct request to GSI/KSDMA/DDMA
     Wayanad for the unreleased July 2024 42-point datasheets — the PDLS programme collects
     them per event, so an internal Wayanad-2024 set may exist unpublished).
  2. Whether to schedule a **reachability re-probe** of Bhusanket/Bhukosh
     (`python scripts/review_bhusanket_index_2024.py` re-diffs the live catalogue against the
     on-disk index in one command) and an interactive enumeration of the NRSC Bhuvan atlas /
     UNOSAT (browser session; websearch still down).
  3. Whether to keep the two assessed KSDMA documents as on-disk evidence (current state) or
     promote them to `data/raw/` at a future authorized acquisition.
- **What must not be re-derived:** the CEMS negative (quote the discovery note §3 — API queries
  with positive controls); the Bhusanket catalogue state (on-disk index = last verified
  2026-10-25; live unreachable 2026-10-29); the two document classifications (zero EN+ML
  geospatial patterns); the PDLS "four incidence locations" FIR fact (L3245) and the
  single-Wayanad-datasheet fact; the go_ms6 image-only finding.
- **Standing rule for any future use of these candidates:** map products and prose are never
  sources of records; records/coordinates may not be inferred from maps; candidate additions
  happen only at an authorized acquisition with file-level validation.
- **Quick commands:** `python scripts/review_bhusanket_index_2024.py` ·
  `python scripts/probe_official_sources_2024.py` (and `_round2…5`) ·
  `python scripts/query_cems_activations_api.py` · p2/p3/p4 checkers + `git diff --check`.
