@echo off
set PROJECT_PATH=d:\a my work\psx_research_analyst

schtasks /create /tn "PSX Pre-Market Analysis" /tr "cmd /c cd /d \"%PROJECT_PATH%\" ^&^& python scheduler/orchestrator.py --run pre_market" /sc weekly /d MON,TUE,WED,THU,FRI /st 08:30 /f

schtasks /create /tn "PSX Post-Market Analysis" /tr "cmd /c cd /d \"%PROJECT_PATH%\" ^&^& python scheduler/orchestrator.py --run post_market" /sc weekly /d MON,TUE,WED,THU,FRI /st 16:30 /f

echo.
echo Tasks created successfully!
echo   - Pre-Market:  8:30 AM (Mon-Fri)
echo   - Post-Market: 4:30 PM (Mon-Fri)
