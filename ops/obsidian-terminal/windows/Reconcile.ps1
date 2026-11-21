param([Parameter(Mandatory=$true)][string]$Day)
$ErrorActionPreference = 'Stop'
# Only a unique dispatch in this session window can reconcile the legacy lock.
$folder = Join-Path $PSScriptRoot "state/$Day"
if (!(Test-Path -LiteralPath $folder)) { exit 2 }
$minutes = (Get-Content -Raw (Join-Path $PSScriptRoot 'sessions.json') | ConvertFrom-Json).PSObject.Properties[$Day].Value
if ($null -eq $minutes) { exit 2 }
$local = [DateTime]::SpecifyKind([DateTime]::ParseExact($Day,'yyyy-MM-dd',$null).AddMinutes($minutes),[DateTimeKind]::Unspecified)
$zone = [TimeZoneInfo]::FindSystemTimeZoneById('Central Standard Time')
$start = [TimeZoneInfo]::ConvertTimeToUtc($local,$zone)
$end = $start.AddMinutes(5)
$json = & gh api 'repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml/runs?event=workflow_dispatch&branch=research%2Fobsidian-early-rug-20261025&per_page=100'
if ($LASTEXITCODE -ne 0) { exit 2 }
$runs = @((($json -join [Environment]::NewLine) | ConvertFrom-Json).workflow_runs | Where-Object {
    $created = ([DateTimeOffset]$_.created_at).UtcDateTime
    $created -ge $start -and $created -lt $end
})
# Time-only legacy matching cannot prove ownership, so retain an observation
# without setting accepted or authorizing a resubmission.
$receipt = [ordered]@{
    observed_at = [DateTimeOffset]::UtcNow.ToString('o')
    session = $Day
    ownership_verified = $false
    retry_authorized = $false
    candidate_runs = @($runs | Select-Object id,status,conclusion,created_at,html_url)
}
$temp = Join-Path $folder 'reconciliation.tmp'
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temp -Encoding utf8
Move-Item -LiteralPath $temp -Destination (Join-Path $folder 'reconciliation.json') -Force
exit 2
