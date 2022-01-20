*** Settings ***
Resource	../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Test Cases ***
Positional argument only
	@{arguments}=	Create list		some value	${123}	${True}	hello	hello world
	@{result}=		Default Params	some value
	Should Be Equal    ${result}	${arguments}

Positional argument as named arguement
	@{arguments}=	Create list		some value	${123}	${True}	hello	hello world
	@{result}=		Default Params	positional_arg_no_default=some value
	Should Be Equal    ${result}	${arguments}

Default value - int
	@{arguments}=	Create list		some value	${456}	${True}	hello	hello world
	@{result}=		Default Params	some value  arg_int=${456}
	Should Be Equal    ${result}	${arguments}

Default value - bool
	@{arguments}=	Create list		some value	${123}	${False}	hello	hello world
	@{result}=		Default Params	some value  arg_bool=${False}
	Should Be Equal    ${result}	${arguments}

Default value - string
	@{arguments}=	Create list		some value	${123}	${True}	Skywalker	hello world
	@{result}=		Default Params	some value  arg_string=Skywalker
	Should Be Equal    ${result}	${arguments}

Default value - string with spaces
	@{arguments}=	Create list		some value	${123}	${True}	hello	I am your father
	@{result}=		Default Params	some value  arg_string_with_space=I am your father
	Should Be Equal    ${result}	${arguments}
