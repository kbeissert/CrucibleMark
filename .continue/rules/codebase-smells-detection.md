______________________________________________________________________

## globs: "\*\*/\*" description: This rule ensures that the codebase adheres to high-quality standards, follows best practices, and avoids common pitfalls that can lead to technical debt, security vulnerabilities, or poor maintainability. It should be applied during code reviews, onboarding, and regular maintenance phases. alwaysApply: true

Analyze the entire codebase for code smells, including but not limited to:

1. **WCAG Compliance Issues** (e.g., missing alt text, poor contrast, non-descriptive links).
1. **Performance Issues** (e.g., large DOM elements, inefficient loops, unused variables).
1. **Security Issues** (e.g., hardcoded secrets, SQL injection vulnerabilities, XSS risks).
1. **Architectural Issues** (e.g., circular dependencies, god objects, deep nesting).
1. **Testing Issues** (e.g., missing tests, flaky tests, untested edge cases).
1. **Code Duplication** (e.g., copy-pasted code blocks, repeated logic).
1. **Poor Naming Conventions** (e.g., unclear variable/function names, inconsistent naming).
1. **Anti-Patterns** (e.g., overuse of singletons, callback hell, premature optimization).
1. **Hardcoded Values** (e.g., magic numbers, hardcoded paths/URLs).
1. **Lack of Documentation** (e.g., missing docstrings, comments, or READMEs).

For each detected smell, provide:

- **Location** (file, line number, or function/class name).
- **Severity** (critical, high, medium, low).
- **Description** of the issue.
- **WCAG Compliance Level and Number** (if applicable).
- **Suggested Fixes** with code examples where relevant.
- **References** to relevant design patterns, best practices, or standards.

Use static analysis tools (e.g., SonarQube, ESLint, Pylint, RuboCop) and manual code reviews to identify smells.
