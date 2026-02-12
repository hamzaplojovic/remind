# Release & Homebrew Installation Guide

This guide explains how to release new versions of Remind and automate Homebrew formula updates.

## Automated Release Process

The project uses GitHub Actions to fully automate building, testing, and releasing binaries for multiple platforms.

### Release Workflow (`.github/workflows/release-binaries.yml`)

The workflow is triggered when you push a version tag and automatically:

1. **Builds binaries** for three platforms:
   - macOS x86_64 (Intel)
   - macOS ARM64 (Apple Silicon)
   - Linux x86_64

2. **Creates GitHub Release** with:
   - All three platform-specific binaries
   - SHA256SUMS file for verification

3. **Updates Homebrew formula** with:
   - Correct download URLs for each platform
   - Verified SHA256 checksums from GitHub release

4. **Commits formula update** to repository
   - Updates `apps/cli/build_tools/homebrew_formula.rb`

## Creating a Release

### Step 1: Update version number

Update the version in `apps/cli/pyproject.toml`:

```toml
[project]
version = "0.2.0"
```

### Step 2: Commit and tag

```bash
git commit -am "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main
git push origin v0.2.0
```

That's it! The GitHub Actions workflow will:
- Build binaries for all three platforms
- Create a GitHub release with the binaries
- Generate and verify SHA256 checksums
- Update the Homebrew formula automatically
- Commit the formula update

### Step 3: Monitor the workflow

Watch the progress in GitHub Actions:

```
https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
```

**Expected jobs**:
- `build [macos x86_64]` - Builds on macOS 13 (Intel)
- `build [macos arm64]` - Builds on macOS latest (Apple Silicon)
- `build [linux x86_64]` - Builds on Ubuntu latest
- `create-release` - Creates GitHub release with all binaries
- `update-homebrew-formula` - Updates homebrew formula with checksums
- `create-homebrew-pr` (optional) - Creates PR to homebrew-core

## Installation Methods

### Method 1: Official Homebrew (Recommended)

After the formula is accepted by Homebrew/homebrew-core:

```bash
brew install remind-cli
```

### Method 2: Community Homebrew Tap

Until the formula is in homebrew-core, use the community tap:

```bash
brew tap hamzaplojovic/remind https://github.com/hamzaplojovic/homebrew-remind
brew install remind-cli
```

### Method 3: Direct from GitHub Release

Install directly from GitHub releases:

```bash
# macOS Intel
wget https://github.com/hamzaplojovic/remind/releases/download/v0.2.0/remind-macos-x86_64
chmod +x remind-macos-x86_64
sudo mv remind-macos-x86_64 /usr/local/bin/remind

# macOS Apple Silicon
wget https://github.com/hamzaplojovic/remind/releases/download/v0.2.0/remind-macos-arm64
chmod +x remind-macos-arm64
sudo mv remind-macos-arm64 /usr/local/bin/remind

# Linux
wget https://github.com/hamzaplojovic/remind/releases/download/v0.2.0/remind-linux-x86_64
chmod +x remind-linux-x86_64
sudo mv remind-linux-x86_64 /usr/local/bin/remind
```

### Method 4: Curl Script (Recommended for CI/CD)

```bash
curl -sSL https://remind.dev/install.sh | bash
```

## Verifying Releases

### Check SHA256 checksums

After downloading a binary, verify it with the SHA256SUMS file:

```bash
# Download the binary and SHA256SUMS
wget https://github.com/hamzaplojovic/remind/releases/download/v0.2.0/remind-macos-x86_64
wget https://github.com/hamzaplojovic/remind/releases/download/v0.2.0/SHA256SUMS

# Verify
shasum -c SHA256SUMS

# Expected output:
# remind-macos-x86_64: OK
```

### Test the binary

```bash
./remind --version
./remind --help
./remind add "Test reminder" --due "tomorrow 5pm"
./remind list
```

## Homebrew Formula Submission

### Before submitting to homebrew-core

1. **Ensure the formula works**:
   ```bash
   brew install --build-from-source ./apps/cli/build_tools/homebrew_formula.rb
   remind --version
   ```

2. **Run Homebrew tests**:
   ```bash
   brew test remind-cli
   ```

3. **Style check**:
   ```bash
   brew audit remind-cli
   ```

### Submit to homebrew-core

1. Fork [Homebrew/homebrew-core](https://github.com/Homebrew/homebrew-core)

2. Add the formula to `Formula/r/remind-cli.rb`:
   ```bash
   cp apps/cli/build_tools/homebrew_formula.rb <homebrew-core-fork>/Formula/r/remind-cli.rb
   ```

3. Commit and push:
   ```bash
   cd <homebrew-core-fork>
   git add Formula/r/remind-cli.rb
   git commit -m "Add remind-cli formula for v0.2.0"
   git push origin add-remind-cli
   ```

4. Create a Pull Request on Homebrew/homebrew-core with:
   - Title: `Add remind-cli formula`
   - Description mentioning:
     - Version and release URL
     - Testing instructions
     - Why you think it belongs in homebrew-core

## Troubleshooting

### Build fails on GitHub Actions

**Check the logs**:
```
https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
```

**Common issues**:
- Python dependencies not installed: Check `apps/cli/pyproject.toml`
- PyInstaller failing: Check `apps/cli/build_tools/build.py`
- Binary naming mismatch: Ensure `matrix.binary-name` matches expected names

### Homebrew formula generation fails

**Run locally to debug**:
```bash
cd apps/cli
uv sync
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v0.2.0
```

**Expected output**:
- `macOS x86_64 SHA256: <hash>`
- `macOS arm64  SHA256: <hash>`
- `Linux x86_64 SHA256: <hash>`
- `✓ Formula written to build_tools/homebrew_formula.rb`

### SHA256SUMS file missing

**Check GitHub release**:
- Download the release from: https://github.com/hamzaplojovic/remind/releases
- Should include `SHA256SUMS` file with all three binaries listed

**If missing**:
- Run workflow again with: `git push origin --delete v0.2.0 && git tag v0.2.0 && git push origin v0.2.0`
- Or manually create checksums:
  ```bash
  shasum -a 256 remind-* > SHA256SUMS
  gh release upload v0.2.0 SHA256SUMS
  ```

## Homebrew Tap Maintenance

If maintaining a community tap at `hamzaplojovic/homebrew-remind`:

1. **Keep in sync** with the main repository formula:
   ```bash
   cd <homebrew-remind-fork>
   cp ../remind/apps/cli/build_tools/homebrew_formula.rb Formula/remind-cli.rb
   git commit -am "Update to latest formula"
   git push
   ```

2. **Test the tap**:
   ```bash
   brew tap hamzaplojovic/remind <path-to-local-fork>
   brew install remind-cli
   remind --version
   ```

## GitHub Actions Secrets (Optional)

For the optional Homebrew PR creation job, add this secret to your repository:

1. Go to Settings → Secrets and variables → Actions
2. Add `HOMEBREW_GITHUB_TOKEN`:
   - Personal access token with `public_repo` scope
   - Used to create PRs on homebrew-core

Without this token, the `create-homebrew-pr` job will be skipped (it's optional).

## Files Involved

- **Workflow**: `.github/workflows/release-binaries.yml`
- **Build script**: `apps/cli/build_tools/build.py`
- **Formula generator**: `apps/cli/build_tools/generate_homebrew_formula.py`
- **Formula template**: `apps/cli/build_tools/homebrew_formula.rb`
- **Installation script**: `infrastructure/scripts/install.sh`

## Next Steps

1. Test the release workflow with a pre-release tag: `v0.1.0-rc1`
2. Monitor build times and optimize if needed
3. Set up the community Homebrew tap repository
4. Submit formula to homebrew-core for official inclusion
