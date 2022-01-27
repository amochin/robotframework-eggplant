*** Settings ***
Resource	../keywords/common.robot

Test Setup  Connect Screenshot SUT
Test Teardown	Stop movie
Suite Setup   Open Session
Suite Teardown  Close Session

*** Test Cases ***
Start and stop movie manually
	Start movie
	Check Input In Notepad    Hello World

Start movie with options
    [Documentation]    If optional arguments passed, default file path should be used properly
    ${path}=    Start Movie    compression_rate=0.3    
    Should Contain    ${path}    Movie    msg=No valid movie file path returned!

Embedded movie in case of errors
	[Documentation]  Expand the expectedly failed keyword to check the embedded video
	Start movie
	Run keyword and expect error	*Hello World IS NOT equal to Wrong text*	Check Input In Notepad    Wrong text

Movie wasn't stopped
	Start movie
	Run keyword and expect error	*StartMovie is not allowed when a movie is already being recorded*	Start movie

Movie wasn't started - error ignored
	Stop movie

Movie wasn't started - error excepted
	Run keyword and expect error	*StopMovie is not allowed -- there is no movie being recorded*
	...	Stop movie	error if no movie started=True