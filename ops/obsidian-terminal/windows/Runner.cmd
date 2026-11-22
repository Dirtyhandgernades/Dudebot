@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PATH=%ProgramFiles%\GitHub CLI;%LOCALAPPDATA%\Programs\GitHub CLI;%PATH%"
set "GH_PROMPT_DISABLED=1"
set "day="
for /f %%D in ('powershell.exe -NoProfile -Command "$t=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow,'Central Standard Time'); $d=$t.ToString('yyyy-MM-dd'); $v=(ConvertFrom-Json -InputObject ([IO.File]::ReadAllText((Join-Path (Get-Location) 'sessions.json')))).PSObject.Properties[$d]; if($null -ne $v -and $t.TimeOfDay.TotalMinutes -ge $v.Value -and $t.TimeOfDay.TotalMinutes -lt ($v.Value+5)){$d}"') do set "day=%%D"
if not defined day exit /b 0
if not exist state mkdir state
if exist "state\%day%\accepted" exit /b 0
if exist "state\%day%" (
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Reconcile.ps1" -Day "%day%"
  exit /b 2
)
gh api repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml --silent || exit /b 1
mkdir "state\%day%" 2>nul || exit /b 2
powershell.exe -NoProfile -Command "[guid]::NewGuid().ToString() | Set-Content -Encoding ASCII 'state\%day%\intent.txt'" || exit /b 2
set /p intent=<"state\%day%\intent.txt"
gh workflow run obsidian-free-quant-feed.yml -f "dispatch_id=%intent%" --repo Dirtyhandgernades/Dudebot --ref research/obsidian-early-rug-20261025 || exit /b 2
echo Dispatch accepted>"state\%day%\accepted"
