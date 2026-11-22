param([Parameter(Mandatory=$true)][string]$Day)
$ErrorActionPreference = 'Stop'
# Legacy locks retain time-window observations; identified requests match exact run titles.
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
$intentPath = Join-Path $folder 'intent.txt'
$verified = $false
if (Test-Path -LiteralPath $intentPath) {
    $intent = (Get-Content -Raw -LiteralPath $intentPath).Trim()
    $parsed = [guid]::Empty
    if (![guid]::TryParse($intent, [ref]$parsed)) { throw 'Invalid dispatch intent' }
    $runs = @($runs | Where-Object { $_.display_title -ceq $intent })
    $verified = $runs.Count -eq 1
}
$receipt = [ordered]@{
    observed_at = [DateTimeOffset]::UtcNow.ToString('o')
    session = $Day
    ownership_verified = $verified
    retry_authorized = $false
    candidate_runs = @($runs | Select-Object id,status,conclusion,created_at,html_url,display_title)
}
$temp = Join-Path $folder 'reconciliation.tmp'
$receipt | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $temp -Encoding utf8
Move-Item -LiteralPath $temp -Destination (Join-Path $folder 'reconciliation.json') -Force
if ($verified) {
    [IO.File]::WriteAllText((Join-Path $folder 'accepted'), "Matched GitHub run " + $runs[0].id)
    exit 0
}
exit 2
