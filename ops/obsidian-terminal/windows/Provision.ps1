param(
    [Parameter(Mandatory=$true)][string]$Destination,
    [Parameter(Mandatory=$true)][string]$PythonPath,
    [string]$SourceRoot
)
$ErrorActionPreference = 'Stop'
if (!$SourceRoot) { $SourceRoot = Join-Path $PSScriptRoot '../../..' }
if (!(Test-Path -LiteralPath $PythonPath -PathType Leaf)) { throw 'Python executable missing' }
$source = Join-Path $SourceRoot 'backtest'
if (!(Test-Path (Join-Path $source 'obsidian_board_retrieval.py'))) {
    $source = Join-Path $PSScriptRoot 'library/backtest'
}
New-Item -ItemType Directory -Force $Destination | Out-Null
$library = Join-Path $Destination ('library-' + [guid]::NewGuid())
New-Item -ItemType Directory -Force (Join-Path $library 'backtest') | Out-Null
foreach ($name in @('obsidian_board_retrieval.py','obsidian_board_intake.py','obsidian_packet_freshness.py')) {
    Copy-Item -LiteralPath (Join-Path $source $name) -Destination (Join-Path $library 'backtest')
}
[IO.File]::WriteAllText((Join-Path $library 'backtest/__init__.py'),'')
$previous = $env:PYTHONPATH
try {
    $env:PYTHONPATH = $library
    & $PythonPath -c 'from backtest.obsidian_board_retrieval import retrieve; from backtest.obsidian_board_intake import delivery_check'
    if ($LASTEXITCODE -ne 0) { throw 'Retrieval library validation failed' }
} finally { $env:PYTHONPATH = $previous }
foreach ($name in @('Monitor.ps1','Reconcile.ps1','Runner.cmd','RunScheduled.vbs','sessions.json')) {
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot $name) -Destination $Destination -Force
}
$temporary = Join-Path $Destination ('runtime-' + [guid]::NewGuid() + '.json')
@{python=$PythonPath; library=$library; provisioned_at=[DateTimeOffset]::UtcNow.ToString('o')} |
    ConvertTo-Json | Set-Content -LiteralPath $temporary -Encoding UTF8
Move-Item -LiteralPath $temporary -Destination (Join-Path $Destination 'runtime.json') -Force
