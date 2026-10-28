"""Phase 5 — Random Forest baseline: per-fold training and evaluation.

Uses ONLY the committed Phase 4 points and folds. For each fold f in 0..4:

  test(f)  = every point with fold == f                         (never resplit)
  train(f) = every point with fold != f, MINUS the point_ids in
             fold_drops.csv with fold == f (the committed 1,000 m buffer)

Constructed counts are asserted against fold_summary.json BEFORE fitting; any
mismatch aborts the run. One fixed RandomForest configuration (configs/
p5_baseline.json); no tuning, no competing models, no synthetic data.

Outputs (data/processed/models/):
  fold_metrics.json        per-fold spatially held-out presence-background
                           RANKING metrics (roc_auc, average_precision) + fold
                           support, mean/-sd, fold-2 marginal flag, permutation
                           importances, limitations, versions, provenance
  fold_<f>_rf.joblib       the five fold models (fitted on the other folds)
  roc_curves.png           per-fold ROC curves (figure only; metrics live in JSON)
  permutation_importance.png  mean +/- sd across folds (interpretive)

The numbers characterise RANKING under presence-background labels; they are not
accuracy on all Wayanad landslides, not performance on confirmed absences, and
no pooled score is reported as if folds were independent.

Run:  python scripts/p5_train_baseline.py
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT / "configs" / "p5_baseline.json").read_text(encoding="utf-8"))
PROC = ROOT / "data" / "processed"
MODELS = PROC / "models"
FEAT_CSV = MODELS / "features_point_table.csv"
OUT_JSON = MODELS / "fold_metrics.json"
PROV_COLS = ["point_id", "role", "label", "event_group_id", "event_year",
             "cluster_id", "block_id", "fold", "x_32643", "y_32643",
             "lon_4326", "lat_4326"]


def sha256(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_png(fig, path: pathlib.Path) -> None:
    """Deterministic PNG: matplotlib output re-saved via PIL with metadata
    stripped, so re-running the script reproduces the file byte for byte."""
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    from PIL import Image
    Image.open(buf).save(path, format="png")
    plt.close(fig)


def main() -> int:
    MODELS.mkdir(parents=True, exist_ok=True)
    spec = CFG["features"]["spec"]
    feat_names = [e["name"] for e in spec]
    mcfg = CFG["model"]

    tab = pd.read_csv(FEAT_CSV)
    fa = pd.read_csv(PROC / "sampling" / "fold_assignments.csv")
    drops = pd.read_csv(PROC / "sampling" / "fold_drops.csv")
    fs = json.loads((PROC / "sampling" / "fold_summary.json").read_text(encoding="utf-8"))

    # provenance must be the Phase 4 authority, carried through unchanged
    assert tab[PROV_COLS].equals(fa[PROV_COLS]), "features table provenance != fold_assignments"
    assert list(tab.columns)[len(PROV_COLS):] == feat_names, "feature order != config order"
    X_all = tab[feat_names].to_numpy(dtype=float)
    y_all = tab["label"].to_numpy(dtype=int)
    assert set(np.unique(y_all)) == {0, 1}

    # ---- construct folds and assert against fold_summary BEFORE fitting ------
    folds = []
    for f in range(fs["n_folds"]):
        test_mask = (tab["fold"].to_numpy() == f)
        train_mask = ~test_mask
        drop_ids = set(drops.loc[drops["fold"] == f, "point_id"])
        ids = tab["point_id"].to_numpy()
        is_drop = np.isin(ids, sorted(drop_ids))
        assert set(ids[is_drop & test_mask]) == set(), f"fold {f}: a test point is in its own drop list"
        train_mask &= ~is_drop
        s = fs["folds"][f]
        tp, tb = int((y_all[test_mask] == 1).sum()), int((y_all[test_mask] == 0).sum())
        rp, rb = int((y_all[train_mask] == 1).sum()), int((y_all[train_mask] == 0).sum())
        assert (tp, tb, rp, rb) == (s["test_positives"], s["test_background"],
                                    s["train_positives"], s["train_background"]), \
            f"fold {f}: counts {(tp, tb, rp, rb)} != fold_summary {(s['test_positives'], s['test_background'], s['train_positives'], s['train_background'])}"
        assert len(drop_ids) == s["dropped_from_train"], f"fold {f}: drop count mismatch"
        folds.append({"fold": f, "train_mask": train_mask, "test_mask": test_mask,
                      "summary": s})
    print("fold construction matches fold_summary.json for all 5 folds")

    # ---- per-fold fit + held-out ranking metrics -----------------------------
    rows, models = [], []
    for fo in folds:
        f, trm, tem = fo["fold"], fo["train_mask"], fo["test_mask"]
        clf = RandomForestClassifier(
            n_estimators=mcfg["n_estimators"], criterion=mcfg["criterion"],
            min_samples_leaf=mcfg["min_samples_leaf"], max_features=mcfg["max_features"],
            bootstrap=mcfg["bootstrap"], class_weight=mcfg["class_weight"],
            random_state=mcfg["random_state"], n_jobs=mcfg["n_jobs"])
        clf.fit(X_all[trm], y_all[trm])
        proba = clf.predict_proba(X_all[tem])[:, 1]
        yte = y_all[tem]
        auc = float(roc_auc_score(yte, proba))
        ap = float(average_precision_score(yte, proba))
        fpr, tpr, _ = roc_curve(yte, proba)
        models.append((f, clf, fpr, tpr, auc))
        rows.append({"fold": f, "roc_auc": auc, "average_precision": ap,
                     "test_positives": fo["summary"]["test_positives"],
                     "test_background": fo["summary"]["test_background"],
                     "test_clusters": fo["summary"]["test_clusters"],
                     "train_positives": fo["summary"]["train_positives"],
                     "train_background": fo["summary"]["train_background"],
                     "dropped_from_train": fo["summary"]["dropped_from_train"]})
        joblib.dump(clf, MODELS / f"fold_{f}_rf.joblib")
        print(f"fold {f}: roc_auc={auc:.4f} average_precision={ap:.4f} "
              f"(test {rows[-1]['test_positives']}+/{rows[-1]['test_background']}-, "
              f"{rows[-1]['test_clusters']} clusters)")

    aucs = np.array([r["roc_auc"] for r in rows])
    aps = np.array([r["average_precision"] for r in rows])

    # ---- permutation importance on each held-out fold (interpretive) ---------
    picfg = CFG["permutation_importance"]
    imp = []
    for (f, clf, _, _, _), fo in zip(models, folds):
        pi = permutation_importance(
            clf, X_all[fo["test_mask"]], y_all[fo["test_mask"]],
            scoring=picfg["scoring"], n_repeats=picfg["n_repeats"],
            random_state=picfg["random_state"], n_jobs=1)
        imp.append(pi.importances_mean)
        print(f"fold {f}: permutation importance computed")
    imp = np.array(imp)          # folds x features
    imp_mean = imp.mean(axis=0)  # unweighted across folds (correlated folds)
    imp_sd = imp.std(axis=0, ddof=1)

    # ---- figures --------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(5.6, 5.2), dpi=110)
    for f, _, fpr, tpr, auc in models:
        ax.plot(fpr, tpr, lw=1.4, label=f"fold {f} (AUC {auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=0.8)
    ax.set_xlabel("false positive rate (background points)")
    ax.set_ylabel("true positive rate (event points)")
    ax.set_title("RF baseline — spatially held-out ROC per fold\n"
                 "presence-background ranking, correlated folds")
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout()
    save_png(fig, MODELS / "roc_curves.png")

    order = np.argsort(imp_mean)
    fig, ax = plt.subplots(figsize=(7.4, 9.2), dpi=110)
    ax.barh(np.array(feat_names)[order], imp_mean[order],
            xerr=imp_sd[order], color="#4878a8", ecolor="#333333", lw=0.6)
    ax.set_xlabel("mean decrease in held-out ROC-AUC under permutation\n"
                  "(mean +/- sd across the 5 correlated folds; interpretive)")
    ax.set_title("RF baseline — permutation importance on held-out folds")
    fig.tight_layout()
    save_png(fig, MODELS / "permutation_importance.png")

    # ---- metrics payload ------------------------------------------------------
    marginal = [f for f in range(fs["n_folds"])
                if fs["folds"][f]["test_clusters"] <= fs["min_test_clusters"]]
    payload = {
        "verdict": "PER-FOLD EVALUATION COMPLETE",
        "model_type": mcfg["type"],
        "model_params": {k: v for k, v in mcfg.items() if k != "rationale"},
        "model_rationale": mcfg["rationale"],
        "random_seed": CFG["random_seed"],
        "feature_names": feat_names,
        "class_handling": CFG["class_handling"],
        "fold_usage": CFG["fold_usage"],
        "metric_interpretation": CFG["metrics"]["interpretation"],
        "fold_metrics": rows,
        "mean_of_folds": {"roc_auc": float(aucs.mean()), "roc_auc_sd": float(aucs.std(ddof=1)),
                          "average_precision": float(aps.mean()),
                          "average_precision_sd": float(aps.std(ddof=1)),
                          "note": "unweighted mean over 5 spatially adjacent, correlated "
                                  "folds; NOT an independent-replication estimate and not "
                                  "a pooled score"},
        "marginal_folds": [{"fold": f,
                            "reason": f"{fs['folds'][f]['test_clusters']} distinct test "
                                      f"clusters (configured minimum is "
                                      f"{fs['min_test_clusters']}); treat as marginal"}
                           for f in marginal],
        "permutation_importance": {
            "scoring": picfg["scoring"], "n_repeats": picfg["n_repeats"],
            "random_state": picfg["random_state"],
            "computed_on": picfg["computed_on"],
            "importance": {n: {"mean": float(imp_mean[i]), "sd": float(imp_sd[i])}
                           for i, n in enumerate(feat_names)},
        },
        "limitations": CFG["limitations"],
        "inputs_sha256": {
            "configs/p5_baseline.json": sha256(ROOT / "configs" / "p5_baseline.json"),
            "data/processed/models/features_point_table.csv": sha256(FEAT_CSV),
            "data/processed/sampling/fold_assignments.csv":
                sha256(PROC / "sampling" / "fold_assignments.csv"),
            "data/processed/sampling/fold_drops.csv":
                sha256(PROC / "sampling" / "fold_drops.csv"),
            "data/processed/sampling/fold_summary.json":
                sha256(PROC / "sampling" / "fold_summary.json"),
        },
        "model_files_sha256": {f"fold_{f}_rf.joblib": sha256(MODELS / f"fold_{f}_rf.joblib")
                               for f in range(fs["n_folds"])},
        "versions": {"python": sys.version.split()[0], "numpy": np.__version__,
                     "pandas": pd.__version__, "sklearn": sklearn.__version__,
                     "joblib": joblib.__version__, "matplotlib": matplotlib.__version__},
        "not_claimed": [
            "no pooled headline score is reported: folds are spatially adjacent and correlated",
            "metrics are presence-background ranking metrics, not accuracy on all Wayanad "
            "landslides and not performance on confirmed absences",
            "the inventory is 92.3% single-year (2018); scores characterise that event population",
            "background labels mean 'no mapped event in the available inventory', not stable ground",
        ],
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print("=" * 78)
    print("per-fold ROC-AUC :", ", ".join(f"{r['roc_auc']:.4f}" for r in rows),
          f"| mean {aucs.mean():.4f} +/- {aucs.std(ddof=1):.4f}")
    print("per-fold AP      :", ", ".join(f"{r['average_precision']:.4f}" for r in rows),
          f"| mean {aps.mean():.4f} +/- {aps.std(ddof=1):.4f}")
    print("marginal fold(s) :", marginal, "- only 5 distinct clusters; flagged")
    print(f"written -> fold_metrics.json, 5x fold_<f>_rf.joblib, roc_curves.png, "
          f"permutation_importance.png in {MODELS.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
