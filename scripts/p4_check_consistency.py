"""Assert that the Phase 4 documentation matches the Phase 4 data products.

A number in a report is a claim. If a script changes the data and the report is not
updated, this fails loudly instead of letting the two drift. Wherever possible the
expected string is derived from the data files themselves (e.g. the fold-positive list
is formatted from fold_summary.json and then searched for in the docs), so a data change
cannot pass next to a stale document.

Sections:
  1  config authority      run-config sha256 == configs/p4_sampling.json on disk
  2  eligibility audit     the 9-decision partition, the three special records
  3  background sampling   counts, uniqueness, exact separation recomputed
  4  fold invariants       0 mixed blocks, groups/clusters atomic, support, buffer
                           recomputed by point_id from the saved tables
  5  docs vs data          measured values (formatted from the JSONs) appear in the docs
  6  disclaimers           required limitation sentences present
  7  banned vocabulary     no line claims positive prediction or a performance figure
  8  manifest              P4-01..P4-06 present, unique ids, doc claim pinned to row count

Run:  python scripts/p4_check_consistency.py
"""
import csv
import hashlib
import json
import pathlib
import re
import sys

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MAIN = pathlib.Path(r"C:\Major")
SAMP = MAIN / "data" / "processed" / "sampling"
DOCS = MAIN / "docs"
CFG_PATH = MAIN / "configs" / "p4_sampling.json"

fails = []


def check(label, actual, expected):
    ok = actual == expected
    print(f"{'PASS' if ok else 'FAIL'}  {label:58s} {actual!r:>12} (expected {expected!r})")
    if not ok:
        fails.append(label)


def contains(label, haystack, needle):
    ok = needle in haystack
    print(f"{'PASS' if ok else 'FAIL'}  {label:58s} {'found' if ok else 'MISSING'}: {needle!r}")
    if not ok:
        fails.append(label)


def norm(text: str) -> str:
    """Collapse whitespace so a needle may span markdown line-wraps."""
    return " ".join(text.split())


def sha256(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


cfg = json.loads(CFG_PATH.read_text(encoding="utf-8"))
run = json.loads((SAMP / "sampling_run_config.json").read_text(encoding="utf-8"))
fs = json.loads((SAMP / "fold_summary.json").read_text(encoding="utf-8"))
es = json.loads((SAMP / "eligibility_summary.json").read_text(encoding="utf-8"))
audit = pd.read_csv(SAMP / "eligibility_audit.csv", keep_default_na=False)
bg = pd.read_csv(SAMP / "background_samples.csv")
fa = pd.read_csv(SAMP / "fold_assignments.csv")
dr = pd.read_csv(SAMP / "fold_drops.csv")
man = list(csv.DictReader(open(DOCS / "data_manifest.csv", encoding="utf-8")))

DOC_NAMES = ["MODELLING_TARGET_DECISIONS.md", "SAMPLING_STRATEGY_REPORT.md",
             "SPATIAL_VALIDATION_REPORT.md", "PHASE4_PROGRESS.md"]
docs_raw = {n: (DOCS / n).read_text(encoding="utf-8") for n in DOC_NAMES}
docs = {n: norm(t) for n, t in docs_raw.items()}
target, sampling, validation, progress = (docs[n] for n in DOC_NAMES)

# ---- 1. config authority ----------------------------------------------------
print("--- config authority ---")
check("run-config names the config file", run["config_file"], "configs/p4_sampling.json")
check("run-config sha256 matches the file on disk", run["config_sha256"], sha256(CFG_PATH))
check("seed recorded in config", cfg["random_seed"], 20261026)
check("seed recorded in run-config", run["random_seed"], 20261026)
sp = cfg["spatial_validation"]
check("exclusion radius", cfg["background"]["exclusion_radius_m"], 100.0)
check("sampling density", cfg["background"]["sampling_density_per_km2"], 1.0)
check("block size", sp["block_size_m"], 3000)
check("buffer gap", sp["buffer_gap_m"], 1000)
check("clustering threshold", sp["clustering_threshold_m"], 1000)
check("n folds", sp["n_folds"], 5)
check("min test positives", sp["min_test_positives"], 45)
check("min test clusters", sp["min_test_clusters"], 5)

# ---- 2. eligibility audit ---------------------------------------------------
print("\n--- eligibility audit ---")
check("all records audited", len(audit), 468)
check("one reason per record",
      int((audit["p4_reason"].astype(str).str.strip() == "").sum()), 0)
dec = audit["p4_use"].value_counts()
check("POSITIVE_EVENT", int(dec.get("POSITIVE_EVENT", 0)), 363)
check("POSITIVE_EVENT_DUPLICATE", int(dec.get("POSITIVE_EVENT_DUPLICATE", 0)), 1)
check("EXCLUDE_BOUNDARY_UNCERTAIN", int(dec.get("EXCLUDE_BOUNDARY_UNCERTAIN", 0)), 5)
check("EXCLUDE_UNDATED_SITE", int(dec.get("EXCLUDE_UNDATED_SITE", 0)), 78)
check("EXCLUDE_NOT_IN_DISTRICT", int(dec.get("EXCLUDE_NOT_IN_DISTRICT", 0)), 12)
check("EXCLUDE_PRE_2000", int(dec.get("EXCLUDE_PRE_2000", 0)), 6)
check("EXCLUDE_WIDEN_REQUIRED", int(dec.get("EXCLUDE_WIDEN_REQUIRED", 0)), 1)
check("EXCLUDE_DISTRICT_CENTROID", int(dec.get("EXCLUDE_DISTRICT_CENTROID", 0)), 1)
check("EXCLUDE_COORDINATE_ERROR", int(dec.get("EXCLUDE_COORDINATE_ERROR", 0)), 1)
check("EXCLUDE_SUPERSEDED", int(dec.get("EXCLUDE_SUPERSEDED", 0)), 0)
pos = audit[audit["p4_use"] == "POSITIVE_EVENT"]
check("positives are one per event group",
      int(pos["event_group_id"].nunique()), len(pos))
yr = pd.to_numeric(pos["event_year"], errors="coerce")
y18 = int((yr == 2018).sum())
check("positives dated 2018", y18, 335)
check("positives not dated 2018", len(pos) - y18, 28)
unc = pos["positional_uncertainty_m"].astype(float)
check("uncertainty min/median/max",
      (float(unc.min()), float(unc.median()), float(unc.max())), (10.0, 30.0, 30.0))
a = audit.set_index("source_record_id")
check("record A eligible positive", a.loc["KER/WYD/58A03/2024/01", "p4_use"],
      "POSITIVE_EVENT")
check("record B coordinate-error exclusion",
      a.loc["14115/p141/row17 (printed Sl.17)", "p4_use"], "EXCLUDE_COORDINATE_ERROR")
check("record C boundary-uncertain exclusion",
      a.loc["14115/p140/row15 (printed Sl.15)", "p4_use"], "EXCLUDE_BOUNDARY_UNCERTAIN")
check("superseded flags carried, not a class",
      int(audit["p4_flags"].astype(str).str.contains("superseded").sum()), 33)

# ---- 3. background sampling --------------------------------------------------
print("\n--- background sampling ---")
check("background sample count", len(bg), run["background_samples"])
check("sample ids unique", int(bg["sample_id"].duplicated().sum()), 0)
check("one sample per grid cell", int(bg.duplicated(["row", "col"]).sum()), 0)
check("eligible cells", run["eligible_cells"], 2330499)
check("eligible km2", run["eligible_km2"], 2097.45)
check("eligible pct of district", run["eligible_pct_of_district"], 98.895)
check("band cells kept by exact test", run["separation"]["band_cells_exact"], 3348)
check("band cells rejected by exact test",
      run["separation"]["band_cells_rejected_by_exact_test"], 435)
check("max positive-to-own-cell offset",
      run["separation"]["max_positive_to_own_cell_centre_m"], 20.46)
pxy = fa.loc[fa["role"] == "positive", ["x_32643", "y_32643"]].to_numpy(float)
bxy = bg[["x_32643", "y_32643"]].to_numpy(float)
sep_recomputed = float(cKDTree(pxy).query(bxy, k=1)[0].min())
check("exact separation recomputed >= radius", sep_recomputed >= 100.0, True)
check("exact separation matches recorded",
      round(sep_recomputed, 1), run["separation"]["exact_min_after_sampling_m"])

# ---- 4. fold invariants (recomputed from the saved tables) -------------------
print("\n--- fold invariants ---")
check("analysis points", len(fa), 2460)
check("positives", int((fa["role"] == "positive").sum()), 363)
check("background", int((fa["role"] == "background").sum()), 2097)
check("point ids unique", int(fa["point_id"].duplicated().sum()), 0)
mixed_group = int((fa[fa["role"] == "positive"].groupby("event_group_id")["fold"]
                   .nunique() > 1).sum())
mixed_clu = int((fa[fa["role"] == "positive"].groupby("cluster_id")["fold"]
                 .nunique() > 1).sum())
mixed_block = int((fa.groupby("block_id")["fold"].nunique() > 1).sum())
check("event groups split across folds", mixed_group, 0)
check("clusters split across folds", mixed_clu, 0)
check("blocks split across folds (recomputed)", mixed_block, 0)
check("fold script reports 0 mixed blocks", fs["mixed_fold_blocks"], 0)
counts = [int(((fa["fold"] == f) & (fa["role"] == "positive")).sum()) for f in range(5)]
check("per-fold positives", counts, [52, 121, 84, 54, 52])
check("spread of fold positives", max(counts) - min(counts), 69)
clus = [int(fa[(fa["fold"] == f) & (fa["role"] == "positive")]["cluster_id"].nunique())
        for f in range(5)]
check("every fold meets 45 positives", min(counts) >= 45, True)
check("every fold meets 5 clusters", min(clus) >= 5, True)
check("fold 2 is the marginal fold (5 clusters)", clus[2], 5)
check("clusters total", int(fa[fa["role"] == "positive"]["cluster_id"].nunique()), 76)
check("blocks total", int(fa["block_id"].nunique()), 271)

gap = float(sp["buffer_gap_m"])
xy = fa[["x_32643", "y_32643"]].to_numpy(float)
drop_issues, min_kept_overall = [], float("inf")
for f in range(5):
    is_test = (fa["fold"] == f).to_numpy()
    rest_idx = np.flatnonzero(~is_test)
    d_rest = cKDTree(xy[is_test]).query(xy[rest_idx], k=1)[0]
    dropped_idx = rest_idx[d_rest <= gap]
    kept_min = float(d_rest[d_rest > gap].min())
    min_kept_overall = min(min_kept_overall, kept_min)
    rows = dr[dr["fold"] == f]
    if set(rows["point_id"]) != set(fa.iloc[dropped_idx]["point_id"]):
        drop_issues.append(f"fold {f} point set")
    rec = dict(zip(fa.iloc[dropped_idx]["point_id"], d_rest[d_rest <= gap]))
    if any(abs(float(r.distance_to_test_m) - float(rec[r.point_id])) > 0.11
           for r in rows.itertuples()):
        drop_issues.append(f"fold {f} distances")
check("fold_drops match recomputation (sets+distances, by point_id)",
      drop_issues, [])
check("total drops", len(dr), fs["totals"]["dropped_from_train"])
check("total drops recomputed", len(dr), 418)
check("dropped positive rows", int((dr["role"] == "positive").sum()), 26)
check("dropped background rows", int((dr["role"] == "background").sum()), 392)
check("unique dropped points", int(dr["point_id"].nunique()), 395)
check("every drop within the gap", bool((dr["distance_to_test_m"] <= gap).all()), True)
check("retained min gap > configured",
      min_kept_overall > gap, True)
check("retained min gap value", round(min_kept_overall, 1), 1001.3)
check("run seed in fold summary", fs["random_seed"], 20261026)
check("chosen candidate seed", fs["assignment"]["chosen_candidate_seed"], 20261028)

# ---- 5. docs vs data (needles formatted from the data files) -----------------
print("\n--- docs vs data ---")
fold_list = "[" + ", ".join(str(v) for v in counts) + "]"
contains("progress quotes the base commit", progress, "570af94")
contains("progress quotes fold positives", progress, fold_list)
contains("validation quotes fold positives", validation, fold_list)
contains("target quotes positive count", target, f"{len(pos)} positives")
contains("target quotes 2018 count", target, str(y18))
contains("target quotes non-2018 count", target, "28 non-2018")
contains("target quotes 2018 share", target, "92.3")
contains("target quotes uncertainty triplet",
         target, "min 10 m, median 30 m, max 30 m")
contains("target quotes temporal verdict", target, "not viable")
contains("sampling quotes eligible km2", sampling,
         f"{run['eligible_km2']:,.2f} km²")
contains("sampling quotes eligible pct", sampling,
         f"{run['eligible_pct_of_district']} %")
contains("sampling quotes sample count", sampling, f"{run['background_samples']:,}")
contains("sampling quotes per-positive ratio", sampling,
         f"{run['background_per_positive']}")
contains("sampling quotes exact separation", sampling,
         f"{run['separation']['exact_min_after_sampling_m']} m")
contains("sampling quotes band rejections", sampling,
         str(run["separation"]["band_cells_rejected_by_exact_test"]))
contains("sampling quotes max offset", sampling,
         f"{run['separation']['max_positive_to_own_cell_centre_m']} m")
contains("sampling quotes conservative margin", sampling,
         f"{run['separation']['conservative_margin_m']} m")
contains("sampling quotes the seed", sampling, str(cfg["random_seed"]))
contains("sampling quotes config sha prefix", sampling,
         run["config_sha256"][:8])
contains("validation quotes clusters", validation,
         f"{fs['clusters']} clusters")
contains("validation quotes units", validation, str(fs["block_units"]))
contains("validation quotes blocks", validation, str(fs["blocks"]))
contains("validation quotes chosen seed", validation,
         str(fs["assignment"]["chosen_candidate_seed"]))
contains("validation quotes retained gap", validation,
         f"{fs['invariants']['min_train_to_test_m']:,.1f} m")
contains("validation quotes zero-gap cross-fold distance", validation, "150.0")
contains("validation quotes drop total", validation,
         str(fs["totals"]["dropped_from_train"]))
contains("progress quotes gate count", progress, "8 / 8 gates")
contains("progress quotes manifest count", progress, f"{len(man)} datasets")
contains("progress quotes consistency suites", progress, "470 / 470")

# ---- 6. required disclaimers -------------------------------------------------
print("\n--- required disclaimers ---")
contains("target: not a forecast", target, "not a forecast")
contains("target: ranking, not a probability", target, "ranking, not a probability")
contains("target: background is absence of mapping", target, "absence of")
contains("target: temporal holdout absent", target, "No viable temporal holdout")
contains("sampling: presence-background named", sampling, "presence-background")
contains("sampling: background not confirmed stable", sampling, "not confirmed stable")
contains("sampling: no fabricated negatives", sampling, "no fabricated negatives")
contains("sampling: separation target is coordinates", sampling,
         "recorded positive coordinate")
contains("validation: independence not asserted", validation, "not asserted")
contains("validation: fold 2 marginal", validation, "5 distinct clusters")
contains("validation: design not performance", validation, "design properties, not performance")
contains("progress: no model exists", progress,
         "No model, training table, synthetic event, susceptibility map or performance "
         "metric exists")

# ---- 7. banned vocabulary ----------------------------------------------------
print("\n--- banned vocabulary (negation in the same sentence allowed) ---")
# Markdown emphasis is stripped and text is normalised to sentences, so a negation
# and its term never fall on different sides of a line-wrap. "predictor" is a design
# word (predictor layers/cells) and is not a predictive claim.
NEG_RE = re.compile(r"\b(not|never|cannot|no|nothing|none|without|refuse|lacks?|"
                    r"absent|nor)\b", re.IGNORECASE)
banned_re = re.compile(r"\b(forecast\w*|predict(?!or)\w*|prediction\w*|warning\w*|"
                       r"accuracy|auc\b|f1\b|roc\b)\b", re.IGNORECASE)
offenders = []
for name, raw in docs_raw.items():
    plain = re.sub(r"[*_`\u201c\u201d]", "", norm(raw))
    for sentence in re.split(r"(?<=[.!?])\s+", plain):
        if banned_re.search(sentence) and not NEG_RE.search(sentence):
            offenders.append(f"{name}: {sentence[:100]}")
check("no un-negated predictive/performance claims", len(offenders), 0)
if offenders:
    for o in offenders:
        print("      " + o.encode("ascii", "replace").decode("ascii"))

# ---- 8. manifest --------------------------------------------------------------
print("\n--- manifest ---")
ids = [r["dataset_id"] for r in man]
check("manifest columns", len(man[0]), 16)
check("manifest unique ids", len(ids), len(set(ids)))
check("P4 rows present", [f"P4-{i:02d}" for i in range(1, 7)], [i for i in ids if i.startswith("P4-")])
contains("progress pins the manifest row count", progress, f"{len(man)} datasets")
bad = [r["dataset_id"] for r in man
       if not (MAIN / r["local_path"]).exists()
       or r["validation_status"] != "VERIFIED"
       or len(r["limitations"]) <= 40]
check("P4 manifest rows healthy (path, status, limitations)",
      [i for i in bad if i.startswith("P4-")], [])

print("\n" + "=" * 70)
if fails:
    print(f"{len(fails)} CHECK(S) FAILED")
    for f in fails:
        print("  - " + f)
    raise SystemExit(1)
print("all Phase 4 consistency checks passed -- documentation matches the Phase 4 outputs")
