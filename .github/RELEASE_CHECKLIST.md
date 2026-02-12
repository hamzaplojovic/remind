# Release Checklist

Use this checklist before creating your first release and for each subsequent release.

## Pre-Release Setup (One-time)

- [ ] Repository is public (required for GitHub releases)
- [ ] `HOMEBREW_GITHUB_TOKEN` secret is configured (optional, for automatic Homebrew PRs)
- [ ] `.github/workflows/release-binaries.yml` is in place
- [ ] `apps/cli/build_tools/build.py` exists and is executable
- [ ] `apps/cli/build_tools/generate_homebrew_formula.py` exists and is executable
- [ ] `apps/cli/pyproject.toml` has correct version and dependencies
- [ ] `RELEASE.md` is accessible to users
- [ ] README has installation instructions with GitHub release link

## Before Each Release

### Version Management

- [ ] Update version in `apps/cli/pyproject.toml`
  ```toml
  [project]
  version = "x.y.z"
  ```

- [ ] Update version in README (if mentioned)
- [ ] Review CHANGELOG (if you maintain one)
- [ ] Commit version bump:
  ```bash
  git commit -am "chore: bump version to x.y.z"
  ```

### Code Quality

- [ ] All tests pass locally:
  ```bash
  make test
  # or
  pytest apps/ packages/ -v
  ```

- [ ] Linting passes:
  ```bash
  ruff check apps/ packages/
  ruff format --check apps/ packages/
  mypy apps/cli/src
  ```

- [ ] No uncommitted changes:
  ```bash
  git status
  ```

### Build Verification (Recommended)

- [ ] Local binary builds successfully:
  ```bash
  cd apps/cli
  uv sync --extra build
  uv run python build_tools/build.py
  ./dist/remind --version
  ```

- [ ] Binary works for basic commands:
  ```bash
  ./dist/remind --help
  ./dist/remind add "Test" --due "tomorrow"
  ./dist/remind list
  ```

- [ ] Daemon works (macOS/Linux):
  ```bash
  ./dist/remind scheduler --status
  ```

### Git Hygiene

- [ ] Working directory is clean:
  ```bash
  git status
  # Should show: "On branch main, nothing to commit, working tree clean"
  ```

- [ ] You're on the correct branch:
  ```bash
  git rev-parse --abbrev-ref HEAD
  # Should show: main
  ```

- [ ] Main branch is up to date:
  ```bash
  git pull origin main
  ```

## Creating the Release

### Tag Creation (The trigger!)

```bash
# Create an annotated tag
git tag -a v1.0.0 -m "Release v1.0.0"

# OR create a lightweight tag
git tag v1.0.0

# Push the tag to GitHub
git push origin v1.0.0
```

✅ **This triggers the GitHub Actions release-binaries workflow**

### Monitor the Workflow

- [ ] Visit: https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
- [ ] Watch the builds:
  - [ ] `build [macos x86_64]` - On `macos-13`
  - [ ] `build [macos arm64]` - On `macos-latest`
  - [ ] `build [linux x86_64]` - On `ubuntu-latest`
- [ ] Wait for all builds to complete (~5-10 min each)
- [ ] Confirm `create-release` job succeeds
- [ ] Confirm `update-homebrew-formula` job succeeds
- [ ] Check `create-homebrew-pr` job (may be skipped if token not configured)

**Typical workflow duration**: 15-25 minutes

## After Release

### Verify GitHub Release

- [ ] Release exists: https://github.com/hamzaplojovic/remind/releases
- [ ] All three binaries are present:
  - [ ] `remind-macos-x86_64`
  - [ ] `remind-macos-arm64`
  - [ ] `remind-linux-x86_64`
- [ ] SHA256SUMS file is present
- [ ] Release notes/description is accurate

### Test Downloaded Binaries

```bash
# Download and test each binary
cd /tmp

# macOS x86_64
wget https://github.com/hamzaplojovic/remind/releases/download/v1.0.0/remind-macos-x86_64
chmod +x remind-macos-x86_64
./remind-macos-x86_64 --version
```

### Verify Homebrew Formula

- [ ] Formula was automatically updated:
  - Check: `apps/cli/build_tools/homebrew_formula.rb`
  - Verify: Correct version number
  - Verify: Correct SHA256 hashes
  - Verify: Correct download URLs

### Test Homebrew Installation (if applicable)

**Using community tap** (if you maintain one):
```bash
brew tap hamzaplojovic/remind
brew install remind-cli
remind --version
```

**Or test locally**:
```bash
brew install --build-from-source ./apps/cli/build_tools/homebrew_formula.rb
remind --version
remind --help
```

### Announce Release

- [ ] Update website/landing page
- [ ] Post to social media
- [ ] Update Discord/Slack
- [ ] Email users (if applicable)
- [ ] Create blog post (if significant update)

## Troubleshooting During Release

### Build fails on GitHub Actions

1. **Check workflow logs**:
   - https://github.com/hamzaplojovic/remind/actions
   - Click the failed job
   - Review error messages

2. **Common issues**:
   - Python dependencies not found → Check `pyproject.toml`
   - PyInstaller fails → Test locally with `uv run python build_tools/build.py`
   - Binary naming mismatch → Check workflow `matrix.binary-name`

3. **Fix and retry**:
   ```bash
   # Delete the tag locally
   git tag -d v1.0.0

   # Fix the issue
   # ...

   # Recreate and push tag
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0
   ```

### Homebrew formula generation fails

1. **Check formula generation script output**:
   - Visit workflow logs
   - Look for `Generate Homebrew formula` step
   - Review error messages

2. **Test locally**:
   ```bash
   cd apps/cli
   uv sync
   uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.0
   ```

3. **Expected output**:
   ```
   Generating Homebrew formula for hamzaplojovic/remind v1.0.0...
   macOS x86_64 SHA256: abc123...
   macOS arm64  SHA256: def456...
   Linux x86_64 SHA256: ghi789...
   ✓ Formula written to build_tools/homebrew_formula.rb
   ```

### Release doesn't appear on GitHub

1. **Tag might not have pushed**:
   ```bash
   git push origin v1.0.0
   git push origin --tags
   ```

2. **Tag might be lightweight instead of annotated**:
   ```bash
   git tag -a v1.0.0 -m "Release v1.0.0"
   git push origin v1.0.0 --force
   ```

3. **Check if workflow is enabled**:
   - Settings → Actions → General
   - Ensure "Allow all actions and reusable workflows" is selected

## Rollback (if something goes wrong)

```bash
# Delete the tag locally
git tag -d v1.0.0

# Delete the tag on GitHub
git push origin :refs/tags/v1.0.0

# Delete the GitHub release (manually via web UI)
# https://github.com/hamzaplojovic/remind/releases

# Revert the formula update (if merged)
git revert <commit-hash>
git push origin main
```

## Performance Tips

- **Parallel builds**: All three platforms build simultaneously (~10 min)
- **Caching**: Dependencies are cached after first build
- **File size**: Final binary is ~30-50MB (depending on Python size)
- **Network**: Release upload depends on your internet speed

## Next Releases

Keep this checklist handy for each release. Update it if you find:
- New pre-flight checks needed
- Build steps that frequently fail
- Additional platforms to support
- Distribution channels to test

---

**Questions?** See:
- [`RELEASE.md`](../RELEASE.md) - Detailed release guide
- [`CI_CD_GUIDE.md`](../infrastructure/CI_CD_GUIDE.md) - CI/CD system overview
- [GitHub Actions Docs](https://docs.github.com/actions) - Official documentation
