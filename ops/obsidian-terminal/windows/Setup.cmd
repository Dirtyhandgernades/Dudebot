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
copy /y Runner.cmd "%dest%\Runner.cmd" >nul || goto failed
powershell.exe -NoProfile -Command "$ErrorActionPreference='Stop'; $name='OBSIDIAN After-Close Research'; $old=Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue; if($old -and $old.Description -ne 'OBSIDIAN Windows research dispatcher'){throw 'Task name already in use'}; $action=New-ScheduledTaskAction -Execute $env:ComSpec -Argument '/d /c Runner.cmd' -WorkingDirectory $env:dest; $trigger=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10); $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 5); Register-ScheduledTask -TaskName $name -Description 'OBSIDIAN Windows research dispatcher' -Action $action -Trigger $trigger -Settings $settings -User ([Security.Principal.WindowsIdentity]::GetCurrent().Name) -RunLevel Limited -Force | Out-Null; Start-ScheduledTask -TaskName $name; Get-ScheduledTaskInfo -TaskName $name | Select-Object NextRunTime" || goto failed
echo Installed for your Windows user. See Task Scheduler: OBSIDIAN After-Close Research.
echo Local receipts: "%dest%\state"
pause
exit /b 0
:failed
echo Setup failed. Review the message above. GitHub CLI and repository workflow access are required.
pause
exit /b 1
