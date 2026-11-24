param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$PythonPath,
    [string]$SourceRoot
)
$ErrorActionPreference = 'Stop'
if (!$SourceRoot) { $SourceRoot = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path }
if (!(Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python executable missing' }
$library = Join-Path $Destination ('execution-library-' + [guid]::NewGuid())
New-Item -ItemType Directory -Force (Join-Path $library 'smg') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $library 'config') | Out-Null
foreach ($name in @('__init__.py','models.py','market.py','game_rules.py','decision_evidence.py',
    'order_intents.py','order_preparation.py','tinyfish_execution.py','execution_controller.py','execution_service.py')) {
    Copy-Item -LiteralPath (Join-Path $SourceRoot "smg/$name") -Destination (Join-Path $library 'smg')
}
Copy-Item -LiteralPath (Join-Path $SourceRoot 'config/smg_excluded_symbols.txt') -Destination (Join-Path $library 'config')
$previous = $env:PYTHONPATH
try {
    $env:PYTHONPATH=$library
    & $PythonPath -c 'from smg.execution_service import cycle; from smg.game_rules import EXCLUDED_SYMBOLS; assert EXCLUDED_SYMBOLS, "Exclusion list missing"'
    if ($LASTEXITCODE -ne 0) { throw 'Execution runtime import or exclusion validation failed' }
} finally { $env:PYTHONPATH=$previous }
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'RunExecutionCycle.ps1') -Destination $Destination -Force
$configuration = @{python=$PythonPath; library=$library; provisioned_at=[DateTimeOffset]::UtcNow.ToString('o')}
$temporary=Join-Path $Destination ('execution-runtime-' + [guid]::NewGuid() + '.json')
$configuration | ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
Move-Item -LiteralPath $temporary -Destination (Join-Path $Destination 'execution-runtime.json') -Force
# Authority, exit rules, queue, account and credentials are deliberately untouched.
# No scheduled task, activation or execution-owner cutover is created here.
