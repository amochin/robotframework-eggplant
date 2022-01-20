*** Settings ***
Resource	../keywords/common.robot

Test Teardown  Close Session

*** Test Cases ***
Connect to eggDrive
	set eggdrive connection  host=http://localhost  port=5400
	open session

Session BUSY - error if not closed properly
    Open session
    Run keyword and expect error    *BUSY: Session in progress*    Open session    close_previously_open_session=${FALSE}

Session BUSY - close automatically
    Open session
    Open session