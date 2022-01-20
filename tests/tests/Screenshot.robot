*** Settings ***
Resource	../keywords/common.robot

Test Setup  Connect Screenshot SUT
Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
@{MyRect1}=  (100, 100),(200, 200)
@{MyRect2}=  (0, 0),(500, 500)

*** Test Cases ***
Simple Fullscreen Screenshot
    Screenshot

Screenshot with a rectangle
    Screenshot  @{MyRect1}
    Screenshot  @{MyRect2}

Fullscreen with area highlighting
    Screenshot	highlight_rectangle=${MyRect2}

Screenshot taking error if no SUT connected
	[Setup]	Disconnect Screenshot SUT
	Run keyword and expect error	*Unable to take screenshot - no SUT connection available	Screenshot