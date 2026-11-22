$ErrorActionPreference = 'Stop'
$root = Join-Path ([IO.Path]::GetTempPath()) ('obsidian-recovery-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path "$root/state/2026-11-23" -Force | Out-Null
Copy-Item "$PSScriptRoot/Reconcile.ps1" "$root/Reconcile.ps1"
'{"2026-11-23":860}' | Set-Content "$root/sessions.json"
$intent = '11111111-1111-4111-8111-111111111111'
$intent | Set-Content "$root/state/2026-11-23/intent.txt"
function global:gh {
    $global:LASTEXITCODE = 0
    $global:response
}
$cases = @(
    @{name='matching'; titles=@($intent); expected=$true},
    @{name='unrelated'; titles=@('another-request'); expected=$false},
    @{name='duplicate'; titles=@($intent,$intent); expected=$false},
    @{name='empty'; titles=@(); expected=$false}
)
foreach ($case in $cases) {
    $accepted = "$root/state/2026-11-23/accepted"
    if (Test-Path $accepted) { Remove-Item -LiteralPath $accepted }
    $runs = @($case.titles | ForEach-Object {
        @{id=42; created_at='2026-11-23T20:21:00Z'; display_title=$_; status='completed'; conclusion='success'}
    })
    $global:response = @{workflow_runs=$runs} | ConvertTo-Json -Depth 4
    & "$root/Reconcile.ps1" -Day '2026-11-23'
    $code = $LASTEXITCODE
    $receipt = Get-Content -Raw "$root/state/2026-11-23/reconciliation.json" | ConvertFrom-Json
    if ($receipt.ownership_verified -ne $case.expected -or (Test-Path $accepted) -ne $case.expected -or $receipt.retry_authorized) {
        throw "Failed $($case.name)"
    }
    if (($case.expected -and $code -ne 0) -or (!$case.expected -and $code -ne 2)) { throw 'Unexpected exit' }
    Write-Output "$($case.name) passed"
}
Write-Output "Test evidence directory $root"
