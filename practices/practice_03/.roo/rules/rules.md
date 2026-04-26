## Memory Bank

Перед каждой сессией ходи в мемори банк по MCP узнавая контекст, после каждой сессии записывай важные данные в мемори банк.

## Dev environment tips

- Run `uvicorn main:app --reload` to start the development server with hot reload.
- Use `python -m pytest` to run the test suite from the project root.
- Copy `.env.example` to `.env` and fill in `OPENWEATHER_API_KEY` before running the app.
- Use `pip install -r requirements.txt` to install all dependencies.

## Code style rules

- Docstrings are allowed; inline comments are not.
- Follow PEP 8: snake_case for variables and functions, PascalCase for classes.
- Use type annotations for all function signatures and return types.
- Prefer f-strings over `.format()` or `%` formatting.
- Keep imports grouped: standard library → third-party → local, separated by blank lines.
- Do not use bare `except:` — always catch specific exception types.

## Architecture rules

- One file — one responsibility. Do not mix unrelated logic in a single module.
- Models live in `models/`, routers live in `routers/`. Do not put business logic in routers.
- Use Pydantic models for all request and response schemas — never use raw dicts in API boundaries.
- External HTTP calls must be isolated in dedicated async functions, not inlined in route handlers.
- All HTTP errors must be raised as `HTTPException` with explicit status codes and detail messages.
- Log every incoming request and its outcome using the standard `logging` module.
- Environment variables must be read via `os.getenv()` — never hardcode secrets or config values.

## Testing instructions

- Place tests in a `tests/` directory, mirroring the source structure (e.g., `tests/routers/test_weather.py`).
- Use `pytest` with `pytest-asyncio` for async route tests.
- Mock all external HTTP calls — tests must not make real network requests.
- Cover happy path, 4xx error cases, and edge cases for every endpoint.
- Run `python -m pytest` before committing — all tests must pass.

## PR instructions

- Title format: `[scope] Short description` (e.g., `[routers] Add DELETE /subscribe/{id}`).
- Always run the test suite before opening a PR.
- Each PR should address a single concern — avoid mixing unrelated changes.
