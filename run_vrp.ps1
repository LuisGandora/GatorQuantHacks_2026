# Runs the rest of the variance-premium experiment unattended (Windows PowerShell 5.1):
#   map (long) -> opencode judges it (V4 review) -> out-of-sample look (long, once) -> opencode writes it up (V6).
# The long Python steps run here, not inside an agent, so no agent timeout can kill them or start them twice.
# Usage, from the project folder:   powershell -ExecutionPolicy Bypass -File run_vrp.ps1
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Step($name, $cmd) {
    Write-Host "== $name  ($(Get-Date -Format 'HH:mm'))"
    cmd /c "$cmd"
    if ($LASTEXITCODE -ne 0) { Write-Host "!! $name failed (exit $LASTEXITCODE). See the log in runs\vrp\ and paste it into chat."; exit 1 }
}

if (-not (Test-Path runs\vrp\map_insample.csv)) {
    Step "V3 in-sample map (1-2 h)" ".venv\Scripts\python vrp.py map > runs\vrp\map.log 2>&1"
}
if (-not (Test-Path runs\vrp\REVIEW.md)) {
    Step "V4 review by opencode" "opencode run --command vrp --auto"
}
$looked = Select-String -Path runs\ledger.jsonl -Pattern '"stage": "vrp_oos"' -Quiet
if (-not $looked) {
    Step "V5 out-of-sample look (30-60 min, once)" ".venv\Scripts\python vrp.py oos > runs\vrp\oos.log 2>&1"
}
Step "V6 write-up by opencode" "opencode run --command vrp --auto"
Write-Host "== done ($(Get-Date -Format 'HH:mm')). Check the Extension section of runs\FINDINGS.md against runs\vrp\MAP.md."
