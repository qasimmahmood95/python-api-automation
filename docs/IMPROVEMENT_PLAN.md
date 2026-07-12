# Production-Readiness Improvement Plan

> **Status: implemented.** All five phases below have been executed; this document is
> kept as the historical roadmap. See the [README](../README.md) for current usage.
> Deliberate deviations: only `smoke` and `negative` markers are registered (a
> `regression` run is simply the full suite); the `v1.0.0` tag is deferred until
> this branch merges to `main`.

Goal: turn this repo into a production-grade API test framework that demonstrates
Senior SDET-level design to anyone reviewing it — clean architecture, quality gates,
CI/CD, and documented engineering decisions.

Target API stays the same: [restful-booker](https://restful-booker.herokuapp.com)
(with an option to run it locally in Docker for deterministic CI).

---

## Current State Assessment

### What works
- Real end-to-end coverage of the booking CRUD lifecycle plus auth.
- Positive and negative paths are both exercised.
- Externalized JSON test data, separated into `valid/` and `invalid/`.
- `pytest-base-url` used for environment configuration.

### What is broken
| Issue | Location | Impact |
|---|---|---|
| `requirements.txt` is UTF-16 + CRLF (Windows `pip freeze >` artifact) | `requirements.txt` | `pip install -r` fails on Linux/macOS/CI |
| Fixture named `test_create_token` and marked `autouse` | `tests/positive_test.py:14` | Runs (a live HTTP call) before *every* test, even ones that don't need auth; `test_` prefix on a fixture is misleading |
| Token shared via `global token` mutable state | `tests/positive_test.py:12,16` | Fragile, breaks under parallelism, hides dependencies |
| Helper method named `test_create_new_booking` with asserts inside | `pages/common.py:10` | Test-prefixed name on a non-test; assertions in helpers obscure failure origin |
| `json.load(open(...))` at module import time | all test modules + `pages/common.py` | File handles never closed; paths relative to CWD, so the suite only works when run from repo root; I/O at collection time |
| No timeouts on any `requests` call | everywhere | A hung API hangs the whole suite forever |
| No cleanup of created bookings | positive tests | Test pollution on the shared public API |
| `pages/` package name | `pages/common.py` | "Page objects" are a UI-automation concept — a red flag in an API framework to a reviewing SDET |

### What is missing
- README (the single most important file for a portfolio repo — currently absent)
- CI/CD (no GitHub Actions), no test report artifacts
- `conftest.py`, markers, parametrization
- Response schema validation (currently only spot-checks single fields)
- Linting/formatting/type-checking, pre-commit hooks
- Logging of requests/responses for failure diagnosis
- Dev/runtime dependency separation; `colorama` (Windows-only artifact) pinned as a direct dep
- Dockerfile / Makefile / any reproducible-run story

---

## Phase 0 — Fix what is broken (small, immediate wins)

1. Re-encode `requirements.txt` as UTF-8/LF; drop transitive pins (keep direct deps:
   `pytest`, `requests`, `pytest-base-url`) or move to `pyproject.toml` in Phase 2.
2. Add a minimal README so the repo is no longer anonymous (expanded in Phase 4).

## Phase 1 — Framework architecture refactor (the core of the upgrade)

1. **API client layer** — replace `pages/common.py` with `src/clients/`:
   - `BaseClient`: wraps `requests.Session` with base URL joining, default timeout,
     retry adapter, and request/response logging hooks.
   - `AuthClient` (`/auth`) and `BookingClient` (`/ping`, `/booking` CRUD): one method
     per endpoint, returning typed responses. No assertions inside clients.
2. **`conftest.py` with proper fixtures**:
   - `auth_token` — session-scoped (one auth call per run instead of one per test).
   - `booking` — factory fixture that creates a booking and deletes it on teardown
     (test isolation + cleanup on the shared API).
   - Data-loading via `pathlib.Path(__file__)`-anchored helpers with context managers —
     suite runs from any CWD, no leaked file handles.
3. **Restructure tests by resource**, not by polarity:
   - `tests/test_auth.py`, `tests/test_ping.py`, `tests/test_booking_crud.py`,
     `tests/test_booking_validation.py`.
   - Parametrize the three near-identical invalid-payload tests into one
     `@pytest.mark.parametrize` case table with ids.
4. **Response schema validation** — Pydantic models (or `jsonschema`) for Booking and
   Auth responses; assert full contract, not just one field.
5. **Markers** — `smoke`, `regression`, `negative`, registered with
   `--strict-markers`.
6. **Config** — `BASE_URL`, credentials via env vars with sane defaults
   (`pytest-base-url` retained); document the demo creds are public, not secrets.
7. **Document API quirks in code** — restful-booker intentionally returns
   `201` for `/ping`, `200 + "Bad credentials"` for failed auth, and `500` for
   validation errors. Comment these where asserted so they read as informed choices,
   not mistakes.

## Phase 2 — Code quality gates

1. `pyproject.toml` as the single config home (project metadata, pytest, ruff, mypy).
2. **Ruff** for linting + formatting; **mypy** with type hints across `src/`.
3. **pre-commit** hooks: ruff, ruff-format, mypy, end-of-file/trailing-whitespace,
   check-json for `test-data/`.
4. Dependency split: runtime vs dev (`requirements.txt` / `requirements-dev.txt` or
   optional-dependencies in `pyproject.toml`).
5. `Makefile` (or `justfile`): `make install`, `make lint`, `make test`, `make smoke`.

## Phase 3 — CI/CD and reporting

1. **GitHub Actions** (`.github/workflows/ci.yml`):
   - `lint` job: ruff + mypy.
   - `test` job: matrix over Python 3.11/3.12/3.13; runs suite against a
     **restful-booker Docker container as a service** (image `mwinteringham/restfulbooker`)
     so CI is deterministic and not hostage to Heroku cold starts.
   - Scheduled nightly run against the live public URL (real-world smoke).
   - Upload `pytest-html` (or Allure) report as an artifact on every run.
2. **Resilience plugins**: `pytest-xdist` (parallel), `pytest-rerunfailures`
   (flaky live-API tolerance, used only in the nightly live job).
3. **Badges** in README: CI status, Python versions, ruff, license.
4. `dependabot.yml` for weekly pip + actions updates.

## Phase 4 — Portfolio polish (what makes reviewers stop scrolling)

1. **README** with: project purpose, architecture diagram (Mermaid), tech stack,
   project layout tree, how-to-run (local, Docker, CI), marker/reporting usage, and a
   **"Design decisions"** section explaining the client-layer pattern, fixture
   strategy, schema validation, and the API-quirk assertions.
2. **`docs/TEST_STRATEGY.md`** — short test strategy: scope, risk-based coverage,
   what's automated vs. not, flakiness policy. Very few candidate repos have one.
3. **Docker support** — `docker-compose.yml` that stands up restful-booker + runs the
   suite with one command.
4. **Dynamic test data** — `faker`-based booking factory instead of a static "Qasim
   Mahmood" payload; keeps JSON files only for invalid-shape cases.
5. **Allure report published to GitHub Pages** from CI (optional, high visual impact).
6. Conventional commit messages from here on; tag `v1.0.0` when Phases 0–3 land.

---

## Suggested order of execution

| Step | Scope | Effort |
|---|---|---|
| 1 | Phase 0 (fix requirements.txt, stub README) | ~15 min |
| 2 | Phase 1 (architecture refactor) | ~half day |
| 3 | Phase 2 (quality gates) | ~2 h |
| 4 | Phase 3 (CI + reporting) | ~2–3 h |
| 5 | Phase 4 (docs & polish) | ~2–3 h |

Each phase lands as its own commit(s) so the git history itself reads like a
professional changelog.
