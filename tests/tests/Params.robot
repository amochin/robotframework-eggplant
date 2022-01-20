*** Settings ***
Resource	../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
@{Packed List}	Value1	Value2	Value3
@{Expected List}	Hello	World	Anybody here?	${Packed List}
${Multiline param N}  Hello\nWorld
${Multiline param R}  Hello\rWorld
${Multiline expected result}  Hello\nWorld\nNew line

*** Test Cases ***
Simple Params
    Several Params  1   second param    third

Quoted strings as params
    Several Params  ${testname}   "second param"    third

Params Numeric_Alphabetic
	Several Params	1	2	04_01_030_20008_XYZ

Integer param
	${my int}=	Set variable	${123}
	${result}=	Return the same value	${my int}
	Should Be Equal    ${result}	${my int}

Float param - positive
	${my float}=	Set variable	${123.45}
	${result}=	Return the same value	${my float}
	Should Be Equal    ${result}	${my float}

Float param - negative
	${my float}=	Set variable	${-123.45}
	${result}=	Return the same value	${my float}
	Should Be Equal    ${result}	${my float}

Float param - convert from string
	${result}=	Return the same value	${-123.45}
	Should Be Equal    ${result}	${-123.45}

Strict variables
	${my float}=	Set variable	${-123.45}
	Run command	set the strictVariables to true
	Run keyword and expect error	*StrictVariablesViolation*	Log undefined variable
	[Teardown]	Run command	set the strictVariables to false

Strict variables - all string arguments must be quoted
	${str}=  Set Variable  hello
	Run command	set the strictVariables to true
	${result}=	return the same value  ${str}
	Should Be Equal    ${result}    ${str}
	[Teardown]	Run command	set the strictVariables to false

Param starting with whitespace
	${string}=	Set variable	${SPACE}Hello
	${result}=	Return the same value	${string}
	Should Be Equal    ${result}	${string}

Param ending with whitespace
	${string}=	Set variable	Hello${SPACE}
	${result}=	Return the same value	${string}
	Should Be Equal    ${result}	${string}

List Params as String
    list Params     ("first", "second", "third")

List Params as List
    list Params     ${Packed List}
    
String params with special characters
    Several Params  ört ?yz+5g   "second param"    third

Params search in scripts should be case insensitive
	Params Capital Letters	let me entertain you

Packed list params
	@{result list}=	packed list params	${Expected List}[0]	${Expected List}[1]	${Expected List}[2]	${Packed List}
	Should be equal	${result list}	${Expected List}
    
Multiline Param - New Line Character
    [Documentation]  The '\\r' and '\\n' characters in RF are converted to the eggPlant specific 'return' character.
    ...  The eggPlant script adds one more 'return', which is equal to '\\n' when it comes back to RF.

    ${Multiline result}=    Return multiline value  ${Multiline param N}
    Should be equal  ${Multiline result}   ${Multiline expected result}

Multiline Param - Return Character
    [Documentation]  The '\\r' and '\\n' characters in RF are converted to the eggPlant specific 'return' character.
    ...  The eggPlant script adds one more 'return', which is equal to '\\n' when it comes back to RF.

    ${Multiline result}=    Return multiline value  ${Multiline param R}
    Should be equal  ${Multiline result}   ${Multiline expected result}
