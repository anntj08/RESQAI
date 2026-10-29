# Run Report RUN-2026-10-29-08 — Integrate the LSZ-01 vs Phase 5 RF comparison into `docs/PHASE5_PROGRESS.md`

**Date:** 2026-10-29 · **Session goal:** documentation-only integration of the completed
descriptive LSZ-01 vs Phase 5 RF comparison and its sensitivity findings into the Phase 5
progress report — no recomputation, no change to the comparison/sensitivity results, Phase
4/5 outputs, map, manifest status, or input data.
**Starting state:** commit `81bb116` (RUN-07 complete), tree clean.
**End state:** commit of this run (pinned in §6); only `docs/PHASE5_PROGRESS.md` modified;
tree clean; nothing pushed.

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | read `AGENTS.md`, `reports/README.md`; `git status` | conventions + clean start | tree clean at `81bb116` |
| 2 | read the four sources of truth: `reports/RUN-2026-10-28-06_lsz-rf-map-comparison.md`, `reports/RUN-2026-10-29-07_lsz-rf-comparison-sensitivity.md`, `outputs/lsz_rf_comparison/comparison_domain.json`, `outputs/lsz_rf_comparison/sensitivity/sensitivity_summary.json` | every number quoted from files, never from memory | all §2 numbers below trace to these four files |
| 3 | grep for cross-references to PHASE5_PROGRESS section numbers repo-wide | confirm renumbering old §7–9 → §8–10 breaks no reference | only the doc's own header paragraph references those sections (RUN-03 references "§2 values", which keeps its number) |
| 4 | edit `docs/PHASE5_PROGRESS.md` | the integration (§3 below) | header paragraph + new §7 (+7.1, 7.2) + renumbered §8/§9/§10 + 1 interpretive bullet + status update |
| 5 | verify structure + characters; review full `git diff docs/PHASE5_PROGRESS.md` | QA before commit | sections 1–10 sequential; em-dashes/percent signs intact; diff = exactly the intended 85 insertions / 9 deletions, single file |
| 6 | p2/p3/p4 documentation consistency checkers + `git diff --check` | applicable checks | p2 pass; p3 **470/470**; p4 **116/116**; diff-check clean |
| 7 | commit + hash pin | capture | §6 |

## 2. Measured values (do not re-derive; quoted from the source files)

**Confirmed, from `comparison_domain.json`:** primary comparison domain (GADM 4.1 ∩ GSI
coverage ∩ valid RF) = 2,248,841 cells = 2,023.96 km² = 95.43 % of the district mask and
95.97 % of the RF map domain; GADM−LSZ exclusion 94,542 cells = 85.09 km²; LSZ-covered
RF-invalid 13,155 cells; zone capture Low 95.097 / Moderate 97.301 / High 95.504 %; cuts
p20 0.0 / p40 0.007447 / p60 0.082566 / p80 0.277386.

**Confirmed, from the RUN-06 report:** make_valid repair delta 0.0 km²; zone-mean RF vote
share monotone Low 0.100228 < Moderate 0.272498 < High 0.381756 (medians 0.0105 / 0.1882 /
0.3287); GSI-High 89.59 % of domain area in Q4∪Q5 (57.03 % in Q5; 0.65 % in Q1∪Q2); Q5
composition 50.64 / 38.52 / 10.85 %.

**Confirmed, from `sensitivity_summary.json`:** V1 cuts 0.000617 / 0.008528 / 0.092314 /
0.282145 (threshold domain = full RF map domain, 2,343,343 cells; comparison domain
unchanged; zone means identical to primary); V2 domain 2,251,769 cells (+2,928 = +2.6352 km²)
with per-zone deltas Low −126,184 / Moderate +157,298 / High −28,186 cells (−113.5656 /
+141.5682 / −25.3674 km²); V2 zone means 0.093024 / 0.260631 / 0.377683 (ordering unchanged);
High-zone Q4∪Q5 = 89.59 / 87.53 / 89.544 % (primary / V1 / V2).

## 3. Exact documentation changes (`docs/PHASE5_PROGRESS.md`, the only file changed)

1. **Header paragraph** (the confirmed/interpretation map of the doc): now reads "Sections
   2–6 record confirmed results … Section 7 records the **comparison-only LSZ-01 layer**
   (added 2026-10-29; measured on saved comparison outputs with gates against the primary
   record; nothing upstream modified). Section 8 lists limitations. Section 9 holds
   interpretation and recommendations only. Section 10 states status."
2. **New section 7** — "Descriptive comparison with the GSI 2022 LSZ zones (LSZ-01) —
   comparison-only layer (confirmed measurements)":
   - preamble: comparison-only, nothing upstream modified, LSZ-01 keeps
     `DOWNLOADED_NOT_FULLY_VALIDATED`, GSI zones not in the predictor stack;
   - the **five limitations carried verbatim** as a labelled block: RF = relative ranking not
     probability/timing; LSZ-01 = another model-derived product, not ground truth/geology/
     labels/predictor; descriptive + spatially autocorrelated, does not establish accuracy;
     LSZ-01 covers 95.99 % of GADM and is not field-validated; all_touched Moderate-absorbs-
     boundary-cells = order-dependent rasterization effect;
   - **7.1 Primary comparison** (labelled "measured", sources cited): domain numbers,
     geometry repair, quintile cuts, the monotone Low < Moderate < High ordering, GSI-High
     top-band concentration, Q5 composition;
   - **7.2 Sensitivity** (labelled "measured", sources cited): comparison table
     (primary vs V1 vs V2: domain, cuts, zone means, High Q4∪Q5), what each variant changed,
     the V2 rasterization mechanism (file-order painting High → Low → Moderate, Moderate
     painted last), and the descriptive stability verdict.
3. **Renumbering:** old §7 Limitations → **§8**, old §8 Interpretation → **§9**, old §9
   Status → **§10** (no external file references the old numbers; verified by grep).
4. **One bullet added to §9 Interpretation** (marked "not confirmed results" by the section
   header): the two products share factor families, so some agreement is expected by
   construction and cannot establish accuracy; LSZ-01 stays out of the predictor stack. This
   preserves the confirmed-measurement vs interpretation distinction.
5. **§10 Status update:** the "what exists now" list gains the comparison-only descriptive
   LSZ layer with its sensitivity checks (pointing to §7, status note kept); run-report list
   extended with RUN-06 and RUN-07.

**Not done (by instruction):** no recomputation of any comparison/sensitivity number; no new
sensitivity analyses; no change to Phase 4/5 outputs, map, manifest (`LSZ-01` stays
`DOWNLOADED_NOT_FULLY_VALIDATED`), or input data; no other doc touched.

## 4. Verification and gates

| Suite | Result |
|---|---|
| `p2_check_consistency.py` | pass |
| `p3_check_consistency.py` | **470/470** |
| `p4_check_consistency.py` | **116/116** |
| `git diff --check` | clean |
| Section-number cross-reference grep | no external references to old §7–9 numbers |
| Full-diff review | single file, 85 insertions / 9 deletions, all intended |

## 5. Outputs produced or changed

- `docs/PHASE5_PROGRESS.md` — the integration described in §3 (the only change).
- `reports/RUN-2026-10-29-08_lsz-comparison-doc-integration.md` — this report.

## 6. Current project state

Phase 5 baseline complete and verified; the descriptive LSZ comparison and its sensitivity
verdict are now part of the Phase 5 progress record as confirmed measurements (§7) with their
limitations carried verbatim, one interpretive caveat in §9, and the status list (§10)
updated. `LSZ-01` remains `DOWNLOADED_NOT_FULLY_VALIDATED`. Commit of this run: **pinned
below** (work + this report; a one-line follow-up pins the hash). Tree clean; nothing pushed.

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Whether the Phase 4 progress doc or AGENTS.md need any echo of the comparison layer
     (deliberately not done — AGENTS.md already carries the standing rules; Phase 4 docs are
     out of scope for a Phase 5 comparison).
  2. Next substantive step for the comparison layer, if any (e.g. OSM-boundary domain variant,
     vector-space comparison, fixed-score-band classes) — each would need its own
     authorisation and the same blocker-gated pattern.
- **What the next step must do / must not do:** must keep the five §7 limitations attached to
  any future summary of the comparison (the doc now carries them in one place — quote or link
  §7, do not paraphrase them away); must never use LSZ-01 as labels, truth, geology, or a
  predictor; must not renumber PHASE5_PROGRESS sections casually (the doc's header paragraph
  maps sections to content types).
- **Quick commands:** `python scripts/p2_check_consistency.py` ·
  `python scripts/p3_check_consistency.py` · `python scripts/p4_check_consistency.py` ·
  `git diff --check`.
- **Do not re-derive (quote as-is):** all §2 numbers above with their source files; the doc
  now states them in PHASE5_PROGRESS §7 — future runs should quote that section instead of
  re-reading the JSONs, unless verifying the JSONs themselves.
