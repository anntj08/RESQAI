# Run Report RUN-2026-10-29-07 — Sensitivity of the LSZ-01 vs Phase 5 RF comparison: full-map thresholds + all_touched rasterization

**Date:** 2026-10-29 · **Session goal:** two descriptive sensitivity checks on the RUN-06
LSZ-01 × RF-quintile comparison — (V1) RF quintile thresholds derived over the **full RF map
domain** and applied inside the unchanged comparison domain; (V2) **all_touched=True** GSI
rasterization with the primary thresholds unchanged — each measured independently against the
primary result. NO retraining, tuning, or changes to any Phase 4/5 output; the primary
comparison outputs preserved unchanged.
**Starting state:** commit `cd6b6a6` (RUN-06 complete), tree clean.
**End state:** commit of this run (pinned in §6); sensitivity outputs under
`outputs/lsz_rf_comparison/sensitivity/`; sources and primary outputs untouched; `LSZ-01` stays
**`DOWNLOADED_NOT_FULLY_VALIDATED`**; tree clean; nothing pushed.

**Standing disclaimers (attached to every table, figure and metadata file produced here):**
1. The RF raster is a **relative ranking conditional on the observed inventory** — not a
   calibrated probability, forecast, warning or timing prediction.
2. The GSI 2022 zones (LSZ-01) are **another model-derived susceptibility product** — not
   ground truth, not geology, not validation labels.
3. This is **descriptive zone/ranking agreement only**; no significance tests; spatial
   autocorrelation is expected in both products.
4. The GSI file covers **95.99 % of the GADM 4.1 project boundary** and is **not
   field-validated**; the zones are **not extrapolated** to the missing GADM area.

**Verdict up front (descriptive, not inferential): the reported zone/ranking pattern is STABLE
under both variants.** Zone-mean RF scores stay monotone Low < Moderate < High in every
variant; the GSI-High zone stays concentrated in the top two RF bands (Q4∪Q5 = 89.59 % primary
/ 87.53 % V1 / 89.54 % V2). The largest single change is V2's zone-composition shift caused by
the rasterization choice itself (Moderate zone fattens +36 %), detailed in §2.3–2.4.

## 1. What was run, in order

| # | Command / file | Purpose | Result (exit, key numbers) |
|---|---|---|---|
| 1 | re-read `AGENTS.md`, `reports/README.md`, RUN-06 report; `git status` | conventions; primary results treated as authoritative | tree clean at `cd6b6a6` |
| 2 | `python scripts/validate_ksdma_lsz_wayanad.py` | task-required re-validation before analysis | exit 0; sha256 match True; CRC ok; coverage GADM 95.99 % / OSM 99.07 % / mask 95.99 % (all_touched 96.11 %) — identical to RUN-05/06 |
| 3 | hash gate (inline + in-script) | LSZ zip + RF raster unchanged | zip `e5da8e03…37e2f` matches fetch_evidence + manifest (status unchanged); RF raster `88687c89…2a053` matches `map_metadata.json` |
| 4 | `python scripts/lsz_rf_comparison_sensitivity.py` (first run) | both variants, hard gates vs primary record | **exit 1 — BLOCKER**: the geometry-repair gate checked the *raw* float delta (`abs(d)>0`) and tripped on ULP noise; measured raw deltas ≤ 1.4e-12 km² (§3 #1); gate re-anchored to the primary record's 6-dp (1 m²) precision, raw deltas recorded unrounded |
| 5 | cleanup + docstring fix + re-run | dead placeholder code removed before first run (§3 #3); overlap-rule description corrected after inspecting V2 deltas (§3 #2) | exit 0; **all gates passed**; see §2 |
| 6 | output inspection + figure QA | verify CSVs carry disclaimers; figure renders | 4 CSVs with `#` disclaimer headers; `sensitivity_figure.png` verified visually (3 panels, labels, footer disclaimers) |
| 7 | p2/p3/p4 checkers + `git diff --check` | regression | pass / 470/470 / 116/116 / clean |
| 8 | commit + hash pin | capture | §6 |

## 2. Measured values (do not re-derive; every number traceable to a file)

### 2.0 Gates (all passed; recorded in `sensitivity_summary.json` → `gates`, `primary_reproduction`)

- Input hashes: LSZ zip and RF raster sha256 both match their recorded metadata (values in §1 #3).
- Recomputed primary comparison domain = **2,248,841 cells** == recorded.
- Recomputed primary quintile cuts = **0.0 / 0.007447 / 0.082566 / 0.277386** == recorded.
- Recomputed primary cross-tab == primary CSV cell-by-cell (15 zone×quintile cells checked).
- Geometry repair: `make_valid` per feature as in the primary; rounded deltas (6 dp of km²)
  equal the primary record exactly (all 0.0). Raw deltas — **High 1.49e-14, Low 1.43e-12,
  Moderate 5.96e-14 km²** (≤ 1.4e-6 m²) — are floating-point ULP noise, ~15 orders of
  magnitude below the 900 m² cell; recorded unrounded in the metadata, gate threshold 1e-6 km²
  (= the primary record's precision).
- Full RF map domain = **2,343,343 cells** == `map_metadata.json` `domain_cells` (V1 gate).

### 2.1 Variant 1 — full-map RF quintile thresholds

**Only the threshold-estimation domain changed.** Bands derived over all valid cells of the
full RF raster domain (district mask AND RF valid = **2,343,343 cells = 2,109.01 km²**); the
fixed cut points were then applied **within the unchanged primary comparison domain**
(GADM ∩ GSI coverage ∩ RF valid = 2,248,841 cells = 2,023.96 km² — identical cells, identical
zone areas, identical per-cell scores).

- V1 cuts: p20 **0.000617**, p40 **0.008528**, p60 **0.092314**, p80 **0.282145**
  (primary: 0.0 / 0.007447 / 0.082566 / 0.277386 — every V1 cut slightly higher because the
  exactly-0 tie mass is proportionally diluted over the larger estimation domain).
- **Zone-mean RF scores are bit-identical to the primary** (Low 0.100228 / Moderate 0.272498 /
  High 0.381756) — necessarily: same cells, same scores; only band membership moves.

% of GSI-zone area in each RF band (primary → V1):

| GSI zone | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| Low | 24.099 → 24.670 | 22.841 → 23.477 | 21.710 → 21.802 | 18.181 → 17.140 | 13.169 → 12.911 |
| Moderate | 9.083 → 9.345 | 11.012 → 11.474 | 15.203 → 15.587 | 24.775 → 24.108 | 39.928 → 39.486 |
| High | 0.205 → 0.205 | 0.441 → 0.479 | 9.764 → 11.785 | 32.557 → 31.076 | 57.033 → 56.454 |

Largest per-band shift: GSI-High Q3 +2.02 pp (9.764 → 11.785); High Q4∪Q5 89.59 → 87.53 %
(−2.06 pp). Q5 (highest band) composition (cells 449,768 → 442,886): Low 50.64 → 50.42 %,
Moderate 38.52 → 38.68 %, High 10.85 → 10.90 %. **Pattern unchanged.**

### 2.2 Variant 2 — all_touched=True zone rasterization (primary cuts unchanged)

The GSI polygons were rasterized with `all_touched=True` (primary: `all_touched=False`),
keeping the **primary comparison-domain quintile cuts** (0.0 / 0.007447 / 0.082566 / 0.277386)
unchanged. The comparison domain was **re-derived explicitly** as GADM ∩ LSZ(all_touched) ∩ RF
valid:

- **2,251,769 cells = 2,026.59 km²** — **+2,928 cells = +2.6352 km² vs primary**
  (95.5541 % of the district mask; primary 95.43 %). Consistent with RUN-05's measured
  all_touched-vs-center coverage difference (96.11 % vs 95.99 %).
- Overlap rule (recorded): `rasterize` paints the (geometry, code) pairs in shapefile file
  order — **High, then Low, then Moderate** — so the later class overwrites earlier ones and
  **Moderate wins overlaps**. This is the SAME single-pass convention as the primary
  rasterization (identical list construction), so the variant is directly comparable.

**Per-zone rasterization deltas (cells within district mask AND RF valid):**

| GSI zone | primary | all_touched | delta cells | delta km² |
|---|---|---|---|---|
| Low | 1,729,430 | 1,603,246 | **−126,184** | −113.5656 |
| Moderate | 433,873 | 591,171 | **+157,298** | +141.5682 |
| High | 85,538 | 57,352 | **−28,186** | −25.3674 |
| (domain) | 2,248,841 | 2,251,769 | +2,928 | +2.6352 |

Zone-composition effect (V2 zone areas in domain): Low 1,556.49 → 1,442.92 km² (−7.3 %),
Moderate 390.49 → 532.05 km² (**+36.3 %**), High 76.98 → 51.62 km² (−33.0 %). Mechanism:
`all_touched` pulls in every boundary cell touched by any polygon, and the file-order painting
then assigns multi-class-touched cells to **Moderate** (painted last) — a rasterization-order
artifact, not a semantic property of the classes.

% of GSI-zone area in each RF band (primary → V2):

| GSI zone | Q1 | Q2 | Q3 | Q4 | Q5 |
|---|---|---|---|---|---|
| Low | 24.099 → 24.988 | 22.841 → 23.422 | 21.710 → 21.910 | 18.181 → 17.651 | 13.169 → 12.028 |
| Moderate | 9.083 → 9.461 | 11.012 → 11.464 | 15.203 → 15.747 | 24.775 → 25.193 | 39.928 → 38.135 |
| High | 0.205 → 0.141 | 0.441 → 0.317 | 9.764 → 9.998 | 32.557 → 33.277 | 57.033 → 56.267 |

Zone-mean RF scores (touched-in boundary cells carry lower scores, diluting every zone):
Low 0.100228 → 0.093024, Moderate 0.272498 → 0.260631, High 0.381756 → 0.377683 — **ordering
unchanged**. Q5 composition (cells 449,768 → 450,546): Low 50.64 → 42.80 %, Moderate 38.52 →
50.04 %, High 10.85 → 7.16 % — follows directly from the Moderate zone fattening above.

### 2.3 Direct comparison with the primary (summary)

| Quantity | primary | V1 | V2 |
|---|---|---|---|
| Comparison domain (cells) | 2,248,841 | 2,248,841 (identical) | 2,251,769 (+2,928) |
| Comparison domain (km²) | 2,023.96 | 2,023.96 | 2,026.59 |
| Quintile cuts p20/p40/p60/p80 | 0.0 / 0.007447 / 0.082566 / 0.277386 | 0.000617 / 0.008528 / 0.092314 / 0.282145 | same as primary (unchanged) |
| Zone means (Low/Med/High) | 0.100228 / 0.272498 / 0.381756 | identical | 0.093024 / 0.260631 / 0.377683 |
| Zone means monotone Low<Med<High | yes | yes | yes |
| GSI-High % in Q4∪Q5 | 89.59 | 87.53 | 89.544 |
| GSI-High % in Q1 | 0.205 | 0.205 | 0.141 |
| Q5 composition (Low/Med/High) | 50.64 / 38.52 / 10.85 | 50.42 / 38.68 / 10.90 | 42.80 / 50.04 / 7.16 |

### 2.4 Pattern-stability verdict (descriptive, computed in-script)

- **Monotone zone ordering** (Low < Moderate < High mean RF score): holds in the primary, V1,
  and V2.
- **High-zone concentration in the upper bands**: Q4∪Q5 = 89.59 % (primary), 87.53 % (V1),
  89.544 % (V2) — stable within ~2 pp.
- **Reading**: the reported zone/ranking pattern is **not an artifact of either analysis
  choice** at the descriptive level. V1 shifts band edges slightly (all cuts rise; largest
  per-band change ~2 pp); V2 leaves per-zone distributions close to the primary but changes
  the *zone composition itself* (Moderate +36 % area from the touched boundary cells painted
  last) — anyone reusing `all_touched=True` for area reporting should know that effect is
  painter-order-dependent, not a property of the data.

## 3. Bugs caught and fixes

| # | Where | What | Fix |
|---|---|---|---|
| 1 | sensitivity script, geometry-repair gate | First run **exit 1, BLOCKER**: the gate tested the raw float delta (`abs(d)>0`), tripping on shapely ULP noise (raw deltas 1.49e-14 / 1.43e-12 / 5.96e-14 km²). The primary record's check operates at 6 dp of km² (= 1 m²) and correctly recorded 0.0 — the stricter gate was over-strict relative to the authoritative method, not evidence of a real area change | measured the raw deltas first, then re-anchored the gate to the primary record's precision: blocker fires only beyond 1e-6 km²; **and** the recomputed rounded deltas must equal the primary recorded values exactly (they do). Raw deltas recorded unrounded in `sensitivity_summary.json`; docstring documents the rationale |
| 2 | sensitivity script, overlap-rule text | My first draft described the painter order as "Low → Moderate → High (High wins ties)" — **wrong**. The V2 per-zone deltas (Moderate +157,298 cells) exposed the real order: `rasterize` paints in shapefile file order **High → Low → Moderate**, so Moderate wins overlaps | prose corrected in docstring and metadata; the convention itself is identical to the primary (same list construction), so all comparisons remain valid |
| 3 | sensitivity script | Dead placeholder code written in the initial draft (`zone_view` helper with `if False` branch, `row_p` placeholder, duplicate `comp` assignment, primary-stats CSV re-read twice inside dict comprehensions) | removed before the first successful run; primary stats CSV now read once |

## 4. Verification and gates

| Suite | Result |
|---|---|
| LSZ re-validation (task-required) | pass — sha256 match, CRC ok, coverage/union identical to RUN-05/06 |
| Input hash gates (zip + RF raster) | pass — both match recorded metadata |
| Primary reproduction gates (domain, cuts, cross-tab cells, repair deltas) | pass — all equal the primary record |
| Full-RF-domain gate (V1) | pass — 2,343,343 cells == `map_metadata.json` |
| `p2_check_consistency.py` | pass |
| `p3_check_consistency.py` | **470/470** |
| `p4_check_consistency.py` | **116/116** |
| `git diff --check` | clean |
| Figure QA | verified visually (3 panels, value labels, footer disclaimers) |

## 5. Outputs produced or changed

All new, sensitivity-only (primary outputs and all upstream files untouched):

- `outputs/lsz_rf_comparison/sensitivity/variant1_full_domain_thresholds_crosstab.csv` — V1
  GSI zone × RF quintile: cells, km², % within zone, % of quintile; four disclaimers as `#`
  header lines.
- `outputs/lsz_rf_comparison/sensitivity/variant1_zone_stats.csv` — V1 per-zone RF score
  distribution (mean/std/min/p05/p25/median/p75/p95/max + per-band shares).
- `outputs/lsz_rf_comparison/sensitivity/variant2_alltouched_crosstab.csv` — V2 cross-tab,
  same columns.
- `outputs/lsz_rf_comparison/sensitivity/variant2_zone_stats.csv` — V2 per-zone stats.
- `outputs/lsz_rf_comparison/sensitivity/sensitivity_summary.json` — full metadata: input
  sha256s + gate results, primary-reproduction record, geometry-repair raw deltas + gate note,
  V1 threshold domain + cuts + what-changed statement, V2 domain deltas + per-zone
  rasterization deltas + overlap rule, direct comparison with the primary (per-zone
  percentages and means), pattern-stability verdicts, disclaimers.
- `outputs/lsz_rf_comparison/sensitivity/sensitivity_figure.png` — 3-panel figure
  (GSI Low / Moderate / High): % of zone area per RF band, primary vs V1 vs V2 bars with value
  labels; all four disclaimers in the footer.
- `scripts/lsz_rf_comparison_sensitivity.py` — re-runnable, blocker-gated (any primary-record
  mismatch exits 1 without writing results).
- `data/interim/lsz_comparison_probe/sensitivity_run_log.txt` — console log of the final run.
- `data/interim/lsz_reference/validation.json` — rewritten by the task-required re-validation
  (numbers identical to RUN-06; timestamp refreshed).

**Explicitly NOT done:** no retraining, tuning, refit, or model changes; no change to the
susceptibility raster, model artifacts, Phase 4 tables, manifest, phase docs, or any primary
comparison output; LSZ-01 status not upgraded; GSI zones not extrapolated; no significance
tests; GSI classes never interpolated (categorical rasterization only, both variants).

## 6. Current project state

Phase 5 baseline complete and verified (RF raster sha256 re-confirmed this run). The primary
LSZ-vs-RF comparison (RUN-06) now carries a **sensitivity layer**: the monotone
Low < Moderate < High ordering and the High-zone top-band concentration are robust to (a)
re-deriving quintile thresholds over the full RF map domain and (b) `all_touched=True`
rasterization. Known rasterization caveat: with `all_touched=True`, the zone painted last in
file order (Moderate) absorbs multi-class-touched boundary cells (+36.3 % zone area) — a
painter-order artifact worth remembering for any future area reporting. `LSZ-01` remains
`DOWNLOADED_NOT_FULLY_VALIDATED`. Commit of this run: **`6d77f1e`** (work + this report; a
one-line follow-up pins the hash). Tree clean; nothing pushed.

## 7. Next-step handoff (prompt material)

- **Decisions the user must make:**
  1. Whether the sensitivity verdict warrants a one-line pointer in `PHASE5_PROGRESS.md`
     (deliberately not done — Phase 4/5 docs untouched, as in RUN-06).
  2. Whether further sensitivity axes are wanted, e.g. (a) GADM vs OSM boundary as the
     comparison domain, (b) vector-space (polygon-level weighted means) instead of the 30 m
     grid, (c) RF bands as fixed score ranges instead of domain quantiles. Each would need the
     same blocker-gated pattern; cuts for both threshold domains are recorded, so (c) is
     reproducible from §2.1 alone.
  3. Whether the V2 painter-order finding should be attached as a caveat wherever
     `all_touched=True` rasterization is used for area accounting elsewhere in the project.
- **What the next step must do / must not do:** must keep the four disclaimers attached to any
  reuse of these tables/figures; must never use the GSI zones as labels, validation truth, or
  predictors; must not read RF vote shares as probabilities; must not "fix" the V2 zone
  composition by reordering the paint list without labelling it a new method (the current
  order matches the primary convention — comparability beats tidiness). If the LSZ archive is
  ever re-downloaded, re-run `validate_ksdma_lsz_wayanad.py` and the hash gate first.
- **Quick commands:** `python scripts/validate_ksdma_lsz_wayanad.py` ·
  `python scripts/lsz_rf_comparison_sensitivity.py` ·
  `python scripts/lsz_rf_map_comparison.py` (primary) · p2/p3/p4 checkers.
- **Do not re-derive (quote as-is):** primary domain 2,248,841 cells = 2,023.96 km²; V1
  threshold domain 2,343,343 cells = 2,109.01 km²; V1 cuts 0.000617 / 0.008528 / 0.092314 /
  0.282145; V2 domain 2,251,769 cells = 2,026.59 km² (+2,928 = +2.6352 km²); V2 per-zone
  deltas Low −126,184 / Moderate +157,298 / High −28,186 cells (−113.5656 / +141.5682 /
  −25.3674 km²); V2 zone areas Low 1,442.92 / Moderate 532.05 / High 51.62 km²; zone means
  primary 0.100228 / 0.272498 / 0.381756, V1 identical, V2 0.093024 / 0.260631 / 0.377683;
  High-zone Q4∪Q5 89.59 / 87.53 / 89.544 %; Q5 composition primary 50.64/38.52/10.85, V1
  50.42/38.68/10.90, V2 42.80/50.04/7.16; repair raw deltas 1.49e-14 / 1.43e-12 / 5.96e-14 km²;
  zip sha256 `e5da8e03…37e2f`; RF raster sha256 `88687c89…2a053`.
