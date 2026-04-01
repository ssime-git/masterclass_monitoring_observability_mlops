# AGENTS.md

This file defines the default engineering, review, and contribution standards for this repository.

## Core Principles

- Use English everywhere in code, comments, docstrings, logs, documentation, commit messages, and user-facing text.
- Keep the codebase modular, type-safe, easy to read, and easy to debug.
- Prefer small files and focused units of logic over large, multi-purpose modules.
- Write code that is explicit and maintainable rather than clever.
- Add unit tests for all production changes unless there is a clear and documented reason not to.
- Prefer the simplest solution that correctly solves the problem.
- Do not introduce abstraction, configuration, or extensibility before there is a real use case.
- Avoid duplication of important logic, while also avoiding premature abstraction.
- Leave the codebase in a cleaner state than you found it.

## Engineering Principles

- Apply `KISS`: keep solutions simple and proportionate to the problem.
- Apply `YAGNI`: do not build speculative features or abstractions.
- Apply `DRY`: reduce duplicated logic where doing so improves maintainability.
- Follow single-responsibility principles for modules, classes, and functions.
- Prefer explicit code over implicit behavior.
- Prefer composition over inheritance unless inheritance is clearly justified.
- Keep public interfaces small, stable, and well-typed.
- Separate pure business logic from I/O, framework glue, and external service integration.
- Avoid hidden side effects and unnecessary shared mutable state.
- Fail fast on invalid input at the correct boundary with clear error messages.
- Preserve backward compatibility unless a breaking change is intentional, documented, and tested.
- Default to secure practices: never hardcode secrets, validate external input, and use the least privilege needed.

## Code Style

- Do not add comments for self-explanatory code.
- Keep comments only when they add non-obvious context, constraints, or rationale.
- Prefer clear naming and small refactors over explanatory comments.
- Avoid long functions. Split logic into focused steps when a function starts combining multiple responsibilities.
- Replace inline business-specific magic values with named constants when that improves readability.
- Keep files as small as reasonably possible without creating artificial fragmentation.

## Python Standards

- Prefer the standard `logging` module over `print`.
- Keep typing explicit on important interfaces, service methods, dataclasses, and validation or correction flows.
- Maintain type safety across the codebase. New code should be compatible with `mypy`.
- Use `is None` and `is not None` for `None` checks.
- Prefer precise exception handling. Do not catch broad `Exception` unless the boundary is intentionally defensive and the reason is clear.
- When exceptions are caught, handle them in a way that preserves debuggability and avoids hiding the root cause.
- Use straightforward control flow and simplify redundant branches when behavior stays unchanged.

## Testing Standards

- We should always have unit tests for production code.
- Test files should stay readable and lightweight.
- Avoid redundant comments and docstrings in tests when the test name already explains the intent.
- Keep pedagogical or learner-facing feedback precise enough to explain the real blocker without revealing the full expected solution or hidden assertions.
- When execution fails, prefer surfacing a sanitized runtime issue and likely file instead of a vague generic message.
- Run the smallest relevant test scope for the change before pushing.

## Tooling Standards

- Use `Makefile` targets as the main entry points for local developer workflows whenever practical.
- Use `uv` and `uvx` for dependency and tool execution workflows.
- Integrate `ruff` and `mypy` into the standard development flow.
- Prefer targeted validation locally after edits, starting with `ruff`, `mypy`, and the smallest relevant test scope.

## Review Follow-Up

- Treat review comments as potentially codebase-wide, not only local to the commented line.
- For each review point, decide explicitly whether the right action is `fix`, `close`, or `clarify`.
- Before closing a thread, make sure the code change or rationale is in place and validated.
- Reflect the outcome in a concise reply when addressing review feedback.

## GitHub PR Workflow

- When addressing feedback, summarize the latest pass in a short PR comment once the fixes are pushed.
- Resolve review threads only after the related code or rationale is in place.

## Documentation Standards

- Avoid emoji in `README` files and repository documentation unless explicitly required.
- Avoid using `---` separators in `README` files.
- Keep documentation concise, direct, and consistent with the repository style rules.

## Conventional Commit Types

Use the following commit types:

- `feat`: Introduces a new feature for the user.
- `fix`: Fixes a bug in the application.
- `feat!` / `fix!`: Introduces a backward-incompatible breaking change.
- `docs`: Documentation changes only.
- `chore`: Maintenance tasks that do not affect production code.
- `refactor`: Code changes that neither fix a bug nor add a feature.
- `test`: Adds or updates tests.
- `ci`: Changes to CI/CD configuration and pipelines.
- `revert`: Reverts a previous commit.
