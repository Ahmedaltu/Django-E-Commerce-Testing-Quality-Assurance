# Test Plan

## Introduction

This plan defines a testing strategy for the existing Python server-side of a Django-based ecommerce application.  
The purpose is to validate the stability, correctness, and reliability of the current implementation of the server logic.

### System Under Test (SUT)

The **SUT** is the **Python server component** of a Django ecommerce platform.  
Testing focuses exclusively on the **server-side logic** — models, forms, views, and integrations — without covering any browser UI, CSS, or JavaScript components.

### Objectives

- Validate that all existing backend features work correctly under normal and edge-case conditions. 
- Ensure **critical ecommerce flows** (cart → checkout → payment) execute successfully with expected data integrity.  
- Identify defects and inconsistencies through systematic unit and integration testing.  
- Measure and maintain sufficient code coverage across critical components.

## Scope and Realism (defines what will and will not be tested)

### Stripe & External Integrations

- External APIs are replaced by mocked endpoints, covering success, common declines, network timeouts, and so on. 

### In Scope

Focuse on individual components to verify correctness in isolation.  
- Models: pricing, discounts, coupon logic, payment validation.  
- Forms: input validation, error messages, required fields.  
- Utility functions and template tags.

Verify interactions among multiple components within Django’s application context. These tests check how different parts of the system work together. 
- Views: add/remove items from cart, apply coupons, checkout workflow.  
- Database operations: order creation, payment updates, and refund processing.  
- Stripe integration: mocked API responses for successful and failed payments.  

Validate complete user workflows through the Django testing client to check if the system works from start to finish, like a real user would.  
Examples:  
- Add an item to the cart, go to checkout, and complete a payment.  
- Try to use an invalid coupon code.  
- Request a refund and check if it is processed correctly.  

### Out of Scope

- Browser UI/visual rendering and cross-browser testing.  
- JavaScript functionality and front-end build pipelines.  
- Full load/stress benchmarking beyond light query checks.  
- Real Stripe live charges (payments are mocked).  
- Email rendering and deliverability (payloads only verified).

### Resources

- Skill resource: members have experience in python
  unittest & coverage: everyone
  pytest: Sophie, Alpo, Ahmed, Tram, Wallen
  robot framework: everyone
  Django test: Elias
  Django app: Elias and Wallen
  integrating payment gateway: Elias, Tram
  Selenium: Sophie, Alpo, Ahmed, Tram
  GitLab CI/CD: Sophie, Elias, Tram
  Linting JS: Sophie, Elias

- Testing environment: Python version 3.9 due to the age of source code. We can try increase the python version. Aalto server host GitLab CI/CD.
- Server environments
  - Ubuntu 24 under WSL2
  - Windows 11
  - MacOs (Apple Silicon)
- Client (browser) environments
  - Firefox on Windows with Responsive Design Mode
  - Chrome (DevTools for mobile emulation)

### Constraints

We have identified a few constraints in our resources that affect our scope, methods and testing environments.

We believe that the SUT is as of now (Oct 2025) unmaintained and lacks specification.
This means that we cannot elicit requirements from actual stakeholders, and for determining the expected outputs of our test cases, we will partially have to resort to "Kiddie Oracles" and comparing to existing, equivalent programs (Copeland, 2003).
As we cannot assume the perspectives of all the stakeholders, we are left with an incomplete picture of the SUT's context of use.
This in turn limits our ability to assign the correct priorities to different quality characteristics (ISO/IEC 25010:2025:en).

Another major constraint lies in the time allocation.
We have a team of six testers, each having a 27-hour budget for the workload in this project, giving a total of 162 person-hours.
We have estimated a rough split for the time allocation on various activities: 20% for setup and planning, 30% for exploratory testing, and 50% for writing automated tests.
Since this test plan is already underway and many of the members have set up their testing environments, the setup and planning activity can be considered mostly completed and thus feasible. Further setup is required for testing the payment integration, see [Limitations, Risks & Mitigation](#limitations-risks--mitigation).

30% of the total time budget means 8.1 hours per person for exploratory testing.
In their book on Exploratory Software Testing, Whittaker (2009) explains many variations of the "tours" metaphor that can guide the testing.
The SUT contains about 56 templates, meaning that each of the six testers only has about 8 templates per hour to cover, by a naive analysis.
However, the templates also contain significant branching logic, with at least 35 `{% if %}` tags.
There is enough template logic alone to make it infeasible to both test and document some of the heavier tours, in the allocated time, even if different tours or districts are assigned to different members of our team. (Not to mention backend logic.)
An example tour that would be ruled out would be the Saboteur tour, where the SUT's resources are disrupted during its operation in as many ways as possible (Whittaker, 2009).
As a result, our exploratory testing focuses mainly on the happy paths (see [TestingTools & Techniques](#testingtools--techniques)).
The time constraint on this activity thus affects our ability to find bugs in the other paths.

50% of the total time budget means 81 hours in total for writing automated tests.
We believe it wouldn't be feasible to achieve full path coverage for the core app in this time, let alone the whole codebase.

Finally, there is a monetary constraint. This testing project has a budget of zero euros, which limits our scope and some aspects of our testing environment.
[Aalto Version doesn't support CI/CD](https://www.aalto.fi/en/services/version-control-system-for-software-development#3-limitations), so other providers are needed for implementing CI/CD workflows.
For example, our budget rules out GitLab, as their free plan is limited to only five users in private groups.
The budget also means that testing payments with real money is not possible.
Overall, when it comes to testing payments, we are dependent on software and environments provided by the third party payment platform Stripe.
Stripe provides [sandbox environments](https://docs.stripe.com/sandboxes) for testing without real money.

## Theory and Standards - Methods

This testing plan follows the SFS-ISO/IEC 25010:2025 standard, and focuses on the following core characteristics relevant to the Django e-commerce application:

- **Functional Suitability:** Ensured through unit and integration tests verifying correctness and completeness of models, views, and API endpoints.
- **Reliability:** Ensured through system's ability to operate consistently under expected and unexpected conditions, including handling errors gracefully and recovering from failures.
- **Compatibility:** System validation across environments (operating systems and browsers).
- **Maintainability:** Supported through linting, and measuring test coverage (statement, branch, and MC/DC).

These characteristics will serve as the theoretical basis for this testing approach.

## Testing Techniques and Tools
We follow an iterative testing process combining different testing techniques. First, we explore the functionality of the application using exploratory testing. Following that, we implement Black box testing and finally, white box testing to identify logical defects within the code. The following section describes the testing techniques and tools that we will utilize. 

### Testing Techniques:
- Exploratory testing: 
    At this stage, we focus on verifying the application's logic and core functionalities. Since the application lacks detailed documentation and specifications, exploratory testing enables us to learn about its behavior by navigating through various user flows and scenarios.

    We adopt a session-based or time-boxed approach, where testers perform focused exploratory sessions—each targeting a specific aspect of the application. These aspects include, but are not limited to:

    - Form functionality and validation

    - Stripe payment integration

    - Underlying database model behavior
    
    During each session we explore happy paths and malformed inputs via Django test‑client, in order to uncover potential security or logical flaws.

    Each session is goal-driven and documented, including steps taken, observations made, and any issues encountered—ensuring reproducibility and traceability.

    If critical defects or important user flows are identified during these sessions, we will formalize them into scripted test cases. These tests will then be automated using tools such as the Robot Framework, contributing to our regression suite and ensuring ongoing coverage.

- Black-box testing: 
After initial exploratory testing, we proceed with black-box testing to validate key functionalities without relying on understanding of the code implementation. Specifically for Views, we can apply techniques such as boundary value analysis, and robustness testing to ensure the system behaves as expected across typical and edge-case inputs.

  - Boundary value analysis helps identify defects that often occur at the edges of input domains. For example, we can test form fields with minimum and maximum allowed characters or values to ensure proper validation and error handling.

  - Robustness testing tests the system with unexpected, malformed, or extreme inputs (e.g., special characters, empty fields, or interrupted workflows like an aborted payment). This helps verify how the system handles invalid inputs or stress scenarios, which is important for non-functional requirements like stability and error recovery.

These techniques help uncover defects both in functional requirements (e.g., incorrect validation logic, flow handling) and non-functional requirements (e.g., usability, and robustness against unexpected input or behavior).

- White-box testing:
    Once we have a solid understanding of the application's functionalities and requirements, we shift focus to white-box testing to ensure internal logic is thoroughly verified and key areas of the codebase are adequately covered.

    - Code coverage approach: 
        - For critical components such as the Payment View, we aim to achieve Modified Condition/Decision Coverage (MC/DC) using decision tables and carefully designed test cases. MC/DC is useful in high-risk areas, as it ensures that each condition independently affects the decision outcome.

        - For simple or low-risk functions -- such as utility methods in models or straightforward logic in views -- we target full branch coverage, ensuring every logical path is executed at least once. This provides confidence in code correctness without incurring unnecessary test complexity.

    - Static analysis and code reviews: In addition to manual inspection of the codebase, we incorporate static analysis tools to perform:

        - Linting: Enforcing code quality standards and catching stylistic or syntactic issues early.

        - Security scanning: Identifying common vulnerabilities (e.g., injection risks, insecure configurations) through automated scanners.


This combined approach ensures not only high test coverage but also improved code quality, maintainability, and security throughout the development lifecycle.
### Testing Tools

- Unittest: we use Unittest over Pytest for both Black and white box for models and forms
- Django testing tools: for both Black and white box for Views
- Robot framework: exploratory testing
- [Coverage and Selenium](https://developer.mozilla.org/en-US/docs/Learn_web_development/Extensions/Server-side/Django/Testing#other_recommended_test_tools):
  - Install coverage.py
  - Validate test coverages for important views.
- [Pylinter](https://pypi.org/project/pylint/): used in white box testing
- [Vulnerability Scanner](https://pypi.org/project/safety/): used in white box testing

## Limitations, Risks & Mitigation
Carr et al. (1993) present a risk identification method based on a taxonomy of software development risks. While rigid adherence to the method in question is not a part of this testing plan, it can be observed that elements in the taxonomy have some overlap with the risks we have identified in this testing project.

The risks involved in this test plan largely originate from the resource limitations discussed in [Constraints](#constraints).
The project's dependency on a third party payment platform is one.
The SUT uses Stripe for payments, meaning that we would need the appropriate API keys for sandbox testing. There is a risk that obtaining these keys could be more difficult than expected, if there are fees or terms that apply. In the case that we cannot obtain these keys, we would have to omit payment testing in the sandbox environment.
This risk is somewhat mitigated by the fact that the code base uses the [official Stripe Python Library](https://pypi.org/project/stripe/) maintained by Stripe. As such, we can assume that the library's documentation serves as a good and correct specification for its integration.
Furthermore, the documentation as well as the model and error classes provided by the official library should make it straightforward to mock the outputs of the API in unit testing.
The resulting mocks should make for relatively realistic tests. However, the library version is outdated, which may affect compatibility with the real platform, thus affecting the realism of the tests. This could be mitigated by upgrading the package version (which might require code changes, something which is not in our scope).
Realism of the test conditions and environment is something we consider, since it falls within
the Environment attribute of the Integration and Test element of Product Engineering risks in the Software Development Risk Taxonomy (Carr et al., 1993).

As noted in the Constraints, there is a lack of documentation which can result in a misunderstanding of requirements.
We attempt to mitigate this by exercising clear communication, particularly when documenting the scripts and results of our exploratory tests.
Our exploratory testing carries risks of its own, as the test oracles are limited to "Kiddie Oracles" and Existing Programs (Copeland, 2003). These methods provide a good starting point, since Ecommerce applications generally have similar features, and us testers also have experience in some of them as regular users.
Nevertheless, the validity and completeness of the output of our test oracles cannot be guaranteed.
Issues with validity and completeness constitute another overlap with the Software Development Risk Taxonomy, as they are attributes of the Requirements element in the Product Engineering class (Carr et al., 1993). According to Carr et al. (1993), undocumented customer expectations are not accounted for in the cost and schedule.
Analogously, that risk also exists to our project schedule: we may discover new requirements or correct our understanding of previous ones as the testing goes along, creating unexpected workload.
Other risks to our project schedule include workload arising from unexpected technical roadblocks and unfamiliar tools.
As a mitigation, we have adjusted our timeline and milestones in an ambitious but realistic manner, so that the schedule can later be relaxed if needed.

As mentioned in [Constraints](#constraints), [CI/CD isn't supported on Aalto Version.](https://www.aalto.fi/en/services/version-control-system-for-software-development#3-limitations)
Workarounds and alternatives may be explored, but these may cost more time than expected due to the unfamiliarity.
(Familiarity is also an attribute found in the Software Development Risk Taxonomy, relating to both the Development Process and Development System elements (Carr et al., 1993). While this test plan doesn't describe a development process, it stands to reason that the same risks could translate to a testing process.)

## Timeline, milestones, and deliverables

- Phase 3 testing report: 11/11
- Milestones:
  - Test plan: finish by 14/10
  - Setup tools: finish by 14/10
    - CICD + Safety
    - JS Linter
    - Django Testing tools
  - Explorary code base and tests: finish by 14/10 - Includes review of existing code, identifying gaps and testable issues.
  - Robot scripts: aim at 27/10 - Automated tests for UI (browsing items, managing shopping cart, making purchases etc)
  - Black & white box tests: aim at 27/10 - EP, BVA, other analysis
  - Reports: tentative deadline 10/11 - Turn findings into a coherent analysis and report

## References

Carr, M., Konda, S., Monarch, I., Walker, C., & Ulrich, F. (1993). Taxonomy-Based Risk Identification.
Retrieved October 14, 2025, from https://www.sei.cmu.edu/library/taxonomy-based-risk-identification/.

Copeland, L. (2003). A Practitioner's Guide to Software Test Design. Artech House.

International Organization for Standardization (2025). ISO/IEC 25010:2025:en. Systems and software engineering - Systems and software Quality Requirements and Evaluation (SQuaRE) - Product quality model.

Whittaker, J. (2009). Exploratory Software Testing. Addison-Wesley Professional.