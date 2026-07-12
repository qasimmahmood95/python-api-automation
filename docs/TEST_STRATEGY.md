# Test Strategy

## 1. Purpose & Scope

This suite provides functional API-level test coverage of the
[restful-booker](https://restful-booker.herokuapp.com) service: authentication (`/auth`),
health check (`/ping`), and the full booking CRUD lifecycle (`/booking`), including
request validation behavior for malformed payloads.

**Out of scope:**

- UI testing — restful-booker's web front end is not exercised.
- Load, performance, and soak testing.
- The API's persistence internals (in-memory store, reset behavior on the public
  instance). Tests treat the service as a black box and assert only on its HTTP contract.

## 2. Test Approach

- **Risk-based coverage.** Effort is weighted toward the behaviors a consumer depends on:
  token issuance, booking create/read/update/delete, and rejection of invalid input.
  Low-risk permutations are represented, not enumerated.
- **Contract validation.** Responses are validated against Pydantic models (Booking,
  BookingCreated, AuthToken), asserting the full response shape and types rather than
  spot-checking single fields.
- **Positive and negative paths.** Every resource has happy-path coverage plus
  representative negative cases (bad credentials, missing/invalid fields, nonexistent
  IDs, missing auth on mutating calls).
- **Test pyramid position.** This is an API-level integration suite against a black-box
  service. There is no application code under test in this repo, so there is no unit
  layer here; the suite sits at the service/API tier and is designed to run fast enough
  (parallelized via `pytest-xdist`) to gate every pull request.

## 3. Test Design Principles

- **Independence and isolation.** Tests never depend on execution order or on data left
  behind by other tests. The `booking` factory fixture creates its own record and
  deletes it on teardown, so the suite is self-cleaning even against the shared public
  instance.
- **Dynamic test data.** Booking payloads are generated with Faker, avoiding name/date
  collisions between runs and between concurrent CI jobs. Static JSON files are reserved
  for invalid-shape payloads, where the exact malformation is the point.
- **No assertions in helpers or clients.** `BaseClient`, `AuthClient`, and
  `BookingClient` return responses; all assertions live in tests, so a failure always
  points at the test that owns the behavior.
- **One behavior per test.** Each test asserts a single observable behavior with a name
  that states it; multi-step lifecycle checks are explicit CRUD-sequence tests, not
  accidental coupling.
- **Parametrization for case tables.** Families of same-shaped cases (invalid payload
  variants, auth failure modes) are one parametrized test with readable `ids`, not
  copy-pasted near-duplicates.
- **Markers.** `smoke` and `negative` markers (registered, `--strict-markers`) allow
  fast subset runs, e.g. `make smoke` or `pytest -m negative`.

## 4. Environments

| Environment | Base URL | Role |
|---|---|---|
| Local Docker (`mwinteringham/restfulbooker`, port 3001) | `http://localhost:3001` | Deterministic target for PR-gating CI and hermetic local runs (`make docker-test`) |
| Live Heroku instance | `https://restful-booker.herokuapp.com` | Nightly real-world smoke against the public deployment |

The base URL is injected via `pytest-base-url` — the `--base-url` CLI flag overrides the
`base_url` default in `pyproject.toml` — so
the same suite runs unchanged against either target. CI's PR workflow runs the Docker
image as a service container; the scheduled nightly workflow points at the live URL.
Credentials for the demo API (`admin`/`password123`) are public documentation values,
supplied via env vars with those defaults — they are configuration, not secrets.

## 5. Flakiness Policy

- **PR gating is deterministic.** Pull requests run only against the local Docker
  container, which has no cold starts, shared state from other users, or network
  variance. A red PR build means a real regression; retries are not enabled there.
- **Reruns are confined to the nightly live job.** `pytest-rerunfailures` is enabled
  only when targeting the public Heroku instance, to tolerate cold starts and transient
  platform noise. A test that passes only on rerun is recorded and reviewed — reruns are
  a signal of instability to investigate, never a fix that closes the issue.
- **Hung-request protection.** Every request goes through `BaseClient`, which enforces
  connect/read timeouts and a bounded retry adapter, so a stalled endpoint fails a test
  quickly instead of hanging the suite or a CI runner.

## 6. Known API Quirks

restful-booker is intentionally quirky. The suite asserts the documented actual
behavior — commented in code so the assertions read as deliberate choices, not mistakes.

| Endpoint / action | Conventional expectation | Actual behavior | Assertion choice |
|---|---|---|---|
| `GET /ping` | `200 OK` | Returns `201 Created` | Assert `201`; comment references the documented quirk |
| `POST /auth` with bad credentials | `401/403` | Returns `200` with body `{"reason": "Bad credentials"}` | Assert `200` **and** the `reason` field — the body, not the status, carries the failure |
| `POST /booking` with invalid payload | `400 Bad Request` | Returns `500 Internal Server Error` | Assert `500`; noted as the API's (poor but stable) validation contract |
| `DELETE /booking/{id}` | `200` or `204` | Returns `201 Created` | Assert `201`, then confirm deletion via a follow-up `GET` returning `404` |

If the upstream service ever corrects these, the failures will be loud and localized,
which is the desired outcome for a contract suite.

## 7. What Is Deliberately Not Automated

- **Load/performance testing.** Meaningless against a shared free-tier demo instance,
  and hostile to other users of it; would need a dedicated environment and tooling
  (e.g., Locust/k6) outside this suite's purpose.
- **Fuzzing beyond representative invalid payloads.** The API collapses all validation
  failures into `500`, so exhaustive fuzzing yields no additional signal; a small curated
  set of invalid-shape cases covers the observable contract.
- **Exhaustive date-boundary matrices.** Checkin/checkout combinations are covered by
  representative cases; a full boundary matrix inflates runtime without proportional
  risk reduction on a demo API with known-loose date handling.
- **Persistence and data-reset verification.** The public instance resets its data on
  its own schedule; asserting on storage behavior would couple tests to platform
  internals rather than the HTTP contract.
- **Auth token expiry timing.** Token lifetime is not documented as a contract; the
  session-scoped token fixture keeps runs well within any observed validity window.
