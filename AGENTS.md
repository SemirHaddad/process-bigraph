# Repository Guidelines

## Project Structure & Module Organization

`process_bigraph/` contains the Python runtime for composing biological models. Core execution lives in `composite.py`, `scheduling.py`, and `plumbing.py`; `processes/` provides model components, `protocols/` execution backends, `workflow/` orchestration, and `visualizations/` plotting helpers. Tests live in `process_bigraph/tests/`, `tests/`, and the root `tests.py`. Documentation and images are under `docs/` (including `docs/_static/`); tutorials are in `notebooks/`. Development helpers and performance measurements live in `scripts/` and `benchmarks/`.

## Build, Test, and Development Commands

Use Python 3.11 or newer; CI uses Python 3.12 and uv.

- `uv sync --frozen`: install the locked project and development dependencies.
- `uv run pytest`: run the default suite, excluding tests marked slow.
- `uv run pytest --run-slow`: include slow backend and simulation tests.
- `uv run pytest --cov=process_bigraph --cov-report=term`: reproduce CI coverage reporting.
- `uvx ruff check`: run the CI lint gate.
- `uv build`: build source and wheel distributions.
- `bash scripts/dev-link.sh`: sync dependencies and link a sibling `../bigraph-schema` checkout when present.

## Coding Style & Naming Conventions

Follow surrounding Python code: four-space indentation, `snake_case` functions and modules, `PascalCase` classes, and uppercase constants. Keep imports explicit and avoid bare `except:` clauses. Ruff checks Pyflakes (`F`) and `E722`; no automatic formatter is configured. Keep optional backend dependencies isolated so core imports work without every extra installed.

## Testing Guidelines

Use pytest and name new files `test_*.py` and functions `test_*`. Place regression tests beside related tests and cover observable behavior, including invalid configurations. Run a focused file while iterating, for example `uv run pytest process_bigraph/tests/test_composite_spec.py`. Mark expensive tests with `@pytest.mark.slow`. CI reports coverage but configures no minimum percentage.

## Commit & Pull Request Guidelines

History mixes short descriptive subjects with scoped prefixes such as `fix(emitter):` and `chore:`. Use concise, action-oriented subjects; include a scope when helpful. Follow `CONTRIBUTING.md`: discuss proposed changes through an issue and obtain maintainer feedback before implementation. Pull requests should explain the problem, resulting behavior, related issue, and validation performed. Review `CLA.md` and `CODE_OF_CONDUCT.md`; submitting a pull request indicates agreement to the CLA.
