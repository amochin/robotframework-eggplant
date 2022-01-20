@echo off
REM usage: launch_eggPlant <port> <log file path> <timeout>

set scriptDir=%~dp0
CD %scriptDir%

set eggplantPath=C:\Program Files\Eggplant\runscript.bat

if "%1"=="" (
	set port=5400
	) else (
		set port=%1
	)

set pid_file=pid_%port%
echo launching eggPlant in Drive Mode
echo start script path: %eggplantPath%
echo port: %port%
echo pid file: %pid_file%

REM log into file if requested
if [%2]==[] (
set str="%eggPlantPath% -driveport %port% -drivelogging 2"
) else (
set str="%eggPlantPath% -driveport %port% -drivelogging 2 >%2 2>&1"
echo Log file: %2
)

REM Save PID to text file in order to terminate it afterwards...
wmic process call create %str%  | find "ProcessId" > %pid_file%
echo Check PID saved in file %pid_file%..
for /f "tokens=3 delims=; " %%a in (%pid_file%) do set savedPID=%%a
echo %savedPID%

REM Wait requested timeout
if [%3]==[] (
set timeout=15
) else (
set timeout=%3
)
echo Waiting %timeout% seconds

ping 127.0.0.1 -n %timeout%>nul
echo done