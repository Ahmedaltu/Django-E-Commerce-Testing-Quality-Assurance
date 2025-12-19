# Pylint Quality & Style Guide

This document describes the Pylint configuration and coding quality standards defined by our team for the Software
Testing and Quality Assurance assignment.

The configuration `.pylintrc`, defines static analysis rules, to ensure a consistent, maintainable, and testable Python
codebase.

The report can be found at `tests/reports/pylint-report.txt` and the analysis report can be found
at `pylint-test-report.md`

## Linting Areas Covered

The current configuration (.pylintrc) evaluates the following key aspects of our Django-based codebase:

### 1. Design Quality

Prevent “God classes” and “mega functions” that are difficult to test and maintain:

* Ensures code structure remains modular, simple, and testable.
* Functions limited to 5 parameters (max-args = 5)
* Functions limited to 50 statements and 12 branches
* Classes limited to 10 attributes and 20 public methods
* Detects excessive local variables or nested complexity
* Encourages small, single-responsibility functions

### 2. Code Structure and Readability

Ensure clean, consistent formatting

* Enforces PEP8 naming conventions (https://peps.python.org/pep-0008/) for variables, functions, classes, and constants.
* Maximum line length: 100 characters
* 4-space indentation enforced
* Unix-style line endings (LF)
* Ignores style checks in auto-generated or test files

### 3. Maintainability & Similarity Detection

* Flags duplicate code blocks (min-similarity-lines = 4)
* Ignores comments, docstrings, and imports when checking duplication
* Detects re-imports, inconsistent returns, and obsolete/redundant suppressions

### 4. Security and Logging

Ensure safe coding and robust debugging practices:

* Disallows risky built-ins (print, eval, exec)
* Enforces consistent logging style (logging-format-style = new)

### 5. Miscellaneous Checks

* Tracks TODO, FIXME, XXX notes for later refactoring.
* Reports only relevant, high-confidence warnings.

## How to Run Pylint

### 1. **Install dependencies**

Make sure Pylint and Django plugin are installed:

```bash
pip install pylint pylint-django pylint-plugin-utils
```

### 2. **Run on the full project**

Run Pylint using the provided configuration:

```bash
pylint --rcfile=.pylintrc core djecommerce > tests/reports/pylint-report.txt
```