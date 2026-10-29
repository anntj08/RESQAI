# Run Report RUN-2026-10-29-11 — Official-inventory request: draft letter to GSI / KSDMA / Wayanad DDMA

**Date:** 2026-10-29 · **Session goal:** produce a reviewable **draft** (not sent) request to GSI,
KSDMA or Wayanad DDMA asking whether additional official geospatial landslide records or PDLS
datasheets exist for the July 2024 Wayanad disaster — drafting only, no contacting, no records.
**Starting state:** commit `1a21042` (RUN-10 complete and hash-pinned); tree carried timing-only
churn in `data/interim/p3/verify_all.json` (six `seconds` fields).
**End state:** work + this report committed (hash pinned in §6); `verify_all.json` churn reverted;
tree clean; nothing pushed; **no draft sent, no agency contacted**.

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | read `AGENTS.md`, `reports/README.md` | standing conventions, report template | read |
| 2 | read `docs/SOURCE_DISCOVERY_2024_WAYANAD_INVENTORY.md`, `reports/RUN-2026-10-29-10_2024-inventory-source-review.md` | establish what RUN-10 already proved and what it handed off | RUN-10 answer stands: no publicly accessible official multi-event inventory; this letter is the sanctioned follow-up |
| 3 | read `docs/INVENTORY_VERIFICATION_REPORT.md` | authoritative record of the 468-record inventory; §6 for the 2024 coordinate facts quoted in the letter | read (482 lines) |
| 4 | `git log --oneline -3`; `git status --short` | baseline | HEAD `1a21042`; one modified file (`verify_all.json`, timing only) |
| 5 | `Select-String` on `ksdma_memorandum_17082024.txt`, `ksdma_meppadi_pdna_2024.txt` for `@`, `0471`, `Phone`, `email`, `Director` | look for contacts inside official texts already on disk | **no agency contact details** in either extract; only internal references (DM Suite URL, email-traffic narrative, `@Rs.` amounts) |
| 6 | `webfetch https://sdma.kerala.gov.in/contact/` | confirm KSDMA published contact | **200** — full address, `+91-471-2778855`, `keralasdma@gmail.com`; KSEOC `seoc.ksdma@kerala.gov.in`, 1070/1079/0471-2778800 |
| 7 | `webfetch https://www.gsi.gov.in/webcenter/portal/GSI/pages_contactus` | GSI contact page | **404** |
| 8 | `webfetch https://www.gsi.gov.in/` | GSI home | 200 but an interstitial "Verifying secure session" shell — **no retrievable contact content** |
| 9 | `webfetch https://wayanad.gov.in/` | DDMA route | 200; homepage publishes helplines only (155300, 1090, 1098, 112, 1091) — **no DDMA mailbox** |
| 10 | `webfetch https://www.gsi.gov.in/contact-us` | GSI contact page (alt path) | **404** |
| 11 | `webfetch https://wayanad.gov.in/<district-directory-page>` | district directory | **200** — District Collector row: `dcwayanad[at]gmail[dot]com`, 9447204666, 04936202230, fax 04936203450, Civil Station North, Kalpetta P.O.; page footer "last updated 20.12.2021" |
| 12 | `Select-String` on `data/interim/gsi_pdf_text/*.txt` for `Jawaharlal Nehru Road`, `@gsi.gov.in`, `033-`, `Kolkata`, `Director General` | find a published GSI address/route inside official GSI texts | found the access sentence in GSI 14768 L51-52 and GSI 14999 L49-50, plus the permission notice on all four PDLS 2024 title pages |
| 13 | `webfetch https://www.gsi.gov.in/webcenter/portal/GSI/pages_contactUs` | GSI contact page (alt casing) | **404** |
| 14 | `Select-String` on `gsi_PDLS_2024_51817.txt` for `Chooralmala|Attamalai|Vellarimala` | pin the exact prose lines quoted in the letter | L3245 (four names), L3247, L3257, L3261, L3281, L3290, L3308 |
| 15 | `Get-Content data/interim/inventory_extracts/inventory_gsi_pdls_wayanad.csv` | exact held-record fields quoted in the letter | 2 rows: `KER/WYD/58A03/2024/01` (p.95) and `KER/WYD/58A03/2025/01` (p.80) |
| 16 | write `data/interim/inventory_source_review_2026-10-29/contact_sources_2026-10-29.json` | provenance for every contact detail used | 4 entries; GSI email/phone/street recorded as unconfirmed |
| 17 | write `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` | the draft itself | 8 sections; NOT SENT banner |
| 18 | `git checkout -- data/interim/p3/verify_all.json` | drop recurring timing churn before checks | clean |
| 19 | `python scripts/p2_check_consistency.py` | Phase 2 docs↔manifest gate | exit 0 — 28 datasets, 16 columns, 44 unique ids |
| 20 | `python scripts/p3_check_consistency.py` | Phase 3 docs↔outputs gate | exit 0 — **470 checks, ALL PASSED** |
| 21 | `python scripts/p4_check_consistency.py` | Phase 4 docs↔outputs gate | exit 0 — P4-01…P4-06 present, progress pins "44 datasets", manifest rows healthy |
| 22 | `python scripts/p4_verify.py` | Phase 4 regeneration gate | exit 0 — **8/8 gates passed**; reproduces 9 outputs byte-identically |
| 23 | `python scripts/p5_verify.py` | Phase 5 gate (started) | **not completed** — hit the 600 s command timeout; no output file written (see §3) |

## 2. Measured values (do not re-derive)

**Contacts (fetched 2026-10-29, provenance in `contact_sources_2026-10-29.json`):**
- KSDMA: Observatory Hills, Vikas Bhavan P.O, Thiruvananthapuram – 695033 · `+91-471-2778855` ·
  `keralasdma@gmail.com` · KSEOC `seoc.ksdma@kerala.gov.in`, 1070/1079/0471-2778800.
- Wayanad district directory (Collector's office): `dcwayanad[at]gmail[dot]com` · mobile 9447204666 ·
  landline 04936202230 · fax 04936203450 · Civil Station North, Kalpetta P.O. · page footer
  "last updated 20.12.2021".
- GSI: **no live contact page retrievable** — `gsi.gov.in` returns a "Verifying secure session"
  interstitial; `/contact-us`, `/webcenter/portal/GSI/pages_contactus`,
  `/webcenter/portal/GSI/pages_contactUs` all 404. Address known only as "Kolkata – 700016" from
  GSI's own report imprint.
- GSI access sentence (verbatim, GSI 14768 L51-52 = GSI 14999 L49-50): "Soft copy of the report and
  digital data can be obtained with the permission of the Director General, Geological Survey of
  India, Kolkata-700016". Permission notice on PDLS 2024 title pages (L38, 1568, 2134, 3583):
  "Not to be published in part or full without prior permission of the Director General, Geological
  Survey of India, Kolkata".

**Facts quoted in the letter (all already established, re-confirmed this run):**
- Inventory: 468 source records / 8 sources; 372 in-window included records → 371 event groups.
- GSI PDLS records held: exactly **two**, both Wayanad — `KER/WYD/58A03/2024/01` (PDF p.95) and
  `KER/WYD/58A03/2025/01` (PDF p.80, June 2024 event, reported 21.05.2025).
- 2024 printed coordinate: `11027'46"N / 76008'03"E` (degree glyph absent in the PDF text layer) =
  11.462778 N, 76.134167 E; whole-second DMS ≈ **31 m**.
- Corroboration: **495 m** vs Sreekumar et al. 2025 Table 1; 1.98 km to Mundakkai, 4.91 km to
  Chooralmala settlements → `CORROBORATED`.
- Four names appear only as prose at `gsi_PDLS_2024_51817.txt` L3245: "incidences occurred in
  Chooralmala, Mundakkai, Attamalai and Vellarimala". L3281 prints "Vellaramala" once (spelling
  variation noted in the letter).

**Gate numbers:** p2 = 28 datasets / 16 columns / 44 unique ids; p3 = 470 checks; p4 = 8/8 gates,
per-fold support `[52 121 84 54 52]`, retained minimum train→test gap **1001.3 m** (> 1000 m).

## 3. Bugs caught and fixes

1. **`data/interim/p3/verify_all.json` timing churn (recurring, third run in a row).** Diff is only
   `seconds` values (e.g. `37.8 → 27.9`). Fix: `git checkout --` before checks. It reappeared after
   the gate run (the p3 checker rewrites timing fields), so it must be reverted again immediately
   before staging — done, see §5.
2. **GSI contact lookup dead end.** Three URL shapes 404 and the homepage serves a session-shell
   page with no parseable content. Fix: stopped guessing URLs after the third 404 and used the
   address/route **printed in GSI's own reports**, leaving email/phone/street as explicit
   placeholders rather than filling them from memory. This is the correct behaviour under the
   "published contact details only" rule.
3. **DDMA has no published mailbox.** The district homepage offers only helplines; the directory
   page offers the **Collector's** address. Fix: the draft labels §1.3 as the Collector's office
   (DDMA chair) and tells the user to re-verify, instead of relabelling the Collector's Gmail as a
   DDMA mailbox.
4. **`p5_verify.py` exceeded the 600 s timeout.** Not a failure of the model: it is a long-running
   regeneration check, and this run changed **no Phase 5 input or output**. Left unrun rather than
   re-run with a huge timeout; recorded here so the next run does not assume it was green. Nothing
   was written by the aborted run (`git status` shows no p5 file).

## 4. Verification and gates

| Gate | Result |
|---|---|
| `p2_check_consistency.py` | PASS — 28 datasets, 16 columns, 44 unique ids |
| `p3_check_consistency.py` | PASS — 470/470 checks |
| `p4_check_consistency.py` | PASS — P4-01…P4-06, "44 datasets" pin, manifest rows healthy |
| `p4_verify.py` | PASS — 8/8 gates, outputs regenerate byte-identically |
| `p5_verify.py` | NOT RUN to completion (timeout; docs-only change, no Phase 5 artefact touched) |
| `git diff --check` | run at staging — clean |

Also verified by inspection: no manifest row, no `data/processed/inventory/*` file, no Phase 4 or
Phase 5 product was modified in this run (`git status` shows only the two new files).
**No draft was sent and no agency was contacted** — the only network use was read-only GETs of
public agency pages, recorded in §1.

## 5. Outputs produced or changed

| File | Status | Contents |
|---|---|---|
| `docs/requests/DRAFT_2026-10-29_official-inventory-request.md` | **new** | The draft: NOT-SENT banner, §0 usage, §1 three recipient blocks with provenance and a suggested sending order, §2 master letter (GSI), §3 KSDMA/DDMA variants, §4 fields table, §5 wording rules, §6 attachment checklist, §7 reply tracker + outcome vocabulary, §8 send log |
| `data/interim/inventory_source_review_2026-10-29/contact_sources_2026-10-29.json` | **new** | Contact provenance: verbatim published strings, URLs, fetch timestamp, and an explicit placeholder policy; GSI failures recorded |
| `reports/RUN-2026-10-29-11_official-inventory-request-draft.md` | **new** | This report |
| `data/interim/p3/verify_all.json` | reverted | timing churn dropped; content as committed |

**Unverified placeholders carried in the draft** (all bracketed, all listed for the user):
`[PLACEHOLDER — GSI published email not confirmed]`, `[PLACEHOLDER — not confirmed]` (GSI telephone),
`[PLACEHOLDER — only city and PIN are printed in GSI reports]` (GSI street address), plus the user's
own `[DATE]`, `[NAME]`, `[DESIGNATION]`, `[INSTITUTION / DEPARTMENT]`, `[CITY]`, `[POSTAL ADDRESS]`,
`[EMAIL]`, `[PHONE]`, and the not-yet-written one-page project note.

## 6. Current project state

- Phase 5 (Random Forest susceptibility baseline) unchanged: no training table, model, metric, map
  or output was read or written by this run.
- Phase 4 inventory unchanged: still 468 source records, 372 in-window, 371 event groups, two 2024
  records; no record added, digitised, merged or deduplicated.
- `docs/data_manifest.csv` unchanged (44 rows); no dataset status changed.
- The drafting task is **complete but not executed**: a reviewed, provenance-checked letter exists;
  the send decision, the GSI contact route, and the project note remain with the user.
- Commit: `<pending — pinned in the follow-up commit>`.

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Sending order and timing (recommendation in §1.4: GSI + KSDMA in parallel, DDMA after).
  2. How to reach GSI: confirm a published email/phone on `gsi.gov.in` (the site is JS-gated for
     automated fetch — a human browser may work), or use the RTI route if no data desk is published.
  3. Whether to write the one-page project note (the only attachment that does not yet exist), or
     send without it.
  4. Whether to include the Meenakshi Bridge (June 2024) record in the enclosures — it is a second
     Wayanad datum that shows the volumes were read carefully, but it is a different event.
- **What the next step must do / must not do:**
  - Do **not** state or imply that additional datasheets are known to exist; the letter asks
    "whether any … are available / held".
  - Do **not** treat Chooralmala/Mundakkai/Attamalai/Vellarimala as four records, and do not derive
    coordinates from the FIR prose.
  - Do **not** paste any reply straight into the inventory: a reply that offers records becomes a
    new source and must pass acquisition → validation → manifest before Phase 4/5 use.
  - Do **not** describe the project as forecasting, warning or an early-warning system.
- **Quick commands:**
  - `python scripts/p2_check_consistency.py && python scripts/p3_check_consistency.py && python scripts/p4_check_consistency.py`
  - `git diff --check`
  - `Get-Content docs/requests/DRAFT_2026-10-29_official-inventory-request.md` (read before sending)
  - `Select-String -Path data/interim/gsi_pdf_text/gsi_PDLS_2024_51817.txt -Pattern 'Chooralmala'`
- **Do not re-derive:** 468 / 385 / 372 / 371; 495 m corroboration; ≈31 m whole-second precision;
  p.95 and p.80 page references; the two record IDs; KSDMA contact strings; the GSI access sentence
  and its line numbers; the GSI 404 findings (three URL shapes); the district-directory staleness
  note (20.12.2021).
