*** Settings ***
Resource	../../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
${Simple string}	Ös this a real life?)
${string with comma}	LBZS SDB09A / LL-DH, DN-DH
${string with space}	${SPACE}LBZS SDB09A / LL-DH, DN-DH${SPACE}

*** Test Cases ***
String Return
    ${s}=  return The Same Value	${Simple string}
	Should be equal  ${s}	${Simple string}

Return string with comma
	${s}=  return The Same Value	${string with comma}
	Should be equal  ${s}	${string with comma}
	
Return string with space
	${s}=  return The Same Value	${string with space}
	Should be equal  ${s}	${string with space}
	
Integer Return
    Log    ${123}
    ${x}=  return The Same Value    ${123}
	Should be equal  ${x}  ${123}

Bool return
	${x}=  return The Same Value    ${TRUE}
	Should be equal  ${x}  ${TRUE}

Float Return
    ${x}=  return The Same Value    ${1.99}
	Should be equal  ${x}  ${1.99}

Empty Return
    ${x}=  return The Same Value    ${EMPTY}
	Should be equal  ${x}  ${EMPTY}