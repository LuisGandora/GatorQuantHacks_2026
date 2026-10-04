# Runs the twelve pre-registered hypotheses unattended (Windows PowerShell 5.1), one stage at a time:
#   in-sample (all twelve, one after another) -> the one out-of-sample look (BH passers only) -> opencode judges (REVIEW.md).
# A lock file stops a second copy from overlapping. Re-running skips finished stages. Progress: runs\hyp\STATUS.txt.
# Usage, from the project folder:   powershell -ExecutionPolicy Bypass -File run_hyp.ps1
Set-Location $PSScriptRoot
New-Item -ItemType Directory -Force runs\hyp | Out-Null
$lock = "runs\hyp\RUNNING.lock"
if (Test-Path $lock) { Write-Host "Already running (remove $lock only if no python or opencode process is left)."; exit 1 }
Set-Content $lock (Get-Date -Format s)

function Status($msg) { $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm')  $msg"; Add-Content runs\hyp\STATUS.txt $line; Write-Host $line }
function Step($name, $cmd) {
    Status "START $name"
    cmd /c "$cmd"
    if ($LASTEXITCODE -ne 0) { Status "FAILED $name (exit $LASTEXITCODE); see its log in runs\hyp\"; return $false }
    Status "DONE  $name"
    return $true
}
function Logged($stage) { (Test-Path runs\ledger.jsonl) -and (Select-String -Path runs\ledger.jsonl -Pattern "`"stage`": `"$stage`"" -Quiet) }

try {
    if (-not (Logged "hyp_insample")) {
        if (-not (Step "in-sample, all twelve (1-3 h)" ".venv\Scripts\python hyp.py insample > runs\hyp\insample.log 2>&1")) { exit 1 }
    }
    if (-not (Logged "hyp_oos")) {
        if (-not (Step "out-of-sample look, BH passers only (once)" ".venv\Scripts\python hyp.py oos > runs\hyp\oos.log 2>&1")) { exit 1 }
    }
    if (-not (Test-Path runs\hyp\REVIEW.md)) {
        if (-not (Step "opencode review" "opencode run --command hyp --auto > runs\hyp\opencode.log 2>&1")) { exit 1 }
    }
    Status "ALL DONE. Read runs\hyp\REVIEW.md, then check its numbers against runs\hyp\RESULTS.md."
} finally {
    Remove-Item $lock -ErrorAction SilentlyContinue
}
