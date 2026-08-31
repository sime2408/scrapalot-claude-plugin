---
description: Run the scrapalot-chat pre-commit hooks (ruff, secrets baseline, file hygiene) on changed files only.
---

# Run Pre-commit Hooks

Run the pre-commit hooks defined in `.pre-commit-config.yaml` only on files that were changed.

Hooks included:
* **pre-commit-hooks**
    - trailing-whitespace
    - end-of-file-fixer
    - check-added-large-files
    - requirements-txt-fixer
* **gitleaks**
    - gitleaks (detect secrets and sensitive info)
* **isort**
    - Apply import sorting with `--profile black`
* **black**
    - Format code with `python3.11`
* **flake8**
    - Run linting with:
        - `--max-line-length=150`
        - `--ignore=E203,E501,W503`
        - additional dependency: `flake8-simplify`

## Conventions
* Always ensure `.pre-commit-config.yaml` is up to date.
* Run inside `scrapalot-chat` conda env or `.venv` run `pre-commit install` if not already installed.
* Execute `pre-commit run --all-files` to validate the full repo.
* If hooks fail, apply the suggested fixes and re-run until clean.

## Goal
Guarantee code quality, security, and consistency across the repo before commits.
