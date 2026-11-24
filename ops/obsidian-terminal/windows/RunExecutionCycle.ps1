param([string]$Configuration)
$ErrorActionPreference = 'Stop'
if (!$Configuration) { $Configuration=Join-Path $PSScriptRoot 'service.json' }
$runtime=Get-Content -Raw (Join-Path $PSScriptRoot 'execution-runtime.json') | ConvertFrom-Json
$previous=$env:PYTHONPATH
try {
    $env:PYTHONPATH=$runtime.library
    & $runtime.python -m smg.execution_service --config $Configuration
    $result=$LASTEXITCODE
} finally { $env:PYTHONPATH=$previous }
exit $result
