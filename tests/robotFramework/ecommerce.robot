*** Settings ***
Library    SeleniumLibrary
Suite Teardown    Close All Browsers

*** Variables ***
${URL}     http://localhost:8000
${USERNAME}   test123
${PASSWORD}   test123

*** Test Cases ***
Login Works
    [Documentation]     Basic log in sequence, with premade user details. tool bar must hidden because selenium.
    Open Browser        ${URL}    Chrome
    Click Element       id:djHideToolBarButton
    Click Element       xpath=//a[@href='/accounts/login/']
    Input Text          id:id_login    ${USERNAME}
    Input Text          id:id_password    ${PASSWORD}
    Click Button        Sign In
    Page Should Contain    Successfully signed in as ${USERNAME} 
    Close Browser