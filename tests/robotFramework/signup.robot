*** Settings ***
Library    SeleniumLibrary
Suite Teardown    Close All Browsers

*** Variables ***
${URL}     http://localhost:8000
*** Variables ***
${PASSWORD}   test123
${VERIFYSUCCESS}        Successfully signed in as
${EXISTINGUSERNAME}     test123
${VERIFYEXISTING}                A user with that username already exists.
${WEAKPASSWORD}         123
${VERIFYWEAKPASSWORD}           Password must be a minimum of 6 characters.
${WRONGUSERNAME}        abcdcddefds
${WRONGPASSWORD}        asdfsdafewdaf4321q4
${VERIFYWRONGPASSWORDORUSERNAME}        The username and/or password you specified are not correct.

*** Test Cases ***
Signup With Valid Credentials
    [Documentation]     Sign up test, username created when test is run
    ${USERNAMETS}=        Evaluate        __import__('time').strftime('%H%M%S') + "testuser"
    Sign Up And Verify    ${USERNAMETS}     ${PASSWORD}       ${VERIFYSUCCESS}

Signup With Existing Username
    [Documentation]     Test that existing username is not allowed
    Sign Up And Verify    ${EXISTINGUSERNAME}     ${PASSWORD}       ${VERIFYEXISTING} 

Signup With Weak Password
    [Documentation]     Test that weak pw is not allowed
    Sign Up And Verify    ${EXISTINGUSERNAME}     ${WEAKPASSWORD}       ${VERIFYWEAKPASSWORD}

Login With Wrong Username
    [Documentation]     Test that nonexisting user is not allowed
    Log In And Verify    ${WRONGUSERNAME}       ${PASSWORD}     ${VERIFYWRONGPASSWORDORUSERNAME}

Login With Wrong Password   
    [Documentation]     Test that wrong pw is not allowed
    Log In And Verify    ${EXISTINGUSERNAME}       ${WRONGPASSWORD}     ${VERIFYWRONGPASSWORDORUSERNAME}

Login With Empty Fields   
    [Documentation]     Test that empty fields dont work. Note! There should be error message instead of nothing happening here.
    Open Browser    ${URL}    Chrome
    Click Element   id:djHideToolBarButton
    Click Element   xpath=//a[@href='/accounts/login/']
    Click Button    Sign In
    Page Should Not Contain    Successfully signed in as
    #There is no error message for this
    Close Browser

*** Keywords ***
Sign Up With Credentials
    [Arguments]    ${username}    ${password}
    Open Browser        ${URL}    Chrome
    Click Element       id:djHideToolBarButton
    Click Element       xpath=//a[@href='/accounts/signup/']
    Input Text      id:id_username    ${username}
    Input Text      id:id_password1   ${password}
    Input Text      id:id_password2   ${password}
    Click Button    Sign Up »

Sign Up And Verify
    [Arguments]    ${username}    ${password}       ${verifypage}
    Sign Up With Credentials    ${username}    ${password}
    Wait Until Page Contains    ${verifypage}    timeout=5s
    Close Browser

Log In And Verify
    [Arguments]    ${username}    ${password}       ${verifypage}
    Login With Credentials      ${username}    ${password}
    Page Should Contain    ${verifypage}
    Close Browser

Login With Credentials
    [Arguments]    ${username}    ${password}
    Open Browser        ${URL}    Chrome
    Click Element       id:djHideToolBarButton
    Click Element       xpath=//a[@href='/accounts/login/']
    Input Text      id:id_login    ${username}
    Input Text      id:id_password   ${password}
    Click Button        Sign In