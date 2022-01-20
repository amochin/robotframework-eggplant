*** Settings ***
Resource	../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Test Cases ***
Comments and params
	empty Comments And Params	Hello world

Deprecating
    [Documentation]    WARNING is expected! Calling a deprecated keyword should make RF give it.
	deprecated Keyword