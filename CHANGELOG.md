# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-20

### Changed
- Default `APP_HOST` changed from `0.0.0.0` to `127.0.0.1` for safer local development; Docker container explicitly sets `0.0.0.0` via environment variable
- Dockerfile ENTRYPOINT switched from bare `uvicorn` to `gunicorn` with `UvicornWorker` workers for production-grade process management
- Health check endpoint now returns version and uptime information
- Readiness check endpoint verifies data store accessibility and respects shutdown state
- Docker HEALTHCHECK timeout increased and made configurable via `HEALTH_CHECK_TIMEOUT` env var

### Added
- `VERSION` file for explicit version tracking
- `gunicorn==23.0.0` production dependency for multi-worker process management
- `WEB_CONCURRENCY` and `HEALTH_CHECK_TIMEOUT` environment variable support in Docker
- Transitive dev dependencies pinned in `requirements-dev.txt` for reproducible dev environments

## [0.3.0] - 2026-02-20

### Added
- Graceful shutdown handling via SIGTERM/SIGINT signal handlers using FastAPI lifespan
- `pyproject.toml` with `requires-python = ">=3.12"` for Python version pinning
- Development setup instructions in README.md
- Git tag `v0.1.0` for initial release version tracking

### Changed
- Application version bumped to 0.3.0

## [0.2.0] - 2026-02-20

### Security
- SECRET_KEY no longer defaults to an empty string; an ephemeral key is auto-generated if unset, with a runtime warning urging operators to set it explicitly
- Dockerfile now applies OS-level security updates during build
- Application code is mounted read-only inside the container
- Non-root user shell set to `/usr/sbin/nologin`

### Changed
- Health check uses `127.0.0.1` instead of `localhost` for reliable container networking
- All transitive Python dependencies are pinned to exact versions in `requirements.txt` for reproducible builds

### Added
- `requirements-dev.txt` with testing and linting tools (pytest, black, flake8, mypy)
- `CHANGELOG.md` for structured release notes

## [0.1.0] - 2026-02-20

### Added
- Initial flight booking agent REST API
- Flight search and booking endpoints
- Docker container packaging with multi-stage build
- Health and readiness check endpoints
