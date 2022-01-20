*** Settings ***
Library    ${CURDIR}/../../EggplantLibrary    suite=${CURDIR}/eggPlantScripts/SuiteOne.suite    host=http://127.0.0.1    port=5400
Library	   Collections
*** Variables ***
${SUT screenshot file}    ${CURDIR}/../SUT-Screenshot.png

*** Keywords ***
Connect Screenshot SUT
	Connect SUT     {Type:"screenshot", name:"${SUT screenshot file}"}

Disconnect Screenshot SUT
	Disconnect SUT	{Type:"screenshot", name:"${SUT screenshot file}"}

Connect Real SUT
	Log  No real SUT configured!  WARN
	# Configure your real SUT here. Example:
	# Connect SUT	(serverID: "localhost", portNum: "5900", password: "XYZ", Type: "VNC Automatic", Visible: "Yes")
	# See more here: http://docs.eggplantsoftware.com/ePF/SenseTalk/stk-sut-information-control.htm#connect-command