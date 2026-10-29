# Run Report RUN-2026-10-29-12 — Request attachments: project note, held-record annex, fields annex

**Date:** 2026-10-29 · **Session goal:** prepare the three remaining attachments for the official
records request — a one-page project note, a held-record annex for the two GSI PDLS Wayanad records,
and a clean fields-request annex — for user review only; nothing sent, no agency contacted, no
inventory or model change.
**Starting state:** commit `8f316d2` (RUN-11 hash pin); tree clean.
**End state:** work + this report committed (hash pinned in §6); `verify_all.json` timing churn
reverted; tree clean; nothing pushed. **The package is not ready to send** — user placeholders and
agency contacts still need review (§7).

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | read `AGENTS.md`, `reports/README.md` | conventions and report template | read |
| 2 | read `reports/RUN-2026-10-29-11_…`, `docs/requests/DRAFT_2026-10-29_…`, `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md`, `docs/INVENTORY_VERIFICATION_REPORT.md` | establish what the letter promises and what the attachments must contain | read; letter §6 listed all three attachments as not yet drafted |
| 3 | `python` dump of `inventory_gsi_pdls_wayanad.csv` | exact field values for the annex | 2 rows, all columns inspected (IDs, printed coordinate text, precision, pages, history) |
| 4 | `python` dump of `inventory_source_records.csv` rows with `source_id = GSI_PDLS` | verification status, source file paths, event-group IDs | 2 rows; both `SOURCE_CONFIRMED`; event groups `EV-2024-MUNDAKKAI`, `EV-2024-MEENAKSHI-BRIDGE` |
| 5 | `python` dump of event group `EV-2024-MUNDAKKAI` | check where `CORROBORATED` actually sits | it sits on `LIT2025` (Sreekumar et al. 2025), **not** on the GSI datasheet |
| 6 | `Select-String` / `python` on `gsi_PDLS_2024_51817.txt` L3345–3402 | confirm printed datasheet fields, whole-second coordinate, absent field 41, page boundary | fields 1–39 only; `11027�46�` / `76008�03�`; page 96 marker at L3378 |
| 7 | `Select-String` on `gsi_PDLS_2025_61074.txt` | confirm printed coordinate and reporting date | L2660 `11�31'15.67"`, L2730 `21.05.2025` |
| 8 | write `docs/requests/ATTACH_2026-10-29_project-note.md` | attachment 1 | 617 body words, 7 sections, 8 placeholders |
| 9 | write `docs/requests/ATTACH_2026-10-29_held-record-annex.md` | attachment 2 | 2-record comparison table, status table, prose-name section, provenance, internal note |
| 10 | write `docs/requests/ATTACH_2026-10-29_fields-request-annex.md` | attachment 3 | 10-field table + 5 notes, one page |
| 11 | edit letter §2 Enclosures and §6 checklist | point at the real files, remove `[TO WRITE]` | 2 edits |
| 12 | `python` consistency script (temp, `%TEMP%\opencode\check_attachments.py`) | verify annex values against CSV, prose-name confinement, placeholder presence | **28/28 checks pass** (after two check-logic refinements, §3) |
| 13 | `python scripts/p2_check_consistency.py` | Phase 2 gate | exit 0 — all consistency checks passed |
| 14 | `python scripts/p3_check_consistency.py` | Phase 3 gate | exit 0 — 470 checks, ALL PASSED |
| 15 | `python scripts/p4_check_consistency.py` | Phase 4 gate | exit 0 — all Phase 4 consistency checks passed |
| 16 | `python scripts/p4_verify.py` | Phase 4 regeneration gate | exit 0 — 8/8 gates, 9 outputs byte-identical |
| 17 | `git checkout -- data/interim/p3/verify_all.json` | drop recurring timing churn | clean before staging |

## 2. Measured values (do not re-derive)

**Held records (from `data/interim/inventory_extracts/inventory_gsi_pdls_wayanad.csv`):**

| Item | 2024 record | 2025 record |
|---|---|---|
| ID | `KER/WYD/58A03/2024/01` | `KER/WYD/58A03/2025/01` |
| Page | 95 (table continues p. 96) | 80 |
| Printed lat/lon | `11027'46"N` / `76008'03"E` (degree glyph absent) | `11A°31'15.67"` / `76' 08' 8.34"` (glyphs degraded) |
| Decimal | 11.462778 / 76.134167 | 11.521019 / 76.13565 |
| Printed precision | whole second ≈ 31 m | 0.01″ ≈ 0.3 m |
| Event date | 1:00 AM 30.07.2024 | June 2024 (reported 21.05.2025) |
| Status | `SOURCE_CONFIRMED` | `SOURCE_CONFIRMED` |

**Conversion check (recomputed from printed DMS, not copied):** 11°27′46″ → 11.462778;
76°08′03″ → 76.134167; 11°31′15.67″ → 11.521019; 76°08′8.34″ → 76.13565. All four agree with the
stored decimals to < 1e-6. Exact match on the first three; the fourth rounds at the 5th decimal
(76.135650 vs stored `76.13565`).

**Cross-document facts reused, not re-measured:** 468 source records / 8 sources; 2,121.0 km² GADM
boundary; 495 m corroboration separation; 1.98 km / 4.91 km to the two settlements; `CORROBORATED`
applies to `LIT2025`, not to the GSI record.

**Gate numbers:** p2 all-pass; p3 470 checks; p4 all-pass; p4_verify 8/8 gates, 9 outputs
byte-identical.

## 3. Bugs caught and fixes

1. **Precision metadata discrepancy (found, deliberately not fixed).** `coord_precision_deg` stores
   `2.778e-06` (0.01″ ≈ 0.31 m) for **both** PDLS rows because
   `scripts/p2_parse_gsi_datasheets.py` hard-codes `round(0.01 / 3600, 9)` at L85 and L131. The 2024
   datasheet prints **whole seconds**, so that column overstates the supported precision by ~100×.
   The stored decimal coordinate is unaffected, and `docs/INVENTORY_VERIFICATION_REPORT.md` §4 and the
   covering letter already say "whole second ≈ 31 m". Fix: the annex states the printed precision and
   records the discrepancy in a **do-not-enclose** internal note. Correcting the CSV would alter a
   Phase 2 product protected by `p3_verify_phase2_untouched.py` and is a user decision.
2. **`CORROBORATED` mis-attribution risk.** The verification report's summary line can be read as if
   the GSI datasheet were `CORROBORATED`. The record table shows the status sits on the `LIT2025` row,
   with the two in one event group at 495 m. Fix: the annex's §3 says this explicitly, so the letter's
   enclosure cannot overclaim.
3. **PowerShell quoting failure.** `python -c "…"` with escaped quotes and backslashes was mangled by
   the shell (`ScriptBlock should only be specified as a value of the Command parameter`). Fix: wrote
   the check as a temp `.py` file and ran it; no repo file involved.
4. **Two over-strict check assertions.** The first draft counted `KER/WYD/` occurrences and expected
   2; the IDs legitimately appear twice each (data table + status table), so it failed at 27/28. Fix:
   compared **distinct** IDs to the CSV set (and later to the same set again), giving 28/28. This was
   a defect in the check, not in the annex.
5. **`verify_all.json` timing churn (fourth consecutive run).** Reappeared after the p3 gate; reverted
   immediately before staging, as in RUN-10/11.

## 4. Verification and gates

| Check | Result |
|---|---|
| Attachment consistency script | **28/28 PASS** — 2 IDs only; DMS→decimal conversions; page refs; precision statements; `SOURCE_CONFIRMED` ×2; no `CORROBORATED` claim on the GSI row; prose-only framing; placeholders present in all three files; NOT SENT banner ×3; letter points at all three files |
| Prose-name confinement | `Attamalai` and `Vellarimala` occur **only** in annex §4; `Chooralmala`/`Mundakkai` also occur as the datasheet's own slide name/locality, never as separate records |
| `p2_check_consistency.py` | PASS |
| `p3_check_consistency.py` | PASS — 470/470 |
| `p4_check_consistency.py` | PASS |
| `p4_verify.py` | PASS — 8/8 gates |
| `p5_verify.py` | not run (docs-only change; no Phase 5 artefact touched) |
| `git diff --check` | run at staging — clean |

**No request was sent, no agency contacted, no network access at all this run.** No manifest row,
inventory product, Phase 4 output or Phase 5 artefact was modified (`git status` shows only the three
new attachment files, the letter edit, and the reverted churn).

## 5. Outputs produced or changed

| File | Status | Contents |
|---|---|---|
| `docs/requests/ATTACH_2026-10-29_project-note.md` | **new** | One-page note: purpose, scope table, intended use, 8 safeguards, what the project does not do, data handling, contact block. 617 body words |
| `docs/requests/ATTACH_2026-10-29_held-record-annex.md` | **new** | Scope statement; 2-record comparison table (IDs, pages, printed and decimal coordinates, precision, dates, dimensions, mechanism, deaths); missing fields preserved; status table; prose-name section; provenance table; internal do-not-enclose note |
| `docs/requests/ATTACH_2026-10-29_fields-request-annex.md` | **new** | Clean 10-field request table + notes (formats, partial answers, no personal data, restricted fields, use) |
| `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` | **modified** | Enclosures now name the three files; §6 checklist points at them instead of `[TO WRITE]` |
| `reports/RUN-2026-10-29-12_request-attachments.md` | **new** | This report |
| `data/interim/p3/verify_all.json` | reverted | timing churn dropped |

**Placeholders left visible for the user** (all bracketed): `[RECIPIENT]`, `[DATE]`, `[NAME]`,
`[DESIGNATION]`, `[INSTITUTION / DEPARTMENT]`, `[POSTAL ADDRESS]`, `[EMAIL]`, `[PHONE]`,
`[ORCID … optional]`, `[REQUEST REFERENCE — to be completed on sending]`.

## 6. Current project state

- Phase 5 unchanged: no model, metric, map or output read or written.
- Phase 4 inventory unchanged: 468 source records, two 2024 records, no additions.
- `docs/data_manifest.csv` unchanged (44 rows); no dataset status changed.
- Request package: **letter + 3 attachments exist and are internally consistent**, but the package is
  **not ready to send**. It needs (a) every user placeholder filled, (b) current agency contacts
  re-verified, (c) the user's send decision.
- Commit: `<pending — pinned in the follow-up commit>`.

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Fill the personal/institutional placeholders in all four files (one identity block, repeated).
  2. Re-verify KSDMA and Wayanad contacts, and decide the GSI route (published contact via a human
     browser, or RTI) — unchanged from RUN-11.
  3. Whether to enclose the full held-record annex (it contains internal status and corroboration
     notes) or only its §2 table. If only §2, cut §3 and §6.
  4. Whether to correct `coord_precision_deg` for the 2024 row. It is a Phase 2 product; correcting
     it requires re-baselining the Phase 2 protection gate. **Not done.**
  5. Sending order and timing (recommendation still GSI + KSDMA, then DDMA).
- **What the next step must do / must not do:**
  - Do **not** describe the package as ready to send until placeholders and contacts are reviewed.
  - Do **not** add a third record or a derived coordinate; the annex is exactly the two held records.
  - Do **not** present Chooralmala/Mundakkai/Attamalai/Vellarimala as four records — the annex's §4
    keeps them as prose names, and the check enforces confinement of the two unused names.
  - Do **not** paste any reply into the inventory; a reply becomes a new source through the normal
    acquisition → validation → manifest route.
  - Do **not** describe the project as forecasting, warning or early-warning.
- **Quick commands:**
  - `python %TEMP%\opencode\check_attachments.py` (re-run the 28 checks; the file is a temp helper,
    not part of the repo — recreate from §4 if missing)
  - `python scripts/p2_check_consistency.py && python scripts/p3_check_consistency.py && python scripts/p4_check_consistency.py`
  - `git diff --check`
  - `python -c "import csv;print(list(csv.DictReader(open('data/interim/inventory_extracts/inventory_gsi_pdls_wayanad.csv',encoding='utf-8'))))"`
- **Do not re-derive:** the two IDs and their pages (95/96 and 80); printed coordinates and their
  decimal conversions; 31 m vs 0.3 m printed precision; `SOURCE_CONFIRMED` on both PDLS rows with
  `CORROBORATED` on `LIT2025`; 495 m / 1.98 km / 4.91 km; 468 records / 8 sources; 2,121.0 km².
