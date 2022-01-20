*** Settings ***
Resource	../keywords/common.robot

Test Setup  Connect Screenshot SUT
Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
${MyText}	This text will be never found
${MyRect}	((0,300),(200,500))

${ImageRect error msg - full screen}	*Image Not Found --\ imagerectangle Error - Unable To Find Image "(TEXT:"${MyText}")". Text not found.
${ImageRect error msg - restricted rect}	${ImageRect error msg - full screen} ${SPACE}Restricted Search Rectangle ${MyRect}*

${Click error msg - full screen}	*Image Not Found --\ click Error - No Text Found On Screen: "(TEXT:"${MyText}")". Text not found.
${Click error msg - restricted rect}	${Click error msg - full screen} ${SPACE}Restricted Search Rectangle ${MyRect}*

*** Test Cases ***
OCR ReadText - full screen
	Run keyword and expect error   ${ImageRect error msg - full screen}	OCR Click Imagerectangle With Text      ${MyText}	${Empty}
	Run keyword and expect error   ${Click error msg - full screen}	OCR Click Text      ${MyText}	${Empty}

OCR ReadText - restricted search rectangle
	Run keyword and expect error  ${ImageRect error msg - restricted rect}    OCR Click Imagerectangle With Text      ${MyText}	${MyRect}
	Run keyword and expect error  ${Click error msg - restricted rect}    OCR Click Text      ${MyText}	${MyRect}