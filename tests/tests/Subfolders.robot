*** Settings ***
Resource	../keywords/common.robot

Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
${input}	hello

*** Test Cases ***
Subfolders - 1 level deep
    ${result}=	Some Submodule.echo  ${input}
    Should Be Equal    ${input}    ${result}

Subfolders - 2 levels deep
    ${result}=	Some Submodule.One More Sub Submodule.echo  ${input}
    Should Be Equal    ${input}    ${result}

