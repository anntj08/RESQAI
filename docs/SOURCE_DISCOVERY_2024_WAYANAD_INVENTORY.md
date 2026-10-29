# Source Discovery — a Wayanad landslide inventory covering the July 2024 events

**Date:** 2026-10-29 · **Run:** RUN-2026-10-29-10 · **Type:** official-source discovery review (documentation/research only)
**Question:** does a *publicly accessible official* source exist that provides a **multi-event geospatial inventory** of the July 2024 Wayanad landslides — beyond the two single-point records already in the Phase 4 inventory?
**Answer:** **No.** Every qualifying official channel was checked and none provides such an inventory. The evidence per candidate is recorded below; one verified negative (Copernicus EMS) was confirmed against a live API with positive controls. No dataset status, inventory file, manifest row or Phase 5 output was changed by this review.

> **Scope rule kept.** This note classifies *sources*; it adds no records. Nothing here may be
> treated as inventory data. Where a document contains a map or prose description of the
> disaster, it is recorded as such — records and coordinates are **never** inferred from maps
> or prose. Susceptibility/inventory work estimates *where* conditions favour failure; nothing
> here speaks to *when*.

---

## 1. What already exists (baseline for the question)

From `docs/INVENTORY_VERIFICATION_REPORT.md` (authoritative):

- The Phase 4 inventory (468 source records) already carries **two 2024 point records**:
  1. **GSI PDLS 2024** (acc. 51817) — one Wayanad 42-point geo-parametric datasheet for the **Mundakkai–Chooralmala** event (11.462778 N, 76.134167 E; DMS whole-second precision ≈ 31 m; corroborated 495 m from the Sreekumar et al. 2025 location, `CORROBORATED`).
  2. **GSI PDLS 2025** (acc. 61074) — one Wayanad 42-point datasheet for the **Meenakshi Bridge, June 2024** event.
- The GSI PDLS 2024 volume's own field report names **four** July 2024 incidence locations — *"incidences occurred in Chooralmala, Mundakkai, Attamalai and Vellarimala"* (extract line 3245 of `data/interim/gsi_pdf_text/gsi_PDLS_2024_51817.txt`) — and states all four fall in the GSI 2022 **Moderate Susceptibility Zone** (lines 3281–3282). The volume contains only **one** Wayanad datasheet (Mundakkai); its other datasheets are Vanimel panchayat (outside Wayanad).
- AGENTS.md's "No inventory contains the July 2024 Wayanad landslides" states the phase-1 position; phase 2 added the two single points above. The gap this run tested is therefore the **multi-event** inventory: one geospatial table covering the several July 2024 events.

## 2. Result per candidate source

Classification key: **INVENTORY** = downloadable table/file of georeferenced event records; **REPORT** = prose/discussion document (may embed a single-event datasheet or maps); **PORTAL/NEGATIVE/UNREACHABLE** as labelled. Coordinates/records are **not** inferred from maps anywhere below.

| # | Candidate (title) | Agency | Event / time coverage | Geographic coverage | Record fields / spatial format | Coordinate precision | Access conditions | Classification | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| A | GSI Bhusanket report catalogue (live) | Geological Survey of India | catalogue spans 1986–2026 field seasons | national (all states) | catalogue fields: Sl.No, Acc. No., Field Season, State, Project type, Title | n/a (report metadata) | public web; **unreachable 2026-10-29** (TCP connect timeout, two independent paths) | PORTAL — last verified state (2026-10-25 on-disk index) contains **no dedicated Wayanad-2024 multi-event report entry**; only Kerala FS 2024-25/2025-26 landslide entries are PDLS 2024 (51817), PDLS 2025 (61074) (both on disk) and two meso-scale LSZ maps (Kodassery/Thrissur SRO-16730, Kuttikkanam/Idukki SRO-16693) | `data/interim/inventory_source_review_2026-10-29/bhusanket_index_review.json`, `index_review_log.txt`; scripts `review_bhusanket_index_2024.py`, `enumerate_bhusanket_kerala.py` |
| B | GSI PDLS 2024, "Post-Disaster Studies of Landslides in Kerala, 2024" (acc. 51817) | GSI | July 2024 Wayanad + other 2024 Kerala events | Kerala | 42-point geo-parametric datasheets; DMS latitude/longitude per site | DMS whole-second ≈ 31 m | public PDF via Bhusanket URL pattern; **on disk** (INV-06, VERIFIED) | REPORT with **single-event** Wayanad datasheet (Mundakkai); FIR names 4 locations — no multi-event Wayanad table exists in the volume | `data/interim/gsi_pdf_text/gsi_PDLS_2024_51817.txt` (L226, L258, L268–269, L3245, L3257, L3281–3282) |
| C | GSI PDLS 2025 (acc. 61074) | GSI | FS 2024-25 events incl. Meenakshi Bridge June 2024 | Kerala | same 42-point datasheet format | DMS ≈ 31 m | public PDF; on disk (INV-07, VERIFIED) | REPORT with single-event datasheet (June 2024 event, already in inventory) | `docs/data_sources.md` §1.9 |
| D | KSDMA "Reports – Landslides 2024" page set | Kerala State Disaster Management Authority | July 2024 Meppadi (Chooralmala–Mundakkai) | Wayanad (+1 Kozhikode item) | page hosts **exactly 4 documents** (links enumerated live) | n/a | public web page, no auth | PORTAL — see D1–D4; **no geospatial inventory among them** | `official_sources_probe.json` (candidate_links), round-1 probe log |
| D1 | Memorandum — Meppadi landslide 2024 (`Memorandum_17082024.pdf`) | Govt. of Kerala (DMD) | 30 July 2024 event | Meppadi GP, Wayanad | narrative: event timing, rainfall, impact | none | public PDF; **on disk** (INV-10) | REPORT (disaster discussion) | `docs/data_sources.md` §1.9 |
| D2 | Meppadi Landslide PDNA 2024 (`Meppadi-Landslide-PDNA_final...pdf`) | KSDMA → Govt. of India | July 2024 event + recovery | Wayanad | recovery/needs narrative; mentions "providing the Geocoordinates of the site" (extract L2709) in the context of works — **no geocoded location table** | none | public PDF; on disk (INV-09) | REPORT (recovery/needs assessment) | `data/interim/gsi_pdf_text/ksdma_meppadi_pdna_2024.txt` (L2709; pattern scan: no coordinate/latitude/longitude table structures) |
| D3 | "Meeting the Essential SRH Needs of Communities Affected by Landslides – Wayanad, Kerala Response, India – 2025" (`FPS2025.pdf`) | implementer: Family Planning Association India (hosted by KSDMA) | response period from 26 Aug 2024 | Wayanad affected communities | SRH services narrative | **none found** (latitude/longitude/GPS/survey-number/inventory/annexure = 0; 'coordinate' ×2 in prose) | public PDF, 8.4 MB, 17 pp (p.17 image-only cover) | **REPORT** (health-sector response report) — retrieved as review evidence only | `ksdma_documents_assessment.json`, `ksdma_documents_deepscan.json`; PDF saved to evidence dir (git-excluded) |
| D4 | 15th Kerala Legislative Assembly, Committee on Environment (2023–2026), **13th Report — "Wayanad Landslide 2024 – Independent study report"** (`Environment-Committee-2025.pdf`) | Kerala Legislative Assembly (independent study) | covers July 2024 Chooralmala–Mundakkai (Wayanad) **and** Vilangad (Kozhikode) | 2 districts | Malayalam; committee findings/recommendations | **none found** (EN and ML patterns — അക്ഷാംശം/രേഖാംശം/സർവേ നമ്പർ/വാർഡ്/ഇൻവെന്ററി/പട്ടിക — all 0; no image-only pages, so no hidden tables) | public PDF, 0.5 MB, 47 pp | **REPORT** (legislative independent study/discussion) — retrieved as review evidence only | `ksdma_documents_assessment.json`, `ksdma_documents_deepscan.json` |
| E | KSDMA Hazard Maps page — landslide section | KSDMA (hosts GSI product) | **GSI 2022 LSZ only** (uploaded 2025-08) | all Kerala districts | shapefile zips per district + summary PDF | polygon zones, not events | public | PORTAL/NEGATIVE — the only landslide geodata offered is susceptibility zoning (LSZ-01, already on disk); **no post-2024 Wayanad LSZ update, no inventory** | `official_sources_probe_round5.json` (`zip_links`: `/wp-content/uploads/2025/08/Wayanad.zip`; section heading "Landslide Susceptibility zones of District of Kerala (GSI, 2022)- Shape files") |
| F | KSDMA Event Specific Maps page | KSDMA | 2013–2020 events | Kerala | event map PDFs | maps (not records) | public | PORTAL/NEGATIVE — **no 2024 event map** (latest = 2020) | `official_sources_probe.json` (round-1 links: Flood-Inundation-Map_2020 … FLOOD_INUNDATION2013) |
| G | KSDMA `/landslides-2024/`, `/event-2024-2/`, `/meppadi-2024-csr/`, `/maps-2/` pages | KSDMA | 2024 events (news/reports) | Kerala | page link scans found only menus, event reports (conferences, DM plans, mock drills), no Wayanad-2024 PDFs beyond D1–D4 | n/a | public | PORTAL/NEGATIVE — link scan found no geospatial inventory documents | `official_sources_probe_round2.json` |
| H | Kerala DM Suite (`dmsuite.kerala.gov.in`) | Govt. of Kerala / Wayanad DDMA | continuous (rainfall ops) | Wayanad district | rainfall collection from plantation gauges interpolated to LSGs; resource management; DM clubs (per PDNA §1.7) | none | public; reachable (HTTP 200) | PORTAL/NEGATIVE — a DRR *operations* portal, not an event inventory | round-2 probe; PDNA extract L3515 ff. |
| I | Wayanad district / DDMA site (`wayanad.gov.in`, incl. `/en/dm-orders/`, `/en/disaster-management-2/`) | Wayanad DDMA (district administration) | DM orders 2020–2026 (monsoon prep, dam operations, soil-excavation ban) | Wayanad | government orders (PDFs) | none | public | PORTAL/NEGATIVE — administrative orders only; **no 2024 landslide orders, reports or inventory visible** on the DM pages | `official_sources_probe_round4.json` (`wayanad_dm_orders`, `wayanad_disaster_page`) |
| J | NDMA landslide resources (`ndma.gov.in`) | NDMA, Govt. of India | **Landslide Atlas 2023** (pre-dates July 2024) | national | atlas PDF, 60 MB | unknown (not downloaded — cannot contain the 2024 events by its date) | public direct download | PORTAL/NEGATIVE — `Landslide_Atlas_2023.pdf` (Download, 60 MB); the "Landslide (42.5 MB)" resources page exposes **no dataset link** (awareness material, empty content area); guidelines pages only | round-3/4 probes; `ndma_landslide_pages_log.txt`, `ndma_425mb_full_log.txt` |
| K | Copernicus Emergency Management Service (rapid mapping activations) | European Commission (CEMS) | activations 2012–2026 | global (requestor states) | activation catalogue: code, title, date, event type, country; products = footprint **maps** | n/a (maps, not records) | public portal + public activations API | **VERIFIED NEGATIVE** — see §3: no Wayanad activation exists; India has exactly 5 activations ever (2013–2019, cyclones/floods, none landslide); Kerala all-time = 0 | `cems_api_*.json`, `cems_api_log.txt`, `cems_india_details_log.txt` |
| L | NRSC / ISRO Bhuvan landslide atlas (`bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=ls`) | NRSC (ISRO) | interactive atlas (JS application) | national | interactive layers; static probe exposes no downloadable Wayanad-2024 inventory | unknown | public; wrapper page HTTP 200 (33 KB); app is JS-only | PORTAL — not enumerable by static probing this session; **unresolved detail**: any NRSC post-event Wayanad-2024 assessment could not be located (websearch unavailable; see §4) | round-1/2 probes (`nrsc_bhuvan_landslide_atlas`) |
| M | GSI Bhukosh (`bhukosh.gsi.gov.in`) | GSI | national datasets | national | n/a | n/a | public when reachable | **UNREACHABLE** — TCP connect timeout 2026-10-29 (consistent with the standing ACCESS_RESTRICTED record in `docs/data_manifest.csv` GEO-02) | round-1 probe log |
| N | GSI main portal (`www.gsi.gov.in`) | GSI | — | national | landing page | n/a | public, HTTP 200 | PORTAL — GSI's Wayanad-2024 public products remain the PDLS volumes (B/C); no separate Wayanad-2024 inventory publication found | round-1 probe log |
| O | NIDM (`nidm.gov.in`) | National Institute of Disaster Management | — | national | n/a | n/a | **UNREACHABLE** — TLS certificate hostname mismatch | UNREACHABLE — recorded failure mode only | round-1 probe log |
| P | UNOSAT (UNITAR) | UNOSAT | — | global | map catalogue (JS application) | maps (not records) | public | NOT PROBED this session — websearch unavailable and the catalogue is JS-only; products would be maps, not inventories, in any case | — (handoff item for a future run) |

Also verified this run: `data/raw/landslide_inventory/ksdma/ksdma_go_ms6_dmd_gsi.pdf` is a **2-page image-only scan** (0 extractable characters, 1 image per page) — this explains the 44-byte text extract from the earlier phase; it is a government-order scan, not an inventory, and cannot be text-verified without OCR (not performed).

## 3. Verified negative: Copernicus EMS has no Wayanad activation

Method (all steps scripted; evidence saved):

1. Legacy URL `emergency.copernicus.eu/mapping/list-of-activations-rapid` (+ no-slash, `/mapping`, `list-of-activations` variants) — **404** for all; the portal has migrated to `mapping.emergency.copernicus.eu`.
2. New portal's activations page is a JS application (React bundle on `cems-mapping-website.s3.amazonaws.com`); its grid exports only the loaded page. Its **public data API** was identified from the browser's network log: `https://mapping.emergency.copernicus.eu/activations/api/activations/`.
3. API queries (HTTP 200, JSON):
   - `q=Wayanad` (all time) → **count 0**
   - `q=Kerala` (all time) → **count 0**
   - `q=India` → 5 activations; details fetched: EMSR049 *Floods in Uttarakhand state – India* (2013), EMSR054/EMSR057 *Tropical Storm in India* (2013), EMSR104 *Flood in Andhra Pradesh – India* (2014), EMSR357 *Tropical Cyclone Fani in Eastern India* (2019) — **none landslide, none 2024**
   - positive controls prove the filters work: `q=Nepal` → 3, `q=landslide` → 30 (activations titled "landslide" exist — in other countries)
4. Conclusion: **no CEMS rapid-mapping activation exists for the July 2024 Wayanad landslides** (nor for Kerala, nor for any Indian landslide). Even if one had existed, CEMS products are satellite-derived footprint/damage **maps** — under this project's rules they would be a candidate to *classify*, never a source of records without authorized digitization.

## 4. Unresolved access issues (exact failure modes recorded)

| Item | Failure (2026-10-29) | Note |
|---|---|---|
| Bhusanket live catalogue | TCP connect timeout (requests, 40 s) + webfetch transport error; third probe same | was reachable 2026-10-25; the on-disk 1,188-report index (last verified catalogue state) shows no Wayanad-2024 entry; anything published after 2026-10-25 is unverifiable until the host responds again |
| Bhukosh | TCP connect timeout (40 s) | consistent with standing GEO-02 ACCESS_RESTRICTED status |
| NIDM | TLS `CERTIFICATE_VERIFY_FAILED` (hostname mismatch) | host-level misconfiguration, not credentials |
| Copernicus legacy URLs | HTTP 404 (9678-byte custom error body) | portal migrated to `mapping.emergency.copernicus.eu` |
| Websearch integration | returned "No search results found" for every query incl. trivial controls | search-assisted discovery unavailable this session; all findings above come from direct fetches of known official hosts |
| NRSC Bhuvan landslide atlas; UNOSAT | JS-only applications; not enumerable by static probing | interactive enumeration (or a future authorized browser session) needed; would still be *maps/portals*, not record tables |
| `ksdma_go_ms6_dmd_gsi.pdf` | image-only scan (2 pp, 0 chars) | OCR not performed (out of scope) |

## 5. What this means (interpretation — clearly separated from measurement)

- The measured facts (§2–§4) say: **no publicly accessible official multi-event geospatial inventory of the July 2024 Wayanad disaster exists today** — or at minimum none is reachable from this environment without interactive portals.
- The inventory's 2024 coverage therefore remains: **two single-event point records** (GSI PDLS datasheets), which is what the best official products (PDLS volumes) themselves contain. The FIR's four named incidence locations are prose statements, not records.
- Paths that could change this picture, each requiring **explicit user authorization** (none taken this run):
  1. Re-probe Bhusanket/Bhukosh when reachable and re-diff the catalogue against the on-disk index (script exists: `scripts/review_bhusanket_index_2024.py`).
  2. Interactive enumeration of the NRSC Bhuvan landslide atlas / UNOSAT (browser session).
  3. Non-public official channels: a direct request to GSI/KSDMA/DDMA Wayanad for field datasheets of the Attamalai/Vellarimala/Chooralmala incidences (the PDLS programme collects 42-point datasheets per event; the July 2024 Wayanad set may exist internally without being published).
  4. Derived event mapping from post-event satellite imagery — this would be **new analysis**, must be labelled as derived/synthetic-adjacent per the standing rules, and could never be presented as an official inventory.
- Per the run instruction, **manifest statuses and the existing inventory were not changed.** Candidate additions can happen only at acquisition time, when file-level review and validation are authorized.

## 6. Evidence index (all under `data/interim/inventory_source_review_2026-10-29/` unless noted)

- `bhusanket_index_review.json`, `index_review_log.txt` — on-disk catalogue review + live-refresh failure
- `official_sources_probe.json` / `_round2/3/4/5.json` + matching `*_log.txt` and `*_display.txt` — reachability and link evidence for every portal
- `ksdma_documents_assessment.json` + log — retrieval + first-pass scan of the two new KSDMA documents; `ksdma_documents_deepscan.json` + log — EN+ML pattern scan, image-page check
- `cems_api_*.json`, `cems_api_log.txt`, `cems_india_details_log.txt`, `cems_activations_export.csv` — CEMS API queries, details, positive controls, grid CSV
- `ksdma_fps2025_srh_needs.pdf`, `ksdma_environment_committee_13th_report.pdf` — the two assessed documents (kept local as review evidence; **git-excluded**, like raw data)
- scripts (committed): `scripts/review_bhusanket_index_2024.py`, `scripts/enumerate_bhusanket_kerala.py`, `scripts/probe_official_sources_2024.py` (+`_round2/3/4/5`), `scripts/assess_ksdma_2024_documents.py`, `scripts/scan_ksdma_docs_text.py`, `scripts/query_cems_activations_api.py`, `scripts/cems_india_details.py`, `scripts/fetch_ndma_landslide_pages.py`, `scripts/fetch_ndma_425mb_detail.py`, `scripts/fetch_ndma_425mb_full.py`, `scripts/show_*.py` (display helpers)

## 7. What was deliberately not done (per instructions)

- No download, digitize, merge or alteration of inventory data; no new manifest rows; no status changes; no Phase 4/5 outputs touched.
- The two KSDMA documents were saved **only** as review evidence in the interim directory and scanned for inventory-like structures; no CSV was produced from them; they remain distinct from the inventory.
- No OCR; no interactive JS-portal crawling beyond the one CEMS session; no credentials or tokens sought; no bypass of any access restriction.
