# Phase 5 Live Demonstration Guide

## What this demonstration runs

Run the verified Phase 5 pipeline from the project root. It re-extracts the configured predictor values, trains and evaluates the five spatial folds, generates the ROC and permutation-importance figures, rebuilds the susceptibility map, and checks that the outputs match the verified baseline. Allow about 10–20 minutes; do not start it during a short presentation unless there is enough time to wait for completion.

Open PowerShell in `C:\Major` and run:

```powershell
python -u scripts/p5_verify.py
```

The `-u` option makes progress visible as the script runs. Continue only after the final line reports `6/6 gates passed -- ALL PHASE 5 GATES PASSED`. The verification command reruns the actual model pipeline and confirms the regenerated outputs are byte-identical to the saved baseline.

## Show the generated outputs

After the run completes, open these generated figures from PowerShell:

```powershell
Start-Process .\data\processed\models\roc_curves.png
Start-Process .\data\processed\models\susceptibility_rf_baseline.png
Start-Process .\data\processed\models\permutation_importance.png
```

The ROC figure shows one curve per spatially held-out fold. The map shows the final Random Forest vote-share ranking over valid district cells. The importance figure shows held-out permutation importance. The GeoTIFF is the GIS raster output; the PNG is the convenient visual display.

## Results to point out

The saved evaluation reports per-fold spatially held-out presence-background ranking metrics:

| Fold | ROC-AUC | Average precision |
|---|---:|---:|
| 0 | 0.8674 | 0.3517 |
| 1 | 0.8712 | 0.5458 |
| 2 | 0.9263 | 0.6168 |
| 3 | 0.7882 | 0.3200 |
| 4 | 0.7720 | 0.3348 |

Fold 2 is marginal because it contains only five clusters. These metrics compare mapped-event points with sampled background points. Background means no event was mapped there in the available inventory; it does not mean confirmed stable terrain. The inventory is 92.3% from 2018, and temporal transfer has not been evaluated.

Average precision summarizes precision across thresholds; it is not precision at one selected threshold. Do not call ROC-AUC “accuracy,” and do not present these values as accuracy on all Wayanad landslides or performance against confirmed absences. The map is a relative susceptibility ranking conditional on the observed inventory, not a calibrated probability or a prediction of when a landslide will occur.

## Files

- Run command: `scripts/p5_verify.py`
- Per-fold metrics: `data/processed/models/fold_metrics.json`
- Verification evidence: `data/interim/p5/verify_p5.json`
- ROC curves: `data/processed/models/roc_curves.png`
- Susceptibility ranking map: `data/processed/models/susceptibility_rf_baseline.png`
- GIS raster: `data/processed/models/susceptibility_rf_baseline_30m.tif`
- Permutation importance: `data/processed/models/permutation_importance.png`
- Full methods and limitations: `docs/PHASE5_PROGRESS.md`
