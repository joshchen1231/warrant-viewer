# Starts the warrant-viewer backend (uvicorn) on 127.0.0.1:8000.
# Usage (PowerShell):  .\start-server.ps1
# Stops any previous instance started by this script (pid stored in data\server.pid),
# then launches a fresh one and waits until /api/health responds.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$data = Join-Path $root "data"

if (-not (Test-Path -LiteralPath $data)) {
    New-Item -ItemType Directory -Path $data -Force | Out-Null
}

$pidFile = Join-Path $data "server.pid"
if (Test-Path -LiteralPath $pidFile) {
    $old = Get-Content -LiteralPath $pidFile
    Stop-Process -Id $old -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

$p = Start-Process -FilePath "py" -ArgumentList "-m", "uvicorn", "app.main:app", `
    "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory (Join-Path $root "backend") `
    -RedirectStandardOutput (Join-Path $data "server.out.log") `
    -RedirectStandardError (Join-Path $data "server.err.log") `
    -WindowStyle Hidden -PassThru
$p.Id | Set-Content -LiteralPath $pidFile

for ($i = 0; $i -lt 20; $i++) {
    Start-Sleep -Seconds 1
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 2
        Write-Output ("server up (pid {0}): {1}" -f $p.Id, ($h | ConvertTo-Json -Compress))
        exit 0
    } catch {
        # not up yet
    }
}
Write-Error "server failed to start; check data\server.err.log"
exit 1
