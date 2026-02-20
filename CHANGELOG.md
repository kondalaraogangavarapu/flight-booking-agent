# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
