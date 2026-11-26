# Diff — CodeStandards

Baseline: `C1SE.70_CodeStandards_DBCAS_ver1.3.docx`
Final: `C1SE.70_CodeStandards_DBCAS_ver1.3.docx`

## Summary

- Paragraphs: 84 changed, 84 added, 149 deleted
- Tables: 3 changed, 13 added, 3 deleted
- Figures: 1 replaced, 0 added, 1 removed
- Sections/headings changed: see detail below

## Figures

| Action | Baseline caption | Final caption |
|---|---|---|
| replaced | (uncaptioned baseline image) | Figure 1. Backend layering and dependency direction |
| removed | (uncaptioned baseline image) |  |

## Detail

### Changed table — front matter

**Before:** TABLE rows=7 cols=4 :: DOCUMENT INFORMATION | DOCUMENT INFORMATION | DOCUMENT INFORMATION | DOCUMENT INFORMATION || Document Title | Code Standard Document | Code Standard Document | Code Standard Document || Author(s) | Khanh, Truong Bao | Khanh, Truong Bao | Khanh, Truong Bao || Role | Team Member | Team Member | Team Member

**After:** TABLE rows=7 cols=4 :: DOCUMENT INFORMATION | DOCUMENT INFORMATION | DOCUMENT INFORMATION | DOCUMENT INFORMATION || Document Title | Code Standards Document | Version | ver1.3 || Author | Do, Nguyen Quoc | Role | Backend Developer || Group | C1SE.70 | Project | DBCAS

### Changed table — front matter

**Before:** TABLE rows=14 cols=6 :: Project acronym | SHFA | SHFA | SHFA | SHFA | SHFA || Project Title | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant | FitAI – Smart Health & Fitness Assistant || Start Date | 19 Aug 2025 | End Date | End Date | 12 December 2025 | 12 December 2025 || Lead Institution | International School, Duy Tan University | International School, Duy Tan University

**After:** TABLE rows=14 cols=6 :: Project acronym | DBCAS | DBCAS | DBCAS | DBCAS | DBCAS || Project Title | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis | DBCAS – AI-Assisted Database Competency Assessment and Skill Gap Analysis || Start Date | 14/09/2

### Changed table — front matter

**Before:** TABLE rows=3 cols=5 :: Version | Date | Comments | Author | Approval || 1.0 | 12 Oct 2025 | Initial Release | All members | X || 2.0 | 16 Oct 2025 | Final | All members | X

**After:** TABLE rows=3 cols=5 :: Version | Date | Comments | Author | Approval || 1.0 | 18/09/2026 | Initial release | C1SE.70 Team | X || 1.3 | 26/11/2026 | Rebuilt from the FITAI Code Standard frame with measured DBCAS standards | Do, Nguyen Quoc | X

### Changed paragraph — front matter

**Before:** TABLE OF CONTENT

**After:** Table of Contents

### Changed paragraph — front matter

**Before:** Always initialize variables before use.

**After:** List of Tables

### Changed paragraph — front matter

**Before:** Always put spaces before and after assignment operators (=, +=, -=, *=, /=) to improve readability.

**After:** List of Figures

### Changed paragraph — front matter

**Before:** Always put spaces before and after comparison operators (==, ===, !=, !==, <, >, <=, >=) to improve readability.

**After:** 1. Purpose and Scope

### Changed paragraph — front matter

**Before:** Example: if (x === 5) { ... }

**After:** This document records the coding standards that the DBCAS repository actually applies, and separates them from advice. A rule appears here only if a configuration file, a script, a hook or a CI job enforces it, or if the repository states it as review policy. Where the project does not enforce something that a standard document usually claims, this document says so.

### Changed paragraph — front matter

**Before:** Always put spaces before and after logical operators (&&, ||) to improve readability.

**After:** Table 1. Enforcement levels used in this document

### Changed paragraph — front matter

**Before:** Always put spaces before and after ternary operators (?:) to improve readability.

**After:** 2. Repository Structure

### Changed paragraph — front matter

**Before:** Example: let type = isAdmin ? 'admin' : 'user';

**After:** DBCAS/

### Changed paragraph — front matter

**Before:** 2.3 Statement Rules

**After:** ├── backend/            FastAPI application, tests, manage.py, pyproject.toml

### Changed paragraph — front matter

**Before:** Statements usually end with a semicolon (;). While JavaScript has Automatic Semicolon Insertion (ASI), explicitly using semicolons is recommended to avoid unexpected behavior.Use whitespace (e.g., indentation, blank lines) to make code easier to read.Use curly braces {} to group statements in code blocks (e.g., in if, else, loops, functions). Even for single-line blocks, using curly braces is recommended for clarity and to prevent errors when adding statements later.

**After:** │   ├── app/            26 modules, routers/ (7 registered; 8 .py files), services/ (72 top-level; 83 with subpackages)

### Changed paragraph — front matter

**Before:** Use comments (// for single-line comments, /* ... */ for multi-line comments) to explain complex or non-obvious parts of the code. Write clear and concise comments.Use the break statement to exit a switch statement or use return to exit a function.Use if, else if, and else for conditions. Place else directly after the closing curly brace } of the if block for better readability.

**After:** │   └── tests/          94 test modules + tests/dn/ (24 contract modules)

### Changed paragraph — front matter

**Before:** Example:

**After:** ├── frontend/           React 19 + Vite SPA, vitest, Playwright configs

### Changed paragraph — front matter

**Before:** JavaScript

**After:** │   ├── src/            components, pages, hooks, i18n, test

### Changed paragraph — front matter

**Before:** if (condition) {

**After:** │   └── e2e/            25 specs; e2e-application/ 3 specs

### Changed paragraph — front matter

**Before:** // ...

**After:** ├── db/                 schema.sql, migrations/ (28 files), seed data

### Changed paragraph — front matter

**Before:** } else if (anotherCondition) {

**After:** ├── scripts/            gates, generators, document build and verification

### Changed paragraph — front matter

**Before:** // ...

**After:** ├── docs/               architecture, diagrams, deliverables, submission

### Changed paragraph — front matter

**Before:** } else {

**After:** └── deploy/, sandbox/   deployment and executor assets

### Changed paragraph — front matter

**Before:** // ...

**After:** The layout is by technical role, not by feature. A feature touches a router, a service, a repository method, a React page and one or two i18n keys; the pull request template asks for all of them.

### Changed paragraph — front matter

**Before:** }

**After:** 3. Naming Conventions

### Changed paragraph — front matter

**Before:** Avoid deeply nested statements (e.g., multiple levels of nested if statements). Try to refactor the code to flatten the control flow.

**After:** Table 2. Naming rules

### Changed paragraph — front matter

**Before:** When returning a value in a function, place return and the returned value on the same line to prevent unexpected errors due to ASI.

**After:** 4. Backend Layering

### Changed paragraph — front matter

**Before:** Example: return result; (avoid writing return\nresult;)

**After:** Figure 1. Backend layering and dependency direction

### Changed paragraph — front matter

**Before:** Each variable declaration should be on a separate line for improved clarity.

**After:** The backend separates HTTP contracts, use cases and queries. Routers declare paths, request models and dependencies; services own transactions and rules; repository classes own SQLAlchemy queries and locks. The dependency direction is one-way and is checked in review: no repository imports a service, no service imports a router.

### Changed paragraph — front matter

**Before:** Example:

**After:** Table 3. Layer responsibilities

### Changed paragraph — front matter

**Before:** let firstName = 'Truong';

**After:** One measured exception exists: six router handlers query the session directly (practice.py lines 148 and 167, sessions.py 167, admin.py 227 and two adjacent handlers). They are listed here as known debt, not as an accepted pattern, and a change touching them should move the query into a repository method.

### Changed paragraph — front matter

**Before:** let lastName = 'Khanh';

**After:** 5. API Conventions

### Changed paragraph — front matter

**Before:** 2.4 Object Rules

**After:** Versioning is a URL path segment: every business route is under /api/v1. Two infrastructure routes (/health and /readiness) are unversioned by design.

### Changed paragraph — front matter

**Before:** Use curly braces {} to declare objects.

**After:** Resources are plural nouns; actions that are not CRUD use a verb segment (/sessions/{id}/submit, /admin/reviews/{id}/claim).

### Changed paragraph — front matter

**Before:** Example: const user = {};

**After:** Request and response bodies are Pydantic models; a handler never returns a raw ORM object.

### Changed paragraph — front matter

**Before:** When an object property name is the same as the variable, use the shorthand syntax to avoid redundancy.

**After:** The OpenAPI document is generated from the application and checked into CI: python scripts/export_openapi.py --check fails when the committed contract differs from the code.

### Changed paragraph — front matter

**Before:** Example:

**After:** Machine-readable errors use the envelope {error: {code, message, details}} with a stable lower_snake_case code; the frontend translates by that code, so a code is part of the public contract.

### Changed paragraph — front matter

**Before:** JavaScript

**After:** List endpoints paginate with limit and offset and return the total when the UI needs it; a missing bound is a review finding.

### Changed paragraph — front matter

**Before:** const name = 'Khanh';

**After:** Authentication is a bearer token resolved by a dependency; authorisation is a capability check in the same dependency chain, never an if-statement in a handler.

### Changed paragraph — front matter

**Before:** const age = 21;

**After:** Table 4. Status code usage

### Changed paragraph — front matter

**Before:** Use the this keyword to refer to the current object within the context of a method.

**After:** 6. Error Handling

### Changed paragraph — front matter

**Before:** Use a colon and a space between each attribute and its value.

**After:** One application exception class, AppError, carries a status code, a machine-readable code, a human message and optional details. Seven handlers translate exceptions at the boundary: LLM errors, database programming and operational errors, the catch-all, AppError, HTTP exceptions and request-validation errors. The catch-all re-applies the security headers because it short-circuits the middleware, a detail that must be preserved in any refactor.

### Changed paragraph — front matter

**Before:** Example: { name: 'Khanh', age: 21 }

**After:** Raise AppError with a new code rather than returning an error body from a handler.

### Changed paragraph — front matter

**Before:** Do not add a comma after the last attribute-value pair in an object definition.

**After:** Never leak a driver message, a stack trace or a prompt to the client.

### Changed paragraph — front matter

**Before:** Use meaningful property names that clearly describe the purpose of the property.

**After:** Log the code and the identifiers, never the answer text or the key.

### Changed paragraph — front matter

**Before:** Place the closing curly brace } on a new line, without leading whitespace.

**After:** A provider failure must degrade to a documented fallback; an unexpected validation failure must not fabricate a score.

### Changed paragraph — front matter

**Before:** Maintain newline consistency between object properties.

**After:** 7. Frontend Conventions

### Changed paragraph — front matter

**Before:** Always end object definitions with a semicolon.

**After:** Components are function components with hooks; no class components.

### Changed paragraph — front matter

**Before:** Example:

**After:** Data access goes through the single API client, which owns the base URL, the bearer token and error-code translation.

### Changed paragraph — front matter

**Before:** JavaScript

**After:** Route guards check the role at the route level; a page does not re-implement authorisation.

### Changed paragraph — front matter

**Before:** const config = {

**After:** Every user-visible string is an i18n key; a literal string in JSX is a review finding.

### Changed paragraph — front matter

**Before:** apiKey: 'your_api_key',

**After:** Charts read prepared series from the API; no scoring is recomputed in the browser.

### Changed paragraph — front matter

**Before:** apiUrl: 'https://api.example.com'

**After:** Styling uses Tailwind utility classes; shared visual tokens live in one place.

### Changed paragraph — front matter

**Before:** };

**After:** 8. Internationalization

### Changed paragraph — front matter

**Before:** 2.5 Line Length

**After:** English and Vietnamese catalogues are flat JSON with the same key set: 1 700 leaf keys in 34 groups in each language, zero drift. Question text is translated separately in the database, with English as the canonical original and a source hash per translation. Error codes are also i18n keys, so a new backend code requires a matching entry in both catalogues.

### Changed paragraph — front matter

**Before:** Limit line length to no more than 80 characters, with a maximum of 100 characters. If longer lines are necessary, break them into multiple lines to ensure readability across different screens and editors.

**After:** 9. Testing Standards

### Changed paragraph — front matter

**Before:** Use the dot (.) at the beginning of the line for long method chains or commas (,) at the end of the line for array elements or object properties to make it easier to follow when lines are wrapped.

**After:** Table 5. Test layers

### Changed paragraph — front matter

**Before:** Use 2 spaces for indentation. Avoid using tabs. Ensure your editor is configured to use spaces instead of tabs.

**After:** A bug fix adds a regression test that fails before the fix.

### Changed paragraph — front matter

**Before:** Add spaces inside single-line blocks (e.g., in simple if or loop statements), but this is generally discouraged for consistency. Prefer using curly braces for all code blocks.

**After:** A test never calls a real provider: the QA profile serves deterministic fake JSON.

### Changed paragraph — front matter

**Before:** There is no space between function identifiers and their calls.

**After:** A test may not be skipped or weakened to make a gate pass; a skip must name the reason in the test.

### Changed paragraph — front matter

**Before:** Example: myFunction();

**After:** There is no coverage threshold. Coverage is not measured anywhere in the repository, so no percentage is claimed in this document.

### Changed paragraph — front matter

**Before:** Use spaces around operators (as mentioned in section 2.2).

**After:** 10. Lint and Format

### Changed paragraph — front matter

**Before:** Keep lines short (between 80-100 characters).

**After:** Table 6. Configured tools

### Changed paragraph — front matter

**Before:** Example: processData(item1, item2);

**After:** Python formatting is not automated: there is no ruff format configuration and no formatter job. Python style is therefore a review standard. Line endings are normalised at the Git layer (.gitattributes) so the formatter sees the same text on Windows and Linux.

### Changed paragraph — front matter

**Before:** Use blank lines to separate logical sections of code, making it easier to read and understand.

**After:** 11. Commit and Branch Conventions

### Changed paragraph — front matter

**Before:** Use spaces to format comments clearly.

**After:** Commits follow Conventional Commits: <type>(<scope>): <description>, with ten accepted types (feat, fix, docs, style, refactor, test, chore, perf, ci, build), a lowercase imperative description of 50–72 characters without a trailing period, and an optional body of lines up to 72 characters. One commit does one thing. The integration branch is develop2; main receives merges by pull request only.

### Changed paragraph — front matter

**Before:** 2.7 Quotes

**After:** Attribution is the one mechanically enforced part: the commit-msg hook rejects AI or tool credit trailers and bot co-authors. The message format itself is a review standard, not a hook or a CI gate; the repository has no commitlint job.

### Changed paragraph — front matter

**Before:** Use single quotes (') or double quotes (") for strings, but maintain consistency throughout the project codebase. Some teams may have a preference; agree on one within your team.

**After:** 12. Pull Requests and CI

### Changed paragraph — front matter

**Before:** Triple quotes (''' or """) are unnecessary for simple strings in JavaScript as they are typically used for multi-line strings in languages like Python. In JavaScript, you can use template literals (backticks ``) for multi-line strings or variable interpolation.

**After:** The pull request template requires a summary, a verification list (tests, lint and format, manual verification, STATUS and BACKLOG when state changed), a risk section naming affected users and data with a rollback path, migration and breaking-change flags, and an independent-review flag.

### Changed paragraph — front matter

**Before:** Prefer using template literals (backticks ``) when you need to interpolate variables or create multi-line strings for better readability.

**After:** Table 7. CI workflows and jobs

### Changed paragraph — front matter

**Before:** Always use strict equality (=== and !==) instead of loose equality (== and !=) to avoid unexpected behavior due to type coercion.

**After:** There is no coverage job, no static-analysis security job beyond the dependency audits and the custom frontend audit, and no type-checking job.

### Changed paragraph — front matter

**Before:** Exception: Allow the use of obj == null as a shorthand to check for both null and undefined.

**After:** 13. Secret Handling

### Changed paragraph — front matter

**Before:** 2.9 Dot Location

**After:** Secrets live in the environment only. .env is ignored and never committed; .env.example documents every variable name and is checked by the environment inventory gate. The scanner applies seven patterns to the working tree, to staged blobs in the pre-commit hook, and to archives up to 128 MiB; it reports paths, never values.

### Changed paragraph — front matter

**Before:** Use a period (.) to access object properties and methods.

**After:** The allowlist has six entries, each pinned by path, rule, SHA-256 and a reason that must start with “Fake fixture:”; it cannot be widened to hide a real secret.

### Changed paragraph — front matter

**Before:** The dot must be on the same line as the property or method being accessed.

**After:** A finding is fixed at the source; deleting the line from history is an owner decision, not a routine fix.

### Changed paragraph — front matter

**Before:** For long method chains, the dot can be placed at the beginning of the line for improved readability.

**After:** The measured result at this commit is zero findings in the tree and zero matching commits in history.

### Changed paragraph — front matter

**Before:** Example:

**After:** 14. Review Checklist

### Changed paragraph — front matter

**Before:** JavaScript

**After:** Table 8. Reviewer checklist

### Changed paragraph — front matter

**Before:** .methodA()

**After:** 15. Known Gaps

### Changed paragraph — front matter

**Before:** .methodB()

**After:** No coverage measurement or threshold exists.

### Changed paragraph — front matter

**Before:** .methodC();

**After:** No Python type checker or formatter is configured.

### Changed paragraph — front matter

**Before:** 2.10 Array

**After:** ruff checks only four correctness families and skips backend/tests outside tests/dn.

### Changed paragraph — front matter

**Before:** Use concise syntax to declare an array. Use square brackets [] to create an array.

**After:** Six router handlers still access the database session directly.

### Changed paragraph — front matter

**Before:** Example: const numbers = [1, 2, 3];

**After:** Two foreign-key columns lack a dedicated index.

### Changed paragraph — front matter

**Before:** Avoid mutating the original array when not necessary. Prefer using non-mutating methods (e.g., map, filter, reduce, slice, concat) to maintain immutability and easier state management.

**After:** [OWNER TO PROVIDE: whether commitlint and a coverage gate should be added before the defence]

### Changed paragraph — front matter

**Before:** When working with arrays, check the data type of elements to avoid errors during operations or comparisons.

**After:** Appendix A. Open owner decisions

### Changed paragraph — front matter

**Before:** When accessing elements in an array, ensure you are using a valid index and not exceeding the array bounds to prevent IndexError (or similar errors).

**After:** The following values are not derivable from the repository. They stay owner-owned and are not asserted anywhere in this document.

### Changed paragraph — front matter

**Before:** Use a single import statement per module for better traceability of dependencies. However, you can import multiple members from the same module in one import statement.

**After:** Appendix B. Figure sources

### Changed paragraph — front matter

**Before:** Example: JavaScript

**After:** Every shipped figure is traceable to a repository source. The figure number is the number used in the body and in the List of Figures.
