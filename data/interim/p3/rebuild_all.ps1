# Rebuild every Phase 3 derived product from raw inputs, in stage order.
#
# ERROR POLICY
#   $ErrorActionPreference is "Continue", not "Stop", by design. PowerShell promotes a
#   line written to *stderr* by a native command into a terminating error under "Stop",
#   even when the process exits 0. That is how the first attempt at this rebuild died
#   immediately after rainfall: the stage had succeeded, but numpy had written a
#   RuntimeWarning to stderr.
#
#   Success is therefore judged by $LASTEXITCODE alone, checked immediately after every
#   python invocation. The runner stops at the FIRST failing stage rather than
#   continuing, because later stages consume earlier outputs and would otherwise run on
#   missing inputs and produce misleading errors.
#
#   The rainfall warnings themselves were also fixed at source (scripts/p3_rainfall.py
#   now counts the all-NaN Pacific/Arabian-Sea window cells, asserts the nodata
#   footprint, and scopes the expected numpy warnings to those reductions). They remain
#   documented in that script and recorded in rainfall_validation.json. They are not
#   suppressed globally, and warnings from any other stage are still printed.
#
#   PowerShell-native commands that must succeed carry an explicit -ErrorAction Stop;
#   only the native-command invocation is left to exit-code checking.
#
# PREREQUISITES
#   Phase 3 consumes four Phase 1 processed products and does not re-derive them:
#     geology\glim_wayanad_clip.gpkg          <- scripts\clip_geology.py        (offline)
#     geology\glim_wayanad_lithology_summary.csv <- scripts\clip_geology.py     (offline)
#     additional\osm_roads_wayanad_clip.gpkg  <- scripts\acquire_osm_roads.py   (LIVE Overpass)
#     additional\hydrorivers_wayanad_clip.gpkg<- scripts\acquire_hydrorivers.py (download-if-absent)
#   data\processed\geology\ and data\processed\additional\ are MIXED directories: they
#   hold Phase 1 outputs beside Phase 3 outputs. Never delete them wholesale -- doing so
#   removes inputs, not just outputs. The gate below fails with an explicit message
#   instead of a traceback from deep inside a stage.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File data\interim\p3\rebuild_all.ps1
#   powershell -ExecutionPolicy Bypass -File data\interim\p3\rebuild_all.ps1 -From p3_geology.py

param(
  [string]$From = "p3_inspect_inputs.py"
)

$ErrorActionPreference = "Continue"
$log = "data\interim\p3\rebuild_run.log"
if (-not (Test-Path $log)) {
  New-Item -ItemType File -Path $log -ErrorAction Stop | Out-Null
}

# --- Phase 1 processed prerequisites -----------------------------------------
$prereqs = @(
  "data\processed\geology\glim_wayanad_clip.gpkg",
  "data\processed\geology\glim_wayanad_lithology_summary.csv",
  "data\processed\additional\osm_roads_wayanad_clip.gpkg",
  "data\processed\additional\hydrorivers_wayanad_clip.gpkg"
)
$missing = $prereqs | Where-Object { -not (Test-Path $_) }
if ($missing) {
  Write-Output "MISSING PHASE 1 PREREQUISITES (these are inputs, do not delete):"
  $missing | ForEach-Object { Write-Output "  $_" }
  exit 3
}

$py = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $py) { Write-Output "python not found on PATH"; exit 2 }
$pyVersion = (cmd /c "python --version 2>&1")
"HOST python: $pyVersion at $($py.Source)" | Out-File -Append -Encoding utf8 $log

$stages = @(
  "p3_inspect_inputs.py",
  "p3_build_grid.py",
  "p3_boundary_diagnostics.py",
  "p3_dem.py",
  "p3_landcover.py",
  "p3_rainfall.py",
  "p3_soil.py",
  "p3_geology.py",
  "p3_additional.py",
  "p3_inventory_suitability.py",
  "p3_verify_processed.py"
)

$startIdx = [array]::IndexOf($stages, $From)
if ($startIdx -lt 0) { Write-Output "unknown stage: $From"; exit 2 }

for ($i = $startIdx; $i -lt $stages.Count; $i++) {
  $s = $stages[$i]
  $t0 = Get-Date

  # Record the exact script bytes that produced each output, so a later comparison can
  # prove which code revision was run.
  $sha = (Get-FileHash "scripts\$s" -Algorithm SHA256 -ErrorAction Stop).Hash
  "=== $s  sha256=$sha" | Out-File -Append -Encoding utf8 $log

  # cmd /c redirects natively: PowerShell's own *>> mangles native-command progress
  # output (carriage returns and non-ASCII) into unreadable log noise.
  cmd /c "python scripts\$s >> $log 2>&1"
  $code = $LASTEXITCODE

  $dt = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
  "RUN $s exit=$code ${dt}s" | Out-File -Append -Encoding utf8 $log
  Write-Output "RUN $s exit=$code ${dt}s"

  if ($code -ne 0) {
    # Fail fast: later stages consume this stage's outputs.
    Write-Output "FAILED at $s (exit=$code). Later stages not attempted; see $log"
    exit 1
  }
}

Write-Output "rebuild done: $($stages.Count - $startIdx) stage(s) completed"
exit 0
