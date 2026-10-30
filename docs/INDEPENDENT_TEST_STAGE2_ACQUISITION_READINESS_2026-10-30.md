# Independent real-data test — Stage 2: acquisition readiness and intake design

**Date:** 2026-10-30 · **Run:** RUN-2026-10-30-02 · **Type:** acquisition-readiness and intake design.
**No dataset has been acquired. No request has been sent. No agency has been contacted. The model has
not been evaluated on any record outside its training set, and no validation result exists.**

This document turns the Stage 1 verdict ("no local independent dataset") into a route to get one, a
checklist for what arrives, and objective gates that decide whether it can support an independent
test. Stage 1 (`docs/INDEPENDENT_TEST_FEASIBILITY_AUDIT_2026-10-30.md`) remains authoritative: 363
training positives, 2,097 background, 76 clusters, every usable 2000–2026 event already labelled.

---

## 1. What changed since RUN-2026-10-30-01

| Check | Result |
|---|---|
| Git state | clean at `ba6157c` (RUN-01 pin); no uncommitted work in progress |
| New files under `data/raw` | **none** — newest is still `data/raw/landslide_susceptibility_reference/Wayanad.zip`, 2026-10-28 23:27 |
| New files in `docs/requests/` | none; letter and three attachments unchanged except the additive edits in §2.4 |
| Request status | **still NOT SENT** — all four files carry the banner; no reply, no acknowledgement, no dataset |
| Stage 1 findings | reused, not re-derived |

Nothing appeared that would change the Stage 1 verdict. The audit was not repeated.

---

## 2. Acquisition routes — status table

| # | Route | Current status | Blockers | Next action | Evidence path |
|---|---|---|---|---|---|
| 1 | **GSI letter (primary)** — Director General, GSI Kolkata | Draft complete, **NOT SENT** | (a) user identity/contact placeholders; (b) GSI email, phone and street address are **still unconfirmed** — `gsi.gov.in` returns a JS "Verifying secure session" shell and the contact path 404s (checked 2026-10-30); (c) enclosure choice (full held-record annex vs its §2 table only); (d) send decision | User fills the identity block and obtains the GSI contact through a normal browser session, or uses route 4 | `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` §1.1, §2; §3 below |
| 2 | **KSDMA letter (variant)** | Draft complete, **NOT SENT** | user identity/contact placeholders only — KSDMA contact **re-verified 2026-10-30** | User may send in parallel with GSI (different tier, not duplicates) | `DRAFT…` §1.2, §3.1; §3 below |
| 3 | **Wayanad DDMA letter (variant)** | Draft complete, **NOT SENT** | user identity/contact placeholders; Collector email + landline confirmed 2026-10-30, but mobile/fax unconfirmed and the old `/directory/` URL now 404s | User decides whether to keep the unconfirmed mobile/fax (recommend dropping them); send after GSI/KSDMA so redirections can be reflected | `DRAFT…` §1.3, §3.2; §3 below |
| 4 | **RTI application to GSI** (alternative, statutory) | Not drafted | CPIO address must come from GSI's official RTI page (unreachable through this fetcher); fee and channel must be confirmed at filing | Draft only if route 1 gets no substantive reply within the diary period (suggested +21 days) | §4 below |
| 5 | **Passive publication monitoring** — GSI Bhukosh PDLS index | No new volume since PDLS 2025; nothing local | none — just timing | Re-check the index after the next PDLS publication; a new volume could add Wayanad datasheets | `data/raw/landslide_inventory/gsi_bhusanket/LandslideReport.json` (2026-10-25) |
| 6 | Peer-reviewed supplementary tables | Closed for now | LIT2025 already used (2019 + 2024 records, both in training); no other 2024 Wayanad table found | Re-open only on new evidence | `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md` |

**No route has produced data.** Route 1 is the shortest path and is ready apart from user-only fields.

---

## 3. Contact verification log — checked 2026-10-30

Only official agency pages were opened. Nothing was submitted, emailed or posted.

| Agency | Page fetched | Result | Verdict |
|---|---|---|---|
| KSDMA | `https://sdma.kerala.gov.in/contact/` | HTTP 200. Page prints: "OFFICE OF THE KERALA STATE DISASTER MANAGEMENT AUTHORITY / Observatory Hills, Vikas Bhavan P.O / Thiruvananthapuram, Keralam – 695033 / Phone: +91-471-2778855 / Email: keralasdma@gmail.com" | **Unchanged from 2026-10-29 — confirmed** |
| KSDMA (KSEOC) | same page | `seoc.ksdma@kerala.gov.in`, 1070/1079/0471-2778800 | Confirmed; operations line, still not proposed as addressee |
| Wayanad district | `https://wayanad.gov.in/en/whos-who/` | HTTP 200, footer "Last Updated: 14.07.2022". Prints "DISTRICT MAGISTRATE & DISTRICT COLLECTOR WAYANAD / dcwayanad[at]gmail[dot]com / DISTRICT COLLECTORATE WAYANAD, CIVIL STATION, NORTH KALPETTA P.O / 04936202230" | **Email and landline confirmed**; mobile `9447204666` and fax `04936-203450` are **not** on this page — treat as unconfirmed |
| Wayanad district | `https://wayanad.gov.in/en/directory/` and `https://wayanad.gov.in/directory/` | HTTP **404** on both | The citation in the old §1.3 was dead; replaced with the Who's Who URL |
| Wayanad district | `https://wayanad.gov.in/en/contact-us/` | HTTP 200 — gives only the web information manager (`itcellwyd[at]kerala[dot]gov[dot]in`, 9497713714) | Not a records address; not proposed |
| GSI | `https://www.gsi.gov.in/` | Returns a JavaScript "Verifying secure session" shell with no contact content | **Unverifiable through this fetcher** |
| GSI | `https://www.gsi.gov.in/webcenter/portal/GSI/pages_contactus` | HTTP **404** (same as the three attempts on 2026-10-29) | GSI email/phone/street address remain placeholders |

**Consequence for the package:** the Wayanad section is now cited to a live page, and two of its four
numbers are marked unconfirmed. The GSI section still cannot be completed without a browser session —
this is the single hard blocker to sending, besides the user's own identity block.

---

## 4. Alternative route — RTI application to GSI

If the letter gets no substantive answer, the statutory route is the alternative that does not depend
on goodwill or on a working contact page.

- **Instrument:** Right to Information Act 2005 application to the Central Public Information Officer
  (CPIO) of the Geological Survey of India, Ministry of Mines.
- **What it asks for:** copies of the post-disaster 42-point datasheets and any coordinate table or GIS
  layer for the July 2024 Wayanad sites, held beyond `KER/WYD/58A03/2024/01` — the same question as
  the letter, asked in the statutory form.
- **Why it is viable:** a response is required within **30 days** (48 hours where life or liberty is
  concerned), with a defined first-appeal route. A refusal or "not held" answer is itself a recorded
  result, which the project can cite.
- **What must be confirmed at filing, not invented here:** the CPIO's postal address (published on
  GSI's official RTI page — currently unreachable through this fetcher), the current fee (₹10 for a
  central public authority at the time of writing; confirm), and whether the Ministry of Mines is
  onboarded on the central RTI portal. **No address, officer name or fee is asserted in this document.**
- **Timing:** draft only after the letter's diary date passes without a substantive reply. Filing both
  at once is not recommended — it duplicates the same request through two channels.

A second fallback exists but is a different project, not a shortcut: delineating the 2024 landslides
from pre/post satellite imagery would create a *new* source requiring its own accuracy assessment. It
is recorded here only so it is not mistaken for a quick fix.

---

## 5. Does the request clearly ask for what an independent test needs?

Field-by-field, against the requirement list for a multi-event geospatial inventory:

| Requirement | Letter §2 questions | Fields annex | Status |
|---|---|---|---|
| Multi-event / multi-site inventory | Q1 ("for which sites"), Q2 ("Wayanad subset") | intro ("site-level records") | **covered** |
| Coordinates | Q2, Q4 | 3 | **covered** |
| Event dates | Q5 ("event date and time") | 2 | **covered** |
| Record identifiers | Q5 ("site or record identifier") | 1 | **covered** |
| Spatial geometry / point format | Q2 (point files, GIS layers), Q3 (footprint polygon) | 3 + **11 (added)** | **covered after this run** |
| Coordinate reference system | Q4 | 4 | **covered** |
| Precision / uncertainty | Q4 | 5 | **covered** |
| Source provenance | Q5, Q7 | 8 | **covered** |
| Metadata (attribute fields, access, citation) | Q5, Q7, Q8 | 8, 9, 10 | **covered** |
| Event grouping / duplicates | — | **12 (added)** | **covered after this run** |
| Administrative location | — | **13 (added)** | **covered after this run** |

**Edits made this run (additive only; no placeholder, banner or claim changed):**

1. `DRAFT_2026-10-29_official-inventory-request.md` §4 — fields 11–13 added: geometry type and what the
   point represents; event grouping / duplicate relationships; administrative location.
2. `ATTACH_2026-10-29_fields-request-annex.md` — the same three fields, with the reason each matters.
3. `DRAFT…` §1.3 — the dead `wayanad.gov.in/directory` citation replaced with the live Who's Who URL
   (fetched 2026-10-30), mobile/fax marked unconfirmed, page-date caveat corrected to 14.07.2022.
4. `DRAFT…` §1 header — contact provenance now records the 2026-10-30 re-check.

Field 11 matters most: the Phase 5 labels are **source-area points**. A runout centroid or a deposition
point is a different entity, and the request now asks which one is being supplied.

Consistency check after the edits: **30/30 PASS** (`%TEMP%\opencode\check_attachments.py`, extended
from 28 checks with the 13-field count and the geometry/grouping assertions).

---

## 6. Send-readiness checklist (user-only fields marked **[USER]**)

**A. User-only decisions and fields — cannot be completed by the agent**

- [ ] **[USER]** `[NAME]`, `[DESIGNATION]`, `[INSTITUTION / DEPARTMENT]`, `[CITY]`, `[POSTAL ADDRESS]`,
      `[EMAIL]`, `[PHONE]`, optional `[ORCID …]` — one identity block, repeated in the letter and all
      three attachments.
- [ ] **[USER]** `[DATE]` on the letter and attachments; `[REQUEST REFERENCE]` in attachment 3.
- [ ] **[USER]** Recipient order — recommended GSI + KSDMA in parallel, DDMA after (§1.4 of the letter).
- [ ] **[USER]** Enclosure choice — full held-record annex (contains our internal status notes in §3
      and §6) or only its §2 comparison table. If only §2, cut §3 and §6 before sending.
- [ ] **[USER]** Whether to send the Meenakshi Bridge record as part of the held-record annex. It is a
      90 m² June-2024 road-cut slide in the 2025 volume, not a 30 July 2024 site; including it makes
      the "what we already hold" statement complete, excluding it keeps the annex focused on the event.
- [ ] **[USER]** GSI contact route — browser session to `gsi.gov.in`, or RTI (route 4).
- [ ] **[USER]** Send decision and channel (institutional email recommended; keep the sent copy).
- [ ] **[USER]** Whether to drop the unconfirmed DDMA mobile/fax.

**B. Package checks (agent-verified; re-tick before sending)**

- [x] All four files carry `STATUS: … NOT SENT`; none claims a send.
- [x] No personal information, no invented contact detail, no invented coordinate.
- [x] The letter asks **whether** records exist; it does not assert that unpublished records are known.
- [x] Chooralmala / Mundakkai / Attamalai / Vellarimala are presented only as report-prose names.
- [x] The two held records are exactly `KER/WYD/58A03/2024/01` and `KER/WYD/58A03/2025/01`.
- [x] Field list now covers geometry type, event grouping and administrative location.
- [x] No forecast, warning, prediction or timing language anywhere in the package.
- [ ] Re-check KSDMA and Wayanad pages **on the day of sending** (details change; the Who's Who page is
      dated 14.07.2022).
- [ ] Confirm the GSI addressee block is complete (no bracket left in the address).
- [ ] Single PDF bundle if emailing; subject line exactly as in §2; user's institutional account.
- [ ] Diary the follow-up (+21 days) in §7 the same day the request goes out.

---

## 7. Dataset intake checklist — apply to whatever arrives

Work on a copy. **Never edit an original**, and never merge anything into the project inventory during
intake.

| # | Step | Record |
|---|---|---|
| 1 | **Original source and permission** — who supplied it, on what date, under what stated conditions (licence, citation, redistribution, "research only", "do not publish coordinates") | `transmission.json`: sender, date, reference, verbatim conditions |
| 2 | **File hashes** — SHA-256, size, filename, received timestamp, for every file including shapefile sidecars and any PDF cover note | `files.csv` |
| 3 | **Format and readability** — CSV / XLSX / PDF / SHP / GPKG; open read-only; record layer names, sheet names, page count | `intake_log.md` |
| 4 | **CRS** — declared (`.prj`, GPKG `srs_id`, header) vs detected; if absent record "not stated" and do **not** assume EPSG:4326 | `crs_check.json` |
| 5 | **Coordinate precision and uncertainty** — as printed (DMS string, decimal places, "approx") and as converted; keep both; never round or snap | `records.csv` columns `coord_verbatim`, `lat_dd`, `lon_dd`, `precision_text`, `uncertainty_m` |
| 6 | **Event dates** — as printed, ISO date, certainty (day / month / year / unknown); no inferred dates | `records.csv` |
| 7 | **Record IDs** — the agency's identifier verbatim; any internal ID prefixed with the new source key | `records.csv` |
| 8 | **Geometry type** — point / line / polygon, and what a point marks (source area, centroid, runout start, deposition) | `records.csv` |
| 9 | **Duplicates and event grouping** — crosswalk against the existing 468 records by identifier **and** by distance in EPSG:32643; state the radius used; no silent merges | `crosswalk.csv` |
| 10 | **District coverage** — inside GADM 4.1; boundary-uncertain records flagged with the Phase 4 envelope rule, not dropped silently | `coverage.csv` |
| 11 | **Verification status** — one of `VERIFIED`, `DOWNLOADED_NOT_FULLY_VALIDATED`, `IDENTIFIED_NOT_DOWNLOADED`, `ACCESS_RESTRICTED`, `UNAVAILABLE`, per record and per file | `status.csv` |
| 12 | **Manifest** — only after validation: new row with source URL/reference, acquisition date, licence, limitations | `docs/data_manifest.csv` (separate, later run) |

Intake outputs live in `data/interim/inventory_intake_<YYYY-MM-DD>/` and the original in
`data/raw/<new-source>/`; both are git-excluded like all raw data. Only the intake report is committed.

---

## 8. Acceptance gates — objective, decided before any score

A received dataset is assessed against these gates **in order**, and the outcome is recorded as one of
`ACCEPTED_FOR_PROTOCOL`, `INSUFFICIENT`, `NOT_INDEPENDENT`, `UNUSABLE`. A failure at G4 or G5 is fatal
regardless of size; a failure at G6 cannot be argued away by a better score.

| Gate | Test | Pass condition | Source of the threshold |
|---|---|---|---|
| **G1** Provenance and permission | Source named; access condition recorded; file hash recorded | all three present, or "not stated" recorded explicitly | project convention (verification vocabulary) |
| **G2** Format and CRS | File opens; CRS stated or resolvable; transform to EPSG:32643 reproduces any stated control value | every record has a CRS status | `configs/p4_sampling.json` (`analysis_crs`) |
| **G3** Coordinate sanity | Points fall inside 75.7722–76.4356 E / 11.4427–11.9706 N, or are flagged; no silent correction | no record silently moved | AGENTS.md district extent |
| **G4** Stable-ID independence | Intersection with the 363 training `event_group_id`s and the 468 `source_record_id`s | **zero overlap** | `data/processed/sampling/modelling_points.csv` |
| **G5** Spatial independence | Distance from every candidate point to every one of the 363 training positives, EPSG:32643 | **every point > 1,000 m**; report the minimum | `configs/p4_sampling.json` → `buffer_gap_m: 1000` |
| **G6** Cluster sufficiency | Distinct 1 km single-linkage clusters among candidates | **≥ 5 clusters** (configured minimum — not lowered); target **≥ 15–20**; support target **≥ 45 positives** | `configs/p4_sampling.json` → `min_test_clusters: 5`, `min_test_positives: 45` |
| **G7** Predictor coverage | All 30 m predictor cells valid at every candidate point | zero nodata cells; report any invalid count | `configs/p4_sampling.json` (grid, predictor validity) |
| **G8** Comparison class | Fresh background drawn from the same frame, seed pre-registered, 100 m exclusion around **all** positives (training + candidate), disjoint from the 2,097 training background points | zero overlap with training background by ID or grid cell | `configs/p4_sampling.json` (background rules) |
| **G9** No leakage of excluded records | 2024, 2019, undated and 2006–2009 records excluded by ID | zero of those IDs in the candidate set | Stage 1 audit §4 |
| **G10** Reproducibility | Intake script re-runnable; hashes match; intake JSON committed | byte-identical re-run | project convention |

**Why G6 is not negotiable.** The project already flags fold 2 as marginal at exactly 5 clusters
(84 positives, 5 clusters, ROC-AUC 0.9263 discounted). Two 2024 clusters, or six pre-2000 records, are
below that line and would produce a number nobody could defend.

**What a passed dataset still cannot show.** With a defensible background it supports a
presence–background **ranking** result (ROC-AUC / average precision as ranking measures). It does not
support accuracy, false-positive rate, calibration, or claims about confirmed stable ground, because
the inventory contains no confirmed absences.

---

## 9. Staged handoff

**(a) User reviews, completes and sends — or chooses another route.**
Fill the identity block, pick the enclosure, decide on Meenakshi Bridge inclusion and on the DDMA
mobile/fax, resolve the GSI contact, send GSI + KSDMA. Log the send in the letter's §7 the same day and
diary +21 days. *Verifiable output:* a dated tracker row and a sent copy; until then the package stays
NOT SENT.

**(b) Received data is acquired and validated without altering the original.**
Original into `data/raw/<new-source>/` untouched; intake under §7; gates G1–G3 and G9–G10 applied
first (provenance, format, CRS, sanity, leakage, reproducibility). *Verifiable output:* hashes,
`records.csv`, `crs_check.json`, intake report.

**(c) Only after the data passes G4–G8 is the independent-test protocol prepared and locked.**
Protocol fixes the candidate ID list, the 1,000 m rule, the background seed and drawing rule, the
metrics and their names, the reporting unit, and the wording for a weak result. Hash the protocol
before any scoring. *Verifiable output:* a committed protocol file with its hash and a passing
independence re-check.

**(d) Then implement and run the evaluation and live demonstration.**
Fixed Phase 5 configuration, unchanged; per-group ranking metrics with support and cluster counts
beside them; independence check re-run inside the evaluation script. *Verifiable output:* a reproducible
run whose numbers match a saved artefact.

**Until (c) is complete, there is no evaluator and no score — by design.**

---

## 10. What this run did not do

- Did not acquire, download or receive any dataset.
- Did not send, email, submit or post anything; did not contact any agency.
- Did not score the 2024, 2019, undated, 2006–2009 or any other record.
- Did not create an evaluator, add synthetic data, or produce a metric.
- Did not modify the inventory, the manifest, Phase 4 data, Phase 5 configuration, or any model output.
- Did not lower the 5-cluster minimum or propose reusing the 2,097 training background points.

---

## 11. Evidence index

| Claim | Evidence |
|---|---|
| Stage 1 verdict, training composition, 0.00 m overlaps | `docs/INDEPENDENT_TEST_FEASIBILITY_AUDIT_2026-10-30.md`; `reports/RUN-2026-10-30-01_…md` |
| 1,000 m buffer, 5-cluster and 45-positive minimums, 1 km clustering | `configs/p4_sampling.json` (`spatial_validation`) |
| Package still NOT SENT | `docs/requests/*` banners; `reports/RUN-2026-10-29-11`, `-12` |
| KSDMA contact re-verified | `https://sdma.kerala.gov.in/contact/`, fetched 2026-10-30 |
| Wayanad Collector contact re-verified | `https://wayanad.gov.in/en/whos-who/`, fetched 2026-10-30 |
| GSI contact unverifiable | `https://www.gsi.gov.in/` (JS session shell); `/webcenter/portal/GSI/pages_contactus` → 404 |
| Field-coverage edits and 30/30 check | `DRAFT…` §4, `ATTACH…fields-request-annex.md`; `%TEMP%\opencode\check_attachments.py` |
| No new data | `data/raw` newest file 2026-10-28 23:27; git clean at `ba6157c` |
