# Run Report RUN-2026-10-30-02 — Independent test, Stage 2: acquisition readiness and intake design

**Date:** 2026-10-30 · **Session goal:** turn the Stage 1 verdict into a route to obtain a real
independent inventory — verify the request package and its contacts, close any field-coverage gap,
document an alternative route, and define the intake and acceptance gates — without acquiring,
sending, merging or scoring anything.
**Starting state:** commit `ba6157c` (RUN-2026-10-30-01 hash pin); tree clean.
**End state:** Stage 2 document + package edits + this report committed (hash in §6); tree clean;
**no dataset acquired, no request sent, no agency contacted, no score computed.**

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | `Get-Date`, `git status --short`, `git log --oneline -4`, list `reports/RUN-2026-10-30-*` | establish date, baseline, next run number, in-progress work | 2026-10-30; HEAD `ba6157c`; clean; one 10-30 report exists → this is `02` |
| 2 | `Get-ChildItem data\raw -Recurse -File` sorted by mtime | check for newly acquired data | newest still `Wayanad.zip`, 2026-10-28 23:27 — **nothing new** |
| 3 | read `AGENTS.md`, `reports/README.md` | conventions + report template | read |
| 4 | read `docs/INDEPENDENT_TEST_FEASIBILITY_AUDIT_2026-10-30.md`, `reports/RUN-2026-10-30-01_…md` | reuse Stage 1 evidence, do not re-derive | reused: 363/2,097, 76 clusters, 0.00 m overlaps |
| 5 | read `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` (§1–§7) and all three `ATTACH_2026-10-29_*` files | verify NOT SENT, placeholders, field coverage | banners intact; 10 fields in §4/annex; 3 gaps found |
| 6 | read `data/interim/inventory_source_review_2026-10-29/contact_sources_2026-10-29.json` | provenance of every contact already in the letter | KSDMA / Wayanad / GSI entries as recorded 2026-10-29 |
| 7 | `python -c` dump of `configs/p4_sampling.json` | exact thresholds for the acceptance gates | `buffer_gap_m: 1000`, `min_test_clusters: 5`, `min_test_positives: 45`, `clustering_threshold_m: 1000`, background `exclusion_radius_m: 100` |
| 8 | `webfetch https://sdma.kerala.gov.in/contact/` | re-verify KSDMA contact (official page only) | HTTP 200; address/phone/email unchanged |
| 9 | `webfetch https://wayanad.gov.in/en/directory/`, `https://wayanad.gov.in/directory/` | re-verify the cited directory page | **HTTP 404 both** — the letter's citation was dead |
| 10 | `webfetch https://wayanad.gov.in/en/whos-who/` | find the live Collector contact page | HTTP 200; `dcwayanad[at]gmail[dot]com`, `04936202230`; footer 14.07.2022 |
| 11 | `webfetch https://wayanad.gov.in/en/contact-us/` | check for a records address | HTTP 200; only the web information manager (`itcellwyd@kerala.gov.in`) — not used |
| 12 | `webfetch https://www.gsi.gov.in/` and `/webcenter/portal/GSI/pages_contactus` | verify GSI contact | JS "Verifying secure session" shell; contact path **404** — still unverifiable |
| 13 | edit `DRAFT…` §4 (fields 11–13), `ATTACH…fields-request-annex.md` (same 3 fields) | close the geometry / grouping / location gap | 13 fields in both; additive only |
| 14 | edit `DRAFT…` §1 header and §1.3 | fix the dead citation, mark mobile/fax unconfirmed, record the 2026-10-30 re-check | 2 edits; no placeholder or claim changed |
| 15 | `python %TEMP%\opencode\check_attachments.py` (extended to 30 checks) | re-verify package consistency after edits | **30/30 PASS** (first run 29/30, see §3) |
| 16 | write `docs/INDEPENDENT_TEST_STAGE2_ACQUISITION_READINESS_2026-10-30.md` | the deliverable | route table, contact log, field matrix, send checklist, intake checklist, gates G1–G10, staged handoff |
| 17 | write this report | run record | — |

No dataset was acquired or opened for scoring. No evaluator was created. No model was run.

## 2. Measured values (do not re-derive)

**Project thresholds reused for the acceptance gates** — `configs/p4_sampling.json`:

| Parameter | Value | Where |
|---|---|---|
| Analysis CRS | EPSG:32643 | `analysis_crs` |
| Spatial buffer between train and test | **1,000 m** | `spatial_validation.buffer_gap_m` |
| Clustering threshold | **1,000 m** single linkage | `spatial_validation.clustering_threshold_m` |
| Minimum test clusters | **5** | `spatial_validation.min_test_clusters` |
| Minimum test positives | **45** | `spatial_validation.min_test_positives` |
| Background exclusion radius | 100 m | `background.exclusion_radius_m` |
| Background density | 1.0 / km² | `background.sampling_density_per_km2` |
| Folds | 5 | `spatial_validation.n_folds` |

These are the numbers the gates use; **none was changed**.

**Contact re-check, 2026-10-30 (official pages only):**

| Agency | Page | Result |
|---|---|---|
| KSDMA | `https://sdma.kerala.gov.in/contact/` | HTTP 200; `+91-471-2778855`, `keralasdma@gmail.com`, Observatory Hills address — **unchanged** |
| Wayanad Collector | `https://wayanad.gov.in/en/whos-who/` | HTTP 200; `dcwayanad[at]gmail[dot]com`, `04936202230` — **confirmed**; page dated 14.07.2022 |
| Wayanad `/directory/` | both English and Malayalam | **404** — the letter's old citation was dead |
| GSI | `https://www.gsi.gov.in/` | JS session shell, no content; contact path 404 |

**Field coverage after the edits:** 13 fields in both the letter §4 and attachment 3, covering
coordinates, event dates, identifiers, **geometry type and what the point represents**, CRS,
precision/uncertainty, provenance, access, citation, **event grouping**, and **administrative
location**.

**Package state:** letter + 3 attachments; all four carry `STATUS: … NOT SENT`; placeholders intact;
no reply; no new data.

## 3. Bugs caught and fixes

1. **Dead citation in the package.** The letter cited `wayanad.gov.in → Directory`, which now returns
   404 on both language sites. Fix: replaced with the live Who's Who URL, fetched 2026-10-30, and
   corrected the page-date caveat (14.07.2022, not 20.12.2021). Contact data itself was not changed.
2. **Two unconfirmed numbers presented as confirmed.** The DDMA mobile `9447204666` and fax
   `04936-203450` are not on the Who's Who page. Fix: marked unconfirmed inline in the address block
   and in the source note; the user decides whether to drop them.
3. **Real field-coverage gap.** Neither the letter §4 nor attachment 3 asked for geometry type / what
   the point represents, event grouping, or administrative location. Geometry matters because the
   Phase 5 labels are source-area points, and a runout centroid is a different entity. Fix: fields
   11–13 added to both documents (additive; no renumbering of 1–10).
4. **Check-script false failure (29/30).** The new assertion counted `^| n |` rows across the whole
   letter, which also matches the recipient and tracker tables. Fix: scoped the count to the text
   between `## 4. Fields requested` and `## 5.` → 30/30. A defect in the check, not the package.
5. **Typo caught before commit.** "Meikshshi Bridge" in the staged-handoff section of the new document;
   corrected to "Meenakshi Bridge".
6. **GSI site unreachable (blocker, not a bug).** `gsi.gov.in` returns a session-verification shell and
   the contact path 404s, matching the three failures on 2026-10-29. Not worked around; recorded as the
   one hard blocker besides the user's identity block.

## 4. Verification and gates

| Check | Result |
|---|---|
| Attachment/package consistency script | **30/30 PASS** — 2 IDs only; DMS→decimal conversions; page refs; precision statements; `SOURCE_CONFIRMED` ×2; no `CORROBORATED` claim on the GSI row; prose-only framing; placeholders in all three files; NOT SENT ×3; letter links all three; **13 fields in both documents**; geometry + grouping present |
| NOT SENT status | verified from the four files themselves, not from the reports |
| New data check | `data/raw` newest file 2026-10-28 23:27 — none |
| `git diff --check` | run at staging |
| Phase 2/3/4/5 gates | **not run** — no Phase 2–5 product, documentation claim, config or output was touched; only `docs/requests/*` and a new `docs/` file changed. Re-running them would add timing churn to `data/interim/p3/verify_all.json` without testing anything this run changed |
| Model evaluation | **none** — no evaluator, no score, no metric |

**Explicit negative result:** no independent dataset exists, so no external test result exists. Nothing
in this run could be read as evidence that the model generalises outside its training inventory.

## 5. Outputs produced or changed

| File | Status | Contents |
|---|---|---|
| `docs/INDEPENDENT_TEST_STAGE2_ACQUISITION_READINESS_2026-10-30.md` | **new** | 6-route status table; contact log; field-coverage matrix; send-readiness checklist (user-only fields marked); 12-step intake checklist; gates G1–G10 with thresholds; staged handoff (a)–(d); guard rails; evidence index |
| `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` | **modified** | §4 fields 11–13; §1 header provenance; §1.3 live citation + unconfirmed mobile/fax marked |
| `docs/requests/ATTACH_2026-10-29_fields-request-annex.md` | **modified** | fields 11–13 with reasons |
| `reports/RUN-2026-10-30-02_acquisition-readiness-and-intake-design.md` | **new** | This report |
| `%TEMP%\opencode\check_attachments.py` | temp only | extended 28 → 30 checks; not in the repo |

No inventory, manifest, Phase 4 data, Phase 5 configuration, model or output was modified.

## 6. Current project state

- **Independent test:** not possible yet; no dataset acquired; no evaluation performed.
- **Request package:** complete in content, still **NOT SENT**, placeholders intact. One hard blocker
  (GSI contact unverifiable through this fetcher) plus the user's identity block.
- **Phase 5:** unchanged — fixed Random Forest, 5 folds, per-fold ranking metrics as documented.
- **Phase 4 / inventory / manifest:** unchanged.
- Commit: `<pending — pinned in the follow-up commit>`.

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Fill the identity/contact block (name, designation, institution, city, postal address, email,
     phone, optional ORCID) and the date/reference fields.
  2. Choose the enclosure: full held-record annex (includes our internal §3/§6 notes) or only its §2
     table; and whether to include the Meenakshi Bridge record at all (June-2024 road cut, not the
     30 July event).
  3. Decide whether to drop the unconfirmed DDMA mobile/fax.
  4. Obtain the GSI addressee details through a normal browser session, or choose the RTI route.
  5. Recipient order and send date; log it in the letter's §7 and diary +21 days.
- **What the next step must do / must not do:**
  - Do **not** claim the request was sent until a dated tracker row and a sent copy exist.
  - Do **not** acquire, merge or score anything before the gates in Stage 2 §8 are applied.
  - Do **not** lower the 5-cluster / 45-positive minimums or reuse the 2,097 training background points.
  - Do **not** treat the 2024, 2019, undated or 2006–2009 records as test data — they are training
    labels or unusable (Stage 1 §4).
  - Do **not** invent a GSI email, officer name or fee; take them from the official page at send time.
- **Quick commands:**
  - `python %TEMP%\opencode\check_attachments.py` (30 package checks)
  - `python -c "import json;d=json.load(open('configs/p4_sampling.json'));print(d['spatial_validation']['buffer_gap_m'], d['spatial_validation']['min_test_clusters'], d['spatial_validation']['min_test_positives'])"`
  - `Get-ChildItem data\raw -Recurse -File | Sort-Object LastWriteTime -Descending | Select-Object -First 3`
  - `git log --oneline -3`, `git status --short`
- **Do not re-derive:** 1,000 m buffer; 1,000 m clustering; **5** clusters; **45** positives; 100 m
  background exclusion; 1 point/km²; 363 positives / 2,097 background / 76 clusters; 2024 = 2 groups in
  fold 3 at 0.00 m; KSDMA contact confirmed 2026-10-30; Wayanad email/landline confirmed, mobile/fax
  not; GSI contact unverifiable; package NOT SENT with no reply; no new data since 2026-10-28.
