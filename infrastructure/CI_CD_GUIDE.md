# CI/CD and Release Automation Guide

This document explains how the Remind project uses GitHub Actions for continuous integration, testing, and automated releases.

## GitHub Actions Workflows

### Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  GitHub Actions Workflows                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  On Push to Main/PR:                                            │
│  ┌─────────────────┬──────────────┬──────────────┐              │
│  │  lint.yml       │ test-cli.yml │ test-backend │              │
│  │  (ruff, mypy)   │ (pytest)     │ (pytest)     │              │
│  └─────────────────┴──────────────┴──────────────┘              │
│                                                                   │
│  On Push (all branches):                                        │
│  ┌────────────────────────────────────────────┐                 │
│  │  build-docker.yml                           │                 │
│  │  (Build Docker images)                      │                 │
│  └────────────────────────────────────────────┘                 │
│                                                                   │
│  On Version Tags (v*.*.* pattern):                             │
│  ┌─────────────────────────────────────────────────────┐        │
│  │                 release-binaries.yml                │        │
│  ├──────────────────┬──────────────────┬──────────────┤        │
│  │ build [macos x86]│ build [macos arm]│ build [linux]│        │
│  └──────────────────┴──────────────────┴──────────────┘        │
│                  │                                              │
│                  ▼                                              │
│            create-release                                      │
│            (GitHub Release)                                    │
│                  │                                              │
│                  ▼                                              │
│         update-homebrew-formula                               │
│         (Generate & Commit)                                   │
│                  │                                              │
│                  ▼                                              │
│          create-homebrew-pr (optional)                        │
│          (Homebrew/homebrew-core)                             │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Workflows

### 1. Lint Workflow (`.github/workflows/lint.yml`)

**Trigger**: Push to any branch, Pull requests

**Purpose**: Code quality checks

**Jobs**:
- `ruff`: Code style and formatting
- `mypy`: Type checking

**Runs on**: `ubuntu-latest`

### 2. CLI Tests (`.github/workflows/test-cli.yml`)

**Trigger**: Push to any branch, Pull requests

**Purpose**: Unit and integration tests for CLI

**Strategy**: Matrix of Python versions and operating systems
- Python 3.12, 3.13
- macOS (latest), Ubuntu (latest)

**Runs on**: Platform-specific runners

### 3. Backend Tests (`.github/workflows/test-backend.yml`)

**Trigger**: Push to any branch, Pull requests

**Purpose**: Backend API tests with PostgreSQL

**Services**: PostgreSQL database

**Runs on**: `ubuntu-latest`

### 4. Docker Build (`.github/workflows/build-docker.yml`)

**Trigger**: Push to any branch

**Purpose**: Build and push Docker images

**Images built**:
- `ghcr.io/hamzaplojovic/remind-backend:latest`
- `ghcr.io/hamzaplojovic/remind-backend:main` (if on main)
- `ghcr.io/hamzaplojovic/remind-backend:tag-name` (if tag)

**Runs on**: `ubuntu-latest`

### 5. Release Binaries (`.github/workflows/release-binaries.yml`) ⭐

**Trigger**: Push of version tags matching `v[0-9]+.[0-9]+.[0-9]+*`

**Purpose**: Automated cross-platform build, release, and Homebrew formula generation

**Platform Coverage**:
- macOS x86_64 (Intel) - runs on `macos-13`
- macOS ARM64 (Apple Silicon) - runs on `macos-latest`
- Linux x86_64 - runs on `ubuntu-latest`

**Release Process**:
1. **Build** (3 parallel jobs)
   - Each platform builds standalone binary using PyInstaller
   - Generates SHA256 checksum for each binary

2. **Create Release**
   - Downloads all built binaries and checksums
   - Creates GitHub release
   - Uploads binaries and SHA256SUMS file

3. **Update Homebrew Formula**
   - Runs `generate_homebrew_formula.py`
   - Fetches checksums from GitHub release
   - Updates `apps/cli/build_tools/homebrew_formula.rb`
   - Commits and pushes formula update

4. **Create Homebrew PR** (optional)
   - Creates PR to `Homebrew/homebrew-core`
   - Requires `HOMEBREW_GITHUB_TOKEN` secret

## Setting Up Local Development

### Prerequisites

- Python 3.12+
- `uv` package manager
- Docker (optional, for backend testing)
- PostgreSQL (optional, for backend testing)

### Installation

```bash
# Install dependencies
uv sync --all-extras

# Or specific groups
uv sync --all-extras --group dev --group build
```

### Running Tests Locally

**All tests**:
```bash
make test
```

**CLI tests only**:
```bash
make test-cli
```

**Backend tests**:
```bash
make test-backend
```

**Specific test file**:
```bash
pytest apps/cli/tests/test_commands.py -v
```

**With coverage**:
```bash
pytest --cov=apps/cli --cov=apps/backend --cov-report=html
```

### Running Linters Locally

**Ruff (lint and format)**:
```bash
# Check only
ruff check apps/ packages/

# Format files
ruff format apps/ packages/
```

**Mypy (type check)**:
```bash
mypy apps/cli/src apps/backend/src packages/shared/src packages/database/src
```

### Building Docker Images Locally

```bash
# Build backend image
docker build -f infrastructure/docker/backend.Dockerfile -t remind-backend:local .

# Run with docker-compose
docker-compose -f infrastructure/docker/docker-compose.yml up
```

## Building and Testing Binaries Locally

### Build PyInstaller Binary

```bash
cd apps/cli
uv sync --extra build
uv run python build_tools/build.py

# Binary is in: dist/remind
./dist/remind --version
```

### Test Binary

```bash
# Test basic commands
./dist/remind --help
./dist/remind add "Test" --due "tomorrow"
./dist/remind list

# Test daemon features
./dist/remind scheduler --status
./dist/remind scheduler --enable
```

### Generate SHA256SUMS

```bash
cd apps/cli/dist
shasum -a 256 remind > SHA256SUMS
cat SHA256SUMS
```

### Test Homebrew Formula (macOS)

```bash
# Install from local formula
brew install --build-from-source ./apps/cli/build_tools/homebrew_formula.rb

# Test installation
remind --version
remind --help

# Verify Homebrew
brew list | grep remind
```

## Creating a Release

See [`RELEASE.md`](../RELEASE.md) for detailed release instructions.

**Quick version**:

```bash
# Update version in pyproject.toml
# Commit changes
git commit -am "chore: bump version to 1.0.1"

# Tag the release
git tag v1.0.1
git push origin main
git push origin v1.0.1

# Watch the workflow at:
# https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
```

## GitHub Secrets Configuration

Required and optional secrets for GitHub Actions:

### Required (for release automation to work)

None! The default `GITHUB_TOKEN` provides sufficient permissions for creating releases.

### Optional (for enhanced features)

**`HOMEBREW_GITHUB_TOKEN`**:
- **Purpose**: Create PRs on Homebrew/homebrew-core repository
- **Scope**: `public_repo`
- **How to create**:
  1. Go to GitHub Settings → Developer settings → Personal access tokens
  2. Create a classic token with `public_repo` scope
  3. Add to repository Secrets as `HOMEBREW_GITHUB_TOKEN`
- **Note**: Without this, the `create-homebrew-pr` job is skipped (optional)

## Monitoring CI/CD

### GitHub Actions Dashboard

View all workflows:
```
https://github.com/hamzaplojovic/remind/actions
```

Filter by workflow type:
```
https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
```

### Status Badges

Add to README:
```markdown
[![CI/CD](https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml/badge.svg)](https://github.com/hamzaplojovic/remind/actions)
```

### Build Notifications

Configure in GitHub Settings → Notifications → Actions

## Troubleshooting

### Workflow fails with "missing Python"

**Solution**: Ensure `actions/setup-python@v4` is configured correctly:
```yaml
- uses: actions/setup-python@v4
  with:
    python-version: '3.13'
```

### Linting fails

**Locally test**: Run `ruff check` and `ruff format` before pushing
```bash
ruff check --fix apps/
ruff format apps/
```

### Tests fail in CI but pass locally

**Possible causes**:
- Python version mismatch
- Missing dependencies
- Platform-specific issues
- Environment variables

**Debug**:
1. Check Python versions in workflow vs. local
2. Run `uv sync --frozen` to ensure reproducibility
3. Check for platform-specific code (macOS vs Linux)

### Release binary build fails

**Check**:
1. PyInstaller requirements in `pyproject.toml`
2. Build script at `apps/cli/build_tools/build.py`
3. Supported Python version (3.12+)

**Debug locally**:
```bash
cd apps/cli
uv sync --extra build
uv run python build_tools/build.py
```

### Homebrew formula generation fails

**Check**:
1. GitHub release has all three binaries
2. SHA256SUMS file is present
3. Repository name is correct in script

**Manual generation**:
```bash
cd apps/cli
uv sync
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.1
```

## Performance Optimization

### Caching Dependencies

The workflows already cache Python dependencies via `actions/setup-python@v4`:
```yaml
- uses: actions/setup-python@v4
  with:
    cache: 'pip'
    cache-dependency-path: '**/pyproject.toml'
```

### Parallel Jobs

The release workflow uses matrix strategy for parallel platform builds:
```yaml
strategy:
  matrix:
    include:
      - platform: macos
        runs-on: macos-13
      - platform: macos
        runs-on: macos-latest
      - platform: linux
        runs-on: ubuntu-latest
```

Expected build times:
- Each platform build: ~5-10 minutes
- Create release: ~1 minute
- Update formula: ~2 minutes

**Total release time**: ~15-25 minutes

## Advanced: Custom Workflows

### Adding a new test matrix

Edit `.github/workflows/test-cli.yml`:
```yaml
strategy:
  matrix:
    python-version: ['3.12', '3.13', '3.14']
    os: [macos-latest, ubuntu-latest, windows-latest]
```

### Adding pre-release workflows

Create `.github/workflows/pre-release.yml`:
```yaml
on:
  push:
    tags:
      - 'v*-alpha'
      - 'v*-beta'
      - 'v*-rc*'
```

### Slack notifications

Add to any workflow:
```yaml
- name: Slack Notification
  uses: slackapi/slack-github-action@v1
  if: failure()
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
```

## Next Steps

1. Test the full release workflow with a pre-release: `v1.0.0-rc1`
2. Set up `HOMEBREW_GITHUB_TOKEN` if you want automatic Homebrew PRs
3. Set up Slack notifications (optional)
4. Document internal release process for team
5. Monitor build times and optimize if needed
