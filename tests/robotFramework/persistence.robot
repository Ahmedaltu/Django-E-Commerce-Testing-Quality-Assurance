*** Settings ***
Library    SeleniumLibrary
Library    String
Suite Teardown      Close All Browsers

*** Variables ***
${URL}     http://localhost:8000
${USERNAME}   test1001
${PASSWORD}   test100!SecureToByPassPopup
${VERIFYSUCCESS}        Successfully signed in as

*** Test Cases ***
Test cart persists after reopening Browser
    [Documentation]         Tests that after adding item to cart, closing browser and reopening and logging in, the item is still in cart.
    Log In And Verify    ${USERNAME}       ${PASSWORD}          ${VERIFYSUCCESS}
    Add Order
    Close Browser
    Open Browser        ${URL}    Chrome
    Check Login Status
    Check Cart
    Clear Cart
    Close Browser

Test cart persists after logout and login
    [Documentation]    Tests that after adding item to cart, logging out and logging back in, the item is still in cart.
    Log In And Verify    ${USERNAME}    ${PASSWORD}    ${VERIFYSUCCESS}
    Add Order
    Logout
    Close Browser
    Log In And Verify    ${USERNAME}    ${PASSWORD}    ${VERIFYSUCCESS}
    Check Cart
    Clear Cart
    Close Browser

*** Keywords ***
Log In And Verify
    [Arguments]    ${username}    ${password}       ${verifypage}
    Login With Credentials      ${username}    ${password}
    Wait Until Page Contains    ${verifypage}    timeout=5s


Login With Credentials
    [Arguments]    ${username}    ${password}
    Open Browser        ${URL}    Chrome
    Click Element       id:djHideToolBarButton
    Click Element       xpath=//a[@href='/accounts/login/']
    Input Text      id:id_login    ${username}
    Input Text      id:id_password   ${password}
    Click Button        Sign In

Add Order
    Wait Until Page Contains Element   xpath=//a[contains(text(), 'A shirt')]
    Click Element                      xpath=//a[contains(text(), 'A shirt')]
    Wait Until Page Contains Element   xpath=//a[contains(@href, '/add-to-cart/shirt/')]  
    Click Element                      xpath=//a[contains(@href, '/add-to-cart/shirt/')]
    Page Should Contain                Order Summary
    Page Should Contain                A shirt

Check Cart
    Click Element                      xpath=//a[contains(@href, '/order-summary/')]
    Wait Until Page Contains           Order Summary
    Page Should Contain                A shirt

Check Login Status
    ${is_logged_in}=    Run Keyword And Return Status    Page Should Contain Element    xpath=//span[contains(text(), 'Logout')]
    Run Keyword If    not ${is_logged_in}    Log In And Verify    ${USERNAME}    ${PASSWORD}    ${VERIFYSUCCESS}

Clear Cart
    Click Element                       xpath=//i[contains(@class, 'fa-trash')]
    Wait Until Page Does Not Contain    A shirt

Logout
    Click Element    xpath=//a[@href='/accounts/logout/']
    Wait Until Page Contains Element    xpath=//button[text()='Sign Out']
    Click Button    Sign Out
    Wait Until Page Contains        You have signed out.