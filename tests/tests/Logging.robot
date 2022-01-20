*** Settings ***
Resource	../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***

${my log msg}  This message should appear as warning!

*** Test Cases ***
Warnings
	Log warning in eggPlant	${my log msg}