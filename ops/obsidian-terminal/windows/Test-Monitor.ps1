$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('obsidian-monitor-' + [guid]::NewGuid())
New-Item -ItemType Directory -Force "$root/state/2026-11-23" | Out-Null
Copy-Item "$PSScriptRoot/Monitor.ps1" "$root/Monitor.ps1"
'{"python":"FakePython"}' | Set-Content "$root/runtime.json"
'intent' | Set-Content "$root/state/2026-11-23/intent.txt"
function global:gh {
    '{"workflow_runs":[{"id":42,"display_title":"intent"}]}'
    $global:LASTEXITCODE = 0
}
function global:FakePython {
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
