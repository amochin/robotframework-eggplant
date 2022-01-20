@echo off
set scriptDir=%~dp0
CD %scriptDir%

if "%1"=="" (
	set port=5400
	) else (
		set port=%1
	)

set pid_file=pid_%port%

echo Terminate eggPlant in eggDrive mode
echo Read PID from file %pid_file%..
if not exist %pid_file% (
	echo No PID file found, exit..
	exit
)
for /f "tokens=3 delims=; " %%a in (%pid_file%) do set PID=%%a
echo %pid%
echo Kill process %pid%..
taskkill /F /T /PID %pid%
echo Delete PID file
REM we don't want to occasionally kill wrong process
if exist %pid_file% del %pid_file%