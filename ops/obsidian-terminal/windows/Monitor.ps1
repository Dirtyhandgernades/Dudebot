param([Parameter(Mandatory=$true)][string]$Day)
$ErrorActionPreference = 'Stop'
$config = Get-Content -Raw (Join-Path $PSScriptRoot 'runtime.json') | ConvertFrom-Json
$folder = Join-Path $PSScriptRoot "state/$Day"
$sessionMinutes = (Get-Content -Raw (Join-Path $PSScriptRoot 'sessions.json') | ConvertFrom-Json).PSObject.Properties[$Day].Value
if ($null -eq $sessionMinutes) { throw 'Session schedule missing' }
$localDeadline = [DateTime]::SpecifyKind([DateTime]::ParseExact($Day,'yyyy-MM-dd',$null).AddMinutes($sessionMinutes+15), [DateTimeKind]::Unspecified)
$deadline = [TimeZoneInfo]::ConvertTimeToUtc($localDeadline, [TimeZoneInfo]::FindSystemTimeZoneById('Central Standard Time'))
$receipt = Join-Path $folder 'intake/receipt.json'
$missed = Join-Path $folder 'missed-board-deadline.json'
$timely = $false
if (Test-Path -LiteralPath $receipt) {
    $intake = Get-Content -Raw -LiteralPath $receipt | ConvertFrom-Json
    $timely = $intake.intake_verified -eq $true -and [DateTimeOffset]::Parse($intake.received_at).UtcDateTime -le $deadline
}
if ([DateTime]::UtcNow -gt $deadline -and !$timely -and !(Test-Path -LiteralPath $missed)) {
    @{observed_at=[DateTimeOffset]::UtcNow.ToString('o'); deadline=$deadline.ToString('o');
      status='NO_VERIFIED_INTAKE_BY_DEADLINE'} | ConvertTo-Json | Set-Content -LiteralPath $missed
}
$intent = (Get-Content -Raw (Join-Path $folder 'intent.txt')).Trim()
$json = & gh api 'repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml/runs?event=workflow_dispatch&branch=research%2Fobsidian-early-rug-20261025&per_page=100'
if ($LASTEXITCODE -ne 0) {
    @{at=[DateTimeOffset]::UtcNow.ToString('o'); status='GITHUB_READ_FAILED'} |
        ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $folder 'monitor-history.jsonl')
    exit 2
}
$runs = @(($json -join [Environment]::NewLine | ConvertFrom-Json).workflow_runs | Where-Object { $_.display_title -ceq $intent })
if ($runs.Count -ne 1) {
    @{at=[DateTimeOffset]::UtcNow.ToString('o'); status='RUN_IDENTITY_UNRESOLVED'; count=$runs.Count} |
        ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $folder 'monitor-history.jsonl')
    exit 2
}
$env:PYTHONPATH = if ($config.PSObject.Properties['library']) { $config.library } else { Join-Path $PSScriptRoot 'library' }
& $config.python -m backtest.obsidian_board_retrieval --run-id $runs[0].id --intent $intent --directory (Join-Path $folder 'intake') 1> (Join-Path $folder 'monitor-output.json') 2> (Join-Path $folder 'monitor-error.txt')
$result = $LASTEXITCODE
@{at=[DateTimeOffset]::UtcNow.ToString('o'); run_id=$runs[0].id; exit_code=$result;
  output=(Get-Content -Raw (Join-Path $folder 'monitor-output.json'));
  error=(Get-Content -Raw (Join-Path $folder 'monitor-error.txt'))} |
    ConvertTo-Json -Compress | Add-Content -LiteralPath (Join-Path $folder 'monitor-history.jsonl')
exit $result
