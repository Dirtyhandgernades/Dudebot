@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if not exist "Runner.cmd" goto failed
where gh.exe >nul 2>&1
if errorlevel 1 (
  where winget.exe >nul 2>&1 || goto failed
  winget install --id GitHub.cli --exact --source winget || goto failed
)
set "PATH=%ProgramFiles%\GitHub CLI;%LOCALAPPDATA%\Programs\GitHub CLI;%PATH%"
where gh.exe >nul 2>&1 || goto failed
gh auth status --hostname github.com >nul 2>&1
if errorlevel 1 (
  gh auth login --hostname github.com --web --git-protocol https || goto failed
)
gh api repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml --silent || goto failed
set "dest=%LOCALAPPDATA%\OBSIDIAN\ResearchRunner"
if not exist "%dest%" mkdir "%dest%" || goto failed
if not defined OBSIDIAN_PYTHON set "OBSIDIAN_PYTHON=%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0Provision.ps1" -Destination "%dest%" -PythonPath "%OBSIDIAN_PYTHON%" || goto failed
copy /y sessions.json "%dest%\sessions.json" >nul || goto failed
copy /y RunScheduled.vbs "%dest%\RunScheduled.vbs" >nul || goto failed
copy /y Reconcile.ps1 "%dest%\Reconcile.ps1" >nul || goto failed
copy /y Runner.cmd "%dest%\Runner.cmd" >nul || goto failed
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; $name='OBSIDIAN After-Close Research'; $old=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; if($old -and $old.Description -ne 'OBSIDIAN Windows research dispatcher'){throw 'Task name already in use'}; $action=New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\wscript.exe') -Argument '//B //NoLogo RunScheduled.vbs' -WorkingDirectory $env:dest; $trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1); $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5); Register-ScheduledTask -TaskName $name -Description 'OBSIDIAN Windows research dispatcher' -Action $action -Trigger $trigger -Settings $settings -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -RunLevel Limited -Force | Out-Null; Start-ScheduledTask -TaskName $name; Get-ScheduledTaskInfo -TaskName $name | Select-Object NextRunTime" || goto failed
echo Installed for your Windows user. See Task Scheduler: OBSIDIAN After-Close Research.
echo Existing task name retained for upgrade. Dispatch is now 40 minutes before market close.
echo Local receipts: "%dest%\state"
pause
exit /b 0
:failed
echo Setup failed. Review the message above. GitHub CLI and repository workflow access are required.
pause
exit /b 1
