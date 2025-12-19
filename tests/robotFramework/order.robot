*** Settings ***
Library    SeleniumLibrary
Library    String
Suite Teardown      Close All Browsers

*** Variables ***
${URL}     http://localhost:8000
${USERNAME}   test123
${PASSWORD}   test123

*** Test Cases ***
Check Empty Cart
    [Documentation]     Ensure empty cart message when cart is empty
    Login to Store
    Go To Order Summary
    Page Should Contain         Order Summary
    Page Should Contain         Your cart is empty
    Close Browser

Add a shirt Order
    [Documentation]     Test adding a shirt to cart
    Add Order      shirt
    Close Browser

Increase shirt Quantity In Cart
    [Documentation]     Test increasing order size in cart.
    Login to Store
    Go To Order Summary
    Page Should Contain                 shirt
    ${quantity1}=    Get Item Quantity    shirt
    Increase Item Quantity    shirt
    ${quantity2}=    Get Item Quantity    shirt
    ${q1}=    Convert To Integer    ${quantity1.split()[0]}
    ${q2}=    Convert To Integer    ${quantity2.split()[0]}
    ${difference}=    Evaluate    ${q2} - ${q1}
    Should Be Equal As Integers    ${difference}    1
    Close Browser

Decrease shirt Quantity In Cart
    [Documentation]     Test decreasing order size in cart.
    Login to Store
    Go To Order Summary
    Page Should Contain                 shirt
    ${quantity1}=    Get Item Quantity    shirt
    Decrease Item Quantity    shirt
    ${quantity2}=    Get Item Quantity    shirt
    ${q1}=    Convert To Integer    ${quantity1.split()[0]}
    ${q2}=    Convert To Integer    ${quantity2.split()[0]}
    ${difference}=    Evaluate    ${q1} - ${q2}
    Should Be Equal As Integers    ${difference}    1
    Close Browser

Remove shirt Order
    [Documentation]     Test removing an item from cart.
    Login to Store
    Go To Order Summary
    Page Should Contain                 shirt
    Remove Item From Cart    shirt
    Close Browser

Unsuccessfull Order Removal
    [Documentation]     Test removing an item from cart that didn't exist in the cart.
    Login to Store
    Go To Product Page    shirt
    Wait Until Page Contains Element   xpath=//a[contains(@href, '/remove-from-cart/shirt/')]  
    Click Element                      xpath=//a[contains(@href, '/remove-from-cart/shirt/')]
    Page Should Contain                 This item was not in your cart
    Close Browser

Successfull shirt Order Removal
    [Documentation]     Test removing an item from cart that was in the cart.
    Add Order           shirt
    Wait Until Page Contains Element   xpath=//a[contains(text(), 'Continue shopping')]
    Click Element                      xpath=//a[contains(text(), 'Continue shopping')]
    Go To Product Page    shirt
    Wait Until Page Contains Element   xpath=//a[contains(@href, '/remove-from-cart/shirt/')]  
    Click Element                      xpath=//a[contains(@href, '/remove-from-cart/shirt/')]
    Page Should Contain                This item was removed from your cart. 
    Close Browser

*** Keywords ***
Login to Store
    Open Browser    ${URL}    Firefox
    Run Keyword And Ignore Error    Click Element    id:djHideToolBarButton
    Click Element       xpath=//a[@href='/accounts/login/']
    Input Text          id:id_login    ${USERNAME}
    Input Text          id:id_password    ${PASSWORD}
    Click Button        Sign In

Add Order
    [Arguments]    ${item_name}
    Login to Store
    Go To Product Page    ${item_name}
    Wait Until Page Contains Element   xpath=//a[contains(@href, '/add-to-cart/${item_name.lower().replace(" ", "-")}/')]  
    Click Element                      xpath=//a[contains(@href, '/add-to-cart/${item_name.lower().replace(" ", "-")}/')]
    Page Should Contain                Order Summary
    Page Should Contain                ${item_name}

Go To Order Summary
    Wait Until Page Contains Element   xpath=//a[contains(@href, '/order-summary/')]
    Click Element                      xpath=//a[contains(@href, '/order-summary/')]
    Page Should Contain                Order Summary

Go To Product Page
    [Arguments]    ${item_name}
    Wait Until Page Contains Element   xpath=//a[contains(text(), '${item_name}')]
    Click Element                      xpath=//a[contains(text(), '${item_name}')]

Get Item Quantity
    [Arguments]    ${item_name}
    ${quantity}=    Get Text    xpath=//tr[td[contains(., '${item_name}')]]/td[3]
    RETURN          ${quantity}

Increase Item Quantity
    [Arguments]    ${item_name}
    Click Element    xpath=//tr[td[contains(., '${item_name}')]]//a[contains(@href, 'add-to-cart')]
    Page Should Contain    This item quantity was updated.

Decrease Item Quantity
    [Arguments]    ${item_name}
    Click Element    xpath=//tr[td[contains(., '${item_name}')]]/td[3]//a[contains(@href, 'remove-item-from-cart')]

Remove Item From Cart
    [Arguments]    ${item_name}
    Click Element    xpath=//tr[td[contains(., '${item_name}')]]//i[@class='fas fa-trash float-right']
    Page Should Contain    This item was removed from your cart.
    Page Should Contain    Your cart is empty