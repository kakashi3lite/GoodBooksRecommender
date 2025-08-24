# Agent Handbook

Repository guidance for AI and human contributors.

## Directory Overview
- `src/` – application code (frontend and backend)
- `tests/` – unit and integration tests
- `scripts/` – utility scripts
- `terraform/` – infrastructure as code

## Coding Standards
- **Python**: format with `black`, type hints required
- **TypeScript/JS**: use ESLint and Prettier, React functional components
- **Terraform**: run `terraform fmt`

## Build & Test Commands
- `npm test` – frontend tests
- `npm run lint` – frontend linting
- `python -m pytest` – backend tests
- `pre-commit run --all-files` – lint/format all files
- `terraform validate` – infrastructure validation

## Prompt Patterns
- Scope requests to a single concern
- Provide file paths and snippets for context
- Use numbered steps for complex changes
- Run tests and linters after edits
