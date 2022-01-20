*** Settings ***
Resource	../keywords/common.robot
Documentation	These tests use eggplant to stimulate real actions like mouse clicks etc. - so they need a real SUT (VNC/RDP connection)
Default Tags	real_SUT_needed
Test Setup  Connect Real SUT
Suite Setup   Open Session
Suite Teardown  Close Session

*** Test Cases ***
Test One
    Run notepad
    ${x}=    Get Notepad Text
    Log    ${x}
    Run Command    TypeText "Some Text"
    Run Command    CaptureScreen "Screenshot.png"
	Run Command    TypeText endKey
	Run Command    TypeText shiftKey, homeKey
	Run Command    TypeText "Hello World"
	[Teardown]	Close Notepad

Test two
	Some Submodule.ping localhost
	Some Submodule.One More Sub Submodule.wait2seconds