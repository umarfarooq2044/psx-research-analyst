@echo off
REM ============================================================
REM PSX Research Analyst - Windows Task Scheduler Setup
REM ============================================================
REM This script creates scheduled tasks for automatic daily reports
REM ============================================================

echo ============================================
echo PSX Research Analyst - Local Scheduler Setup
echo ============================================
echo.

set PROJECT_PATH=%~dp0
set PYTHON_PATH=python

echo Creating scheduled tasks...
echo.

REM Pre-Market Task (8:30 AM, Mon-Fri)
schtasks /create /tn "PSX Pre-Market Analysis" /tr "cmd /c cd /d \"%PROJECT_PATH%\" && %PYTHON_PATH% scheduler/orchestrator.py --run pre_market" /sc weekly /d MON,TUE,WED,THU,FRI /st 08:30 /f

echo [OK] Pre-Market task created (8:30 AM, Mon-Fri)

REM Post-Market Task (4:30 PM, Mon-Fri)
schtasks /create /tn "PSX Post-Market Analysis" /tr "cmd /c cd /d \"%PROJECT_PATH%\" && %PYTHON_PATH% scheduler/orchestrator.py --run post_market" /sc weekly /d MON,TUE,WED,THU,FRI /st 16:30 /f

echo [OK] Post-Market task created (4:30 PM, Mon-Fri)

echo.
echo ============================================
echo SETUP COMPLETE!
echo ============================================
echo.
echo Your reports will run automatically:
echo   - Pre-Market:  8:30 AM (Mon-Fri)
echo   - Post-Market: 4:30 PM (Mon-Fri)
echo.
echo To view tasks: Open Task Scheduler (taskschd.msc)
echo To run now: Right-click task in Task Scheduler > Run
echo.
pause
