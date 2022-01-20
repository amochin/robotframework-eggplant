*** Settings ***
Documentation	Tests for lists with old legacy formatting (round brackets) - prior to eggPlant 20.1.0.

Resource	../../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
*** Variables ***
${Some string with brackets}	Au (Sieg) - Düren Pbf
${Some string with last bracket}	Saarbrücken Hbf - Neubrücke (Nahe)
${Some string with closing bracket ONLY}	Saarbrücken Hbf - Neubrücke Nahe)

*** Test Cases ***

Simple List Return
	@{expected}=	Create list  ${1}	${2}	${3}	${4}
	Log list  ${expected}
	${l}=  Legacy Lists. return list
	Should be equal  ${l}  ${expected}

List with new line in the value
	@{expected}=	Create List  Value 1	Value\n2
	Log list	${expected}
	@{l}=	Legacy Lists. return list with new line in the value
	Should be equal  ${l}  ${expected}

List with single value
	@{expected}=	Create List   single_value
	Log list	${expected}
	@{l}=  Legacy Lists. return list single value
	Should be equal  ${l}  ${expected}

List with bools
    [Documentation]	Change in eggPlant 21.2.0 - bool values inside a list get quoted
    ...	[false, true] --> ["False", "True"]
    @{expected}=   Create List  ${False}	${True}	${False}
    Log list	${expected}
    ${l}=	Legacy Lists. return list with bools
	Should Be Equal    ${l}	${expected}

List with a float value
	@{expected}=   Create List  ${1}  ${2}  ${3.14}  ${4}
    Log list	${expected}
    ${l}=	Legacy Lists. return list with argument  ${3.14}
	Should Be Equal    ${l}	${expected}

List With Brackets In String Middle
    @{expected}=   Create List  ${1234}  ${Some string with brackets}
    Log list	${expected}
    @{l}	Legacy Lists. return List With Brackets In String	${Some string with brackets}
    Should be equal	${l}	${expected}

List With Brackets In String End (List Middle)
	@{expected}=	Create list  ${1234}	${Some string with last bracket}	ABC
	Log list	${expected}
	@{l}=	Legacy Lists. Return List With Brackets In String In Middle	${Some string with last bracket}
    Should be equal	${l}	${expected}

List With Brackets In String End (List End)
	@{expected}=	Create list  ${1234}	${Some string with last bracket}
	Log list	${expected}
	@{l}=	Legacy Lists. return List With Brackets In String	${Some string with last bracket}
	Should be equal	${l}	${expected}

List With Closing Bracket ONLY In String End (List End)
	@{expected}=	Create list  ${1234}	${Some string with closing bracket ONLY}
	Log list	${expected}
	@{l}=	Legacy Lists. return List With Brackets In String	${Some string with closing bracket ONLY}
	Should be equal	${l}	${expected}

List With Unpaired Closure Bracket And Open Brackets In String Middle
	@{Level 2}=  Create list  ${1234}	he(llo)	abc)
	@{expected}=  Create list  xyz  ${Level 2}
	Log list	${expected}
	@{l}=	Legacy Lists. return List With Unpaired Closure Bracket And Open Brackets In String Middle
	Should be equal	${l}	${expected}

Nested List
	@{Level 3}=  Create list	alpha	beta  gamma
	@{Level 2}=  Create list	A	B   ${Level 3}  C
	@{expected}=  Create list  ${1}  ${2}	${Level 2}  ${3}
	Log list   ${expected}
    ${l}=  Legacy Lists. return nested list
    Should be equal  ${l}  ${expected}

Special Nested List
	@{Level 3 I}=	Create list    ${33}  ${34}
	@{Level 3 II}=	Create list    bla  bla
	@{Level 2}= 	Create list  ${Level 3 I}  ${Level 3 II}
	@{Rectangle List}=	Create list  ${100}  ${200}  ${300}  ${400}
	@{expected}=  Create list  ${46464664}  ${TRUE}  ${4.4}  12:00:00  ${Rectangle List}  ${Level 2}
	Log list   ${expected}
    ${l}=   Legacy Lists. return Nested List Special
    Should be equal  ${l}  ${expected}

Nested List With Empty Values
	@{Level 2}=		Create list  one	two	${EMPTY}
	@{expected}=	Create list  one	${Level 2}	${EMPTY}
    Log list   ${expected}
    @{l}=  Legacy Lists. return nested list with empty values
    Should be equal  ${l}  ${expected}

Nested List With Empty Value At Start (Level 3)
    @{Simple list}=	Create list	 alpha	beta  gamma
    @{Level 3}=		Create list  ${EMPTY}	one	two
    @{Level 2}=		Create list  ${Simple list}	${Simple list}	${Level 3}
    @{expected}=	Create list  ${Level 2}	${Simple list}
    Log list   ${expected}
    @{l}=  Legacy Lists. return nested list with empty value at start
    Should be equal  ${l}  ${expected}

Nested List with a string value with brackets
	@{Level 3}=  Create list	alpha	beta  gamma
	@{Level 2}=		Create list	 A	B   ${Level 3}  ${Some string with last bracket}
	@{expected}=	Create list  ${1}	${2}	${Level 2}	${3}
    Log list   ${expected}
    ${l}=  Legacy Lists. return nested list with string inside  	${Some string with last bracket}
    Should be equal  ${l}  ${expected}