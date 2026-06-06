# sql-lint-service

SQL linting REST service wrapping SQLFluff with custom rules, preprocessors, and hot-reload.

## Stack

- **Python 3.12** — runtime
- **FastAPI 0.135 + Uvicorn 0.44** — REST API server on port 5000
- **SQLFluff 4.1** — core SQL linter; custom rules loaded via plugin entry point
- **Pydantic 2.13** — request/response model validation
- **Watchdog 6.x** — hot-reload file monitoring on the rules directory
- **Docker** — `Dockerfile` + `Dockerfile.optimized` + `docker-compose.yml`

## Layout

| Path | Description |
|------|-------------|
| `app/main.py` | FastAPI app, route handlers, startup/lifespan |
| `app/rules/` | Custom SQLFluff rules `Rule_SS01`–`SS03` |
| `app/rules/preprocessors/` | Preprocessors: date variable, SET filter, comment filter |
| `app/services/` | `LintService`, `PreprocessorManager`, `EventHandlers` |
| `tests/` | ~40 flat `test_*.py` files run via pytest |
| `.dockerignore` / `.env.example` / `docker-build.sh` | Docker & env scaffolding |

## Commands

| Action | Command |
|--------|---------|
| Install deps | `poetry install` (primary) or `pip install -r requirements.txt` |
| Run tests | `pytest` (or `python -m pytest`) |
| Start service | `python app/main.py` (runs uvicorn on 0.0.0.0:5000) |
| Docker build | `docker compose build` (or `./docker-build.sh`) |
| Docker run | `docker compose up` |

## Conventions

- **Docstrings/comments in Chinese** — throughout the codebase
- **Custom rules** — class `Rule_SS{NN}(BaseRule)` with `groups = ("all", "customer")`, `code = "SS{NN}"`
- **Preprocessors** — subclass `BasePreprocessor` from `app.rules.preprocessors.base_preprocessor`
- **Plugin entry** — registered via `[project.entry-points.sqlfluff]` → `sql_lint_rules = "app.rules"`
- **Test files** — `test_*.py` naming, colocated flat in `tests/`
- **No lint/format config found** — no `.pylintrc`, `.flake8`, `setup.cfg` lint sections, or `.pre-commit-config.yaml`

## Watch out for

- **Hot-reload** — editing a file under `app/rules/` while the service runs triggers Watchdog reload (debounced). Stop the service or remove the file to suppress it during refactors.
- **Performance guards** — 5s query timeout, 100KB sampling threshold, 10MB size cap, LRU cache of 100 results. These live in `app/main.py` as env-var-backed constants.
- **Port 5000** — hardcoded in `app/main.py` `__main__` block, not configurable via env.
