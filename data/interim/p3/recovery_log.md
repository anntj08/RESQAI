# Phase 3 recovery and verification log — 2026-10-26

Persistent record of the verification pass that followed the first Phase 3 completion.
Append-only by intent: if the phase is resumed, add a new dated section rather than
rewriting this one.

Scope: geospatial preprocessing, inventory suitability, data-quality verification,
reproducibility, data-readiness. **No model, training table, synthetic event or
performance metric exists in this phase, and none was produced here.**

## Environment

| Item | Value |
|---|---|
| Host interpreter | Python 3.14.6 (`C:\Users\anntr\AppData\Local\Programs\Python\Python314\python.exe`) |
| Working tree | `C:\Major`, branch `main` |
| Base commit | `c5e2c42` (Phase 2 complete) — nothing committed during this pass until the final commit |
| Shell | PowerShell (Windows). Native stderr is **not** treated as failure; only `$LASTEXITCODE` decides |

Times below are **file write times** of the artefact each step produced, not hand-typed
estimates, so they are verifiable with `Get-Item <path> | Select LastWriteTime`.

## Timeline

| Time | Step | Artefact written |
|---|---|---|
| 21:07:54 | Added Phase 2 immutability verifier | `scripts/p3_verify_phase2_untouched.py` |
| 21:14:58 | Fixed rainfall all-NaN handling at source | `scripts/p3_rainfall.py` |
| 21:16:59 | Rewrote runner (error policy, prereq gate, fail-fast) | `data/interim/p3/rebuild_all.ps1` |
| 21:17:38 | Rewrote comparator (`--baseline`, declared additive keys) | `data/interim/p3/compare_rebuild.py` |
| 21:21:14 | Full pipeline, 11 stages | `data/interim/p3/rebuild_run.log` |
| 21:21:21 | Determinism comparison (gen A vs gen B) | `data/interim/p3/rebuild_comparison_roundtrip.json` |
| 21:22:04 | Raw-input immutability verifier | `scripts/p3_verify_raw_immutable.py` |
| 21:23:12 | Six-gate master runner | `scripts/p3_verify_all.py` |
| 21:28:52 | Comparison against pre-recovery baseline | `data/interim/p3/rebuild_comparison.json` |
| 21:28:53 | All gates re-run on final tree | `data/interim/p3/verify_all.json` |
| 21:29:26 | Documentation brought in line with measurements | `docs/PHASE3_PROGRESS.md` |

## Defects found and fixed

| # | Defect | Evidence that exposed it | Fix | Verified by |
|---|---|---|---|---|
| 1 | Runner used `$ErrorActionPreference = "Stop"`, so a benign numpy stderr line killed the pipeline after rainfall although that stage exited 0 | first rebuild attempt stopped at rainfall with a *warning*, not an error | `"Continue"` + `$LASTEXITCODE` check after every python call, fail fast at the first nonzero exit, `cmd /c` redirection, per-stage script SHA-256 + Python version in the log | 11/11 stages exit 0, no stderr noise |
| 2 | The rebuild's "clear outputs" step deleted **four Phase 1 inputs**, so `p3_geology.py` failed with `DataSourceError: ...glim_wayanad_clip.gpkg: No such file or directory` | that traceback | restored all four from `rebuild_backup/`; runner now gates on the four prerequisites and exits **3** with a named list instead of failing inside a stage | `p3_geology.py` exit 0; 4/4 restored files byte-identical to baseline |
| 3 | `p3_rainfall.py` let `Mean of empty slice`, `All-NaN slice encountered`, `Degrees of freedom <= 0` escape to stderr, and carried a dead `if False` branch whose `np.stack(clim)` would have stacked 12 *district scalars* as if they were rasters | stderr captured from the repaired run | scoped the three expected warnings to the three affected reductions via `expect_all_nan_slices()`, asserted each result's NaN footprint equals the no-data footprint, removed the dead branch | all 3 rasters + 3 CSVs byte-identical before/after; JSON gained only 3 additive keys |
| 4 | Three documentation claims were wrong: a `layers_off_grid` key that does not exist, a stale DEM mosaic coordinate (`75.999722` vs measured `75.999583`), and "60 assertions" for a suite that runs 68 | targeted grep against the actual JSON schemas and actual script output | docs corrected to measured values; expected values **not** changed | `p3_check_consistency.py` 470/470; `p2_check_consistency.py` 68/68 |

Defect 4 detail: `14115/p141/row17 (printed Sl.17)` and `14115/p140/row15 (printed Sl.15)`
are **different records** from the precision-corrected `KER/WYD/58A03/2024/01`. They are now
pinned by 17 individual assertions so they cannot be conflated again. Record B is the single
`exclude_until_corrected` row (printed longitude ~77 km east, Tamil Nadu); record C is the
`review_boundary_uncertain` row at 2,836.1 m outside GADM, beyond the 1,578.6 m OSM envelope.

## Decisions taken in this pass

1. **Phase 1 processed products are inputs, not outputs.** `data/processed/geology/` and
   `data/processed/additional/` mix Phase 1 and Phase 3 outputs, so `data/processed/` is never
   deleted wholesale. The four prerequisites are checked by the runner.
2. **The OSM roads clip is treated as fixed input.** It comes from a live Overpass query;
   re-running its producer would silently change the input and make byte comparison meaningless.
3. **Rainfall warnings are scoped, not suppressed.** No global filter. Assertions guard the
   footprint, so a genuine empty-slice bug still fails.
4. **`rebuild_backup/`, `roundtrip_backup/` and `inventory_backup/` are not committed.**
   They are 230.8 MB copies of derived data; the SHA-256 manifests they are compared against
   *are* committed. Added to `.gitignore`.
5. **Comparison tolerances are declared, not implied**: raster pixels `atol 1e-6`, transform
   precision `1e-9`, GeoPackage geometry `1e-12`, CSV numerics `1e-9`.
6. **Volatile JSON keys are allow-listed by name** (`elapsed_s` and friends). A new key fails
   the comparison instead of being silently ignored.

## Commands and exit codes (final run)

| Command | Exit | Result |
|---|---|---|
| `powershell -ExecutionPolicy Bypass -File data\interim\p3\rebuild_all.ps1` | 0 | 11/11 stages: 23.5 / 2.5 / 2.4 / 25.6 / 5.2 / 95.1 / 18.7 / 2.4 / 7.1 / 1.6 / 18.9 s |
| `python data\interim\p3\compare_rebuild.py` | 0 | 68 IDENTICAL, 5 SAME CONTENT, 1 EXPECTED_ADDITIVE, 0 failed |
| `python data\interim\p3\compare_rebuild.py --baseline data\interim\p3\roundtrip_backup --out ...roundtrip.json` | 0 | 68 IDENTICAL, 6 SAME CONTENT, 0 failed |
| `python scripts\p3_verify_raw_immutable.py` | 0 | 431/431 files, 7,808.5 MB, 0 size / 0 hash mismatch |
| `python scripts\p3_verify_phase2_untouched.py` | 0 | 7/7 Phase 2 products byte-identical (disk and backup) |
| `python scripts\p3_check_consistency.py` | 0 | 470 assertions, all passed |
| `python scripts\p2_check_consistency.py` | 0 | 68 assertions, 68 pass / 0 fail |
| `python scripts\build_manifest.py` | 0 | 37 datasets written; idempotent (same SHA-256 on re-run) |
| `python scripts\p3_verify_all.py` | 0 | 6/6 gates passed |
| `git diff --check` | 0 | clean |

## What the metadata snapshots can and cannot prove

`inputs_metadata_before.json` vs `inputs_metadata.json` are field-identical, but they record
`size_bytes` and *sampled* value ranges — **not** a content hash. They are corroboration only.
The authoritative test is `scripts/p3_verify_raw_immutable.py`, which re-hashes every raw file
against `data/file_inventory.csv` (git-tracked, unmodified at `c5e2c42`).

## Not covered by reproducibility

- OSM roads clip: live Overpass snapshot, fixed input (see decision 2).
- `p3_inspect_inputs.py` samples large rasters rather than scanning them; it is an identity
  check on size/dims/CRS/transform/tags/sampled values, not a content hash.
- Determinism is established on one machine and one Python/GDAL/PROJ stack. Byte identity
  across different library versions is not claimed.

## Reproducing the Phase 2 "68 assertions" figure

`docs/PHASE2_PROGRESS.md` originally said 60. The committed script at `c5e2c42` runs 68 checks
(66 pass + 2 fail against the manifest *after* Phase 3 grew it to 37 rows). Reproduce with:

```powershell
cmd /c "git show c5e2c42:scripts/p2_check_consistency.py > data\interim\p3\p2_committed.py"
python data\interim\p3\p2_committed.py    # 66 PASS, 2 FAIL, exit 1
```
