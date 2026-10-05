# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 0.4.0

### Added
- `QuartMicroservice`: a microservice that owns a Quart app (`self.app`) and
  serves it with Hypercorn as one of its managed tasks, so the web server
  shares the service lifecycle. `_initialise()` runs before any request is
  accepted; on stop the server stops accepting connections and lets in-flight
  requests finish (`shutdown_timeout`) before `_shutdown()` runs. Registers the
  health check automatically. Override `_create_background_tasks()` to run
  work (e.g. an event consumer) alongside the server.
- `ServerConfiguration`: host, port, shutdown timeout and access log settings,
  plus `server_configuration_items()` for `ConfigurationManager` layouts
  (environment variables such as `SERVER_HOST` and `SERVER_PORT`).
- `run_microservice(service)`: one-line entry point that installs signal
  handlers, initialises and runs a service, and returns a process exit code
  (0 success, 1 failure, 130 interrupted).
- `BaseMicroservice.install_signal_handlers()`: SIGINT and SIGTERM (e.g.
  `docker stop`) trigger a graceful shutdown, with a `signal.signal` fallback
  on Windows.
- `BaseMicroservice.failed`: whether the service stopped because
  initialisation or a task failed.
- `BaseMicroservice.SHUTDOWN_GRACE_PERIOD` / `_shutdown_grace_period()`:
  seconds `stop()` lets tasks finish by themselves before cancelling them
  (default 0, the previous behaviour).
- `hypercorn>=0.18` added as a direct dependency.

### Changed
- Dependencies now use minimum versions instead of exact pins, so projects
  using Weaver get the newest compatible releases: `aiohttp>=3.14.3,<4`,
  `aiosqlite>=0.22.1` (was 0.21.0), `quart>=0.23.1` (was 0.20.0),
  `jsonschema>=4.26,<5`.
- **Minimum Python is now 3.13** (was 3.12), as Quart 0.23 requires it.
  Supported and tested on Python 3.13 and 3.14.
- `BaseMicroservice.run()` now fails fast: if any task raises, the error is
  logged and the whole service stops (previously it waited for every task to
  finish, so a crashed task could go unnoticed). Tasks that finish normally
  do not stop the service.
- `BaseMicroservice.run()` returns only once shutdown has completed, even if
  `stop()` was called from elsewhere.
- `HealthCheckMixin` reports `503 Service Unavailable` while the service is
  shutting down, so load balancers stop sending it traffic.

### Fixed
- CI: Python is now set up in the same job that runs the checks (it was set
  up in a separate job, which runs on a different machine, so it had no
  effect). Lint and tests now run on Python 3.13 and 3.14, plus a run
  with the minimum allowed dependency versions.

---

## [0.3.0] - 2026-08-04

### Changed
- `aiohttp` updated to 3.14.3.

---

## [0.2.1] - 2026-07-07

### Changed
- `aiohttp` updated to 3.14.1.

---

## [0.2.0] - 2026-06-16

### Changed
- `SqliteInterface`: migrated from synchronous `sqlite3` to async `aiosqlite`.
  All query methods (`create_table`, `run_query`, `insert_query`,
  `bulk_insert_query`, `delete_query`, `run_script`) and `_get_connection` are
  now `async`. `is_valid_database` and `ensure_valid` remain synchronous as
  they perform file-header checks only.
- `aiosqlite==0.21.0` added to project dependencies.
- Test suite for `SqliteInterface` converted to `IsolatedAsyncioTestCase`.

### Fixed
- `validate_json` decorator: moved error response construction inside the
  `except TypeError` block, removing a dangling `error_msg` reference that
  would have caused a `NameError` if any non-TypeError exception were raised
  in a future refactor.
- `BaseApiRoute.validate_json_body`: added `jsonschema.exceptions.SchemaError`
  to the caught exception types so a malformed schema returns a 400 response
  instead of propagating an unhandled exception.

### Added
- Unit tests for `validate_json` decorator covering: valid JSON pass-through,
  validation failure, schema mismatch, and TypeError handling.
- Unit test for `BaseApiRoute.validate_json_body` with a malformed schema
  (`SchemaError` path).

---

## [0.2.0a1] - 2026-06-15

### Added
- `ConfigurationManager`: multi-source configuration resolution (environment
  variable -> config file -> default) with type conversion for `str`, `int`,
  `bool`, `path`, `file`, and `directory` types.
- `SqliteInterface`: thread-safe SQLite wrapper with WAL journal mode, foreign
  key enforcement, and a 5-second busy timeout.
- `BaseMicroservice`: abstract async base class providing initialise/run/stop
  lifecycle, asyncio Event-based shutdown signalling, and task management.
- `BaseApiRoute`: base class for Quart route handlers with JSON body validation
  via `jsonschema`.
- `validate_json` decorator for automatic request body validation on route
  handlers.
- `RestClient`: async HTTP client wrapping `aiohttp` with consistent
  `ApiResponse` returns and timeout/error handling for all standard HTTP verbs.
- `HttpContentType`: content-type constants and detection helpers including
  vendor MIME type support.
- `ApiResponse`: standardised response dataclass with a `success` property for
  HTTP 2xx detection.
- `LoggingConfiguration`: immutable logging settings dataclass.
- CI/CD pipeline (GitHub Actions) enforcing Pylint greater or equal 10.0 and 100% unit test
  coverage on every pull request.
