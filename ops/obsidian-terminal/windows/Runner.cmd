@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
set "PATH=%ProgramFiles%\GitHub CLI;%LOCALAPPDATA%\Programs\GitHub CLI;%PATH%"
set "GH_PROMPT_DISABLED=1"
set "day="
for /f %%D in ('powershell.exe -NoProfile -Command "$t=[TimeZoneInfo]::ConvertTimeBySystemTimeZoneId([DateTimeOffset]::UtcNow,'Central Standard Time'); if([int]$t.DayOfWeek -ge 1 -and [int]$t.DayOfWeek -le 5 -and $t.TimeOfDay.TotalMinutes -ge 970){$t.ToString('yyyy-MM-dd')}"') do set "day=%%D"
if not defined day exit /b 0
if not exist state mkdir state
if exist "state\%day%\accepted" exit /b 0
if exist "state\%day%" exit /b 2
gh api repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml --silent || exit /b 1
mkdir "state\%day%" 2>nul || exit /b 2
gh workflow run obsidian-free-quant-feed.yml --repo Dirtyhandgernades/Dudebot --ref research/obsidian-early-rug-20261025 || exit /b 2
echo Dispatch accepted>"state\%day%\accepted"
