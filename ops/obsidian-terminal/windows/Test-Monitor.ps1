$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('obsidian-monitor-' + [guid]::NewGuid())
New-Item -ItemType Directory -Force "$root/state/2026-11-23" | Out-Null
Copy-Item "$PSScriptRoot/Monitor.ps1" "$root/Monitor.ps1"
'{"python":"FakePython"}' | Set-Content "$root/runtime.json"
'intent' | Set-Content "$root/state/2026-11-23/intent.txt"
'{"2026-11-23":860}' | Set-Content "$root/sessions.json"
function global:gh {
    '{"workflow_runs":[{"id":42,"display_title":"intent"}]}'
    $global:LASTEXITCODE = 0
}
function global:FakePython {
    if ($args[1] -eq 'backtest.obsidian_desk_delivery') {
        $global:deliveryCalled = $true
        $global:LASTEXITCODE = 7
        'synthetic delivery failure'
        return
    }
    if ($global:testStatus -eq 'failure') { $global:LASTEXITCODE=1; 'synthetic failure' }
    elseif ($global:testStatus -eq 'pending') { $global:LASTEXITCODE=0; '{"status":"WAITING_FOR_RUN"}' }
    else { $global:LASTEXITCODE=0; '{"intake_verified":true}' }
}
foreach ($state in @('pending','success','failure')) {
    $global:testStatus=$state
    & "$root/Monitor.ps1" -Day '2026-11-23'
    $code=$LASTEXITCODE
    if (($state -eq 'failure' -and $code -ne 1) -or ($state -ne 'failure' -and $code -ne 0)) {
        throw "Incorrect monitor result for $state"
    }
}
$rows=@(Get-Content "$root/state/2026-11-23/monitor-history.jsonl")
if($rows.Count -ne 3){throw 'History incomplete'}
'Three monitor observations preserved'
$global:testStatus='success'
$global:deliveryCalled=$false
'{"python":"FakePython","desk_vault":"synthetic-existing-vault"}' | Set-Content "$root/runtime.json"
& "$root/Monitor.ps1" -Day '2026-11-23'
if (!$global:deliveryCalled -or $LASTEXITCODE -ne 7) { throw 'Delivery failure was hidden' }
if (!(Test-Path "$root/state/2026-11-23/desk-delivery-history.jsonl")) { throw 'Missing delivery observation' }
'Desk delivery failure surfaced with receipt'
'{"python":"FakePython"}' | Set-Content "$root/runtime.json"
New-Item -ItemType Directory -Force "$root/state/2000-01-03" | Out-Null
'{"2000-01-03":860}' | Set-Content "$root/sessions.json"
'intent' | Set-Content "$root/state/2000-01-03/intent.txt"
& "$root/Monitor.ps1" -Day '2000-01-03'
$missed = "$root/state/2000-01-03/missed-board-deadline.json"
if (!(Test-Path $missed)) { throw 'Missing deadline failure record' }
$first = Get-Content -Raw $missed
& "$root/Monitor.ps1" -Day '2000-01-03'
if ((Get-Content -Raw $missed) -ne $first) { throw 'Deadline receipt overwritten' }
'Missed deadline preserved across repeat observation'
