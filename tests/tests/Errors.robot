*** Settings ***
Resource	../keywords/common.robot

Test Setup  Connect Screenshot SUT
Suite Setup   Open Session
Suite Teardown  Close Session

*** Variables ***
${enteredText}  Hello World
${wrongExpectedText1}  Wrong Test
${wrongExpectedText2}  SomethinWrongText
${error1}  *AssertionFailed -- \ (assertion: actual=expected; actually: ${enteredText} IS NOT equal to ${wrongExpectedText1})
${error2}  *AssertionFailed -- \ (assertion: actual=expected; actually: ${enteredText} IS NOT equal to ${wrongExpectedText2})

*** Test Cases ***
Test with failing keyword
    Run keyword and expect error  ${error1}  Check Input In Notepad    ${wrongExpectedText1}

Test with another failing keyword - one word string param
    Run keyword and expect error  ${error2}  Check Input In Notepad    ${wrongExpectedText2}
