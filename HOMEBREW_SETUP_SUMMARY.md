# Homebrew CI/CD Setup - Complete Summary

## What Was Built

A fully automated release pipeline that:

1. **Builds binaries** for three platforms when you push a version tag
2. **Creates GitHub releases** with all binaries and checksums
3. **Generates Homebrew formulas** with correct SHA256 hashes
4. **Optionally creates PRs** to homebrew-core (with GitHub token)

## Files Created/Modified

### GitHub Actions Workflow
- **Created**: `.github/workflows/release-binaries.yml` (150 lines)
  - Builds on macOS x86_64, macOS arm64, and Linux x86_64
  - Creates GitHub release with binaries and SHA256SUMS
  - Generates and commits Homebrew formula
  - Optionally creates PR to homebrew-core

### Build Tools
- **Modified**: `apps/cli/build_tools/generate_homebrew_formula.py`
  - Added Linux binary SHA support
  - Fixed repository name handling
  - Improved error messages

- **Updated**: `apps/cli/build_tools/homebrew_formula.rb`
  - Fixed class name to `RemindCli`
  - Corrected binary naming and installation
  - Added proper test assertion

### Documentation
- **Created**: `RELEASE.md` (250 lines)
  - Complete release workflow walkthrough
  - Installation method comparison
  - Homebrew formula submission guide
  - Troubleshooting section

- **Created**: `infrastructure/CI_CD_GUIDE.md` (350 lines)
  - Workflow architecture diagram
  - Local development setup
  - Build verification instructions
  - Performance optimization tips

- **Created**: `.github/RELEASE_CHECKLIST.md` (200 lines)
  - Pre-release verification checklist
  - Step-by-step release process
  - Troubleshooting guide
  - Rollback procedures

- **Updated**: `INSTALLATION.md`
  - Added automated release overview
  - Cross-referenced new documentation

## How to Use (Quick Start)

### Create Your First Release

```bash
# 1. Update version in apps/cli/pyproject.toml
# 2. Commit the change
git commit -am "chore: bump version to 1.0.0"

# 3. Create and push a version tag
git tag v1.0.0
git push origin v1.0.0

# 4. Watch the workflow
# → https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml
# (Builds complete in 15-25 minutes)

# 5. Verify the release
# → https://github.com/hamzaplojovic/remind/releases
# Should have: remind-macos-x86_64, remind-macos-arm64, remind-linux-x86_64, SHA256SUMS
```

### Installation Methods (Post-Release)

**Official Homebrew** (once submitted to homebrew-core):
```bash
brew install remind-cli
```

**Community Homebrew Tap**:
```bash
brew tap hamzaplojovic/remind https://github.com/hamzaplojovic/homebrew-remind
brew install remind-cli
```

**Direct from GitHub**:
```bash
wget https://github.com/hamzaplojovic/remind/releases/download/v1.0.0/remind-linux-x86_64
chmod +x remind-linux-x86_64
sudo mv remind-linux-x86_64 /usr/local/bin/remind
```

**Curl Installation Script**:
```bash
curl -sSL https://remind.dev/install.sh | bash
```

## Architecture

### Release Workflow (`.github/workflows/release-binaries.yml`)

```
┌─────────────────────────────────────────────────────────┐
│  Git Tag Push (v1.0.0)                                  │
└──────────────────────┬──────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       ▼               ▼               ▼
   ┌────────┐   ┌────────┐   ┌────────┐
   │ macOS  │   │ macOS  │   │ Linux  │
   │x86_64  │   │ arm64  │   │x86_64  │
   │ build  │   │ build  │   │ build  │
   └────┬───┘   └────┬───┘   └────┬───┘
        │            │            │
        └────────────┼────────────┘
                     │
                     ▼
            ┌─────────────────┐
            │ Create Release  │
            │ + Binaries      │
            │ + SHA256SUMS    │
            └────────┬────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │Update Homebrew      │
            │Formula + Checksums  │
            │(Auto-commit)        │
            └────────┬────────────┘
                     │
                     ▼
            ┌─────────────────────┐
            │Create Homebrew PR   │
            │(optional, needs     │
            │HOMEBREW_TOKEN)      │
            └─────────────────────┘
```

### Build Runners

| Platform | Runner | Architecture | Notes |
|----------|--------|--------------|-------|
| macOS x86_64 | `macos-13` | Intel | Latest macOS 13 image |
| macOS arm64 | `macos-latest` | Apple Silicon | Latest macOS image |
| Linux x86_64 | `ubuntu-latest` | x86_64 | Latest Ubuntu image |

### Build Time Estimate

- Per-platform build: **5-10 minutes**
- Create release: **1 minute**
- Update formula: **2 minutes**
- **Total**: **15-25 minutes**

(First build may be slightly longer due to dependency installation)

## Setup Checklist

### Immediate Setup (Required)

- ✅ `.github/workflows/release-binaries.yml` - Created
- ✅ `apps/cli/build_tools/generate_homebrew_formula.py` - Updated
- ✅ `apps/cli/build_tools/homebrew_formula.rb` - Updated
- ✅ Documentation files - Created
- ✅ Checklist for QA - Created

### Optional Setup (Nice to have)

- ⬜ Set `HOMEBREW_GITHUB_TOKEN` secret for automatic Homebrew PRs
- ⬜ Set up community Homebrew tap at `hamzaplojovic/homebrew-remind`
- ⬜ Update website installation instructions
- ⬜ Create landing page at `remind.dev` (for curl script)

## Testing the Workflow

### Dry Run (Recommended before first real release)

```bash
# Create a pre-release tag to test the workflow without triggering real release
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# Monitor at: https://github.com/hamzaplojovic/remind/actions
# Once confirmed working, delete the tag:
git tag -d v1.0.0-rc1
git push origin :refs/tags/v1.0.0-rc1
```

### Local Testing

```bash
# Test that the build script works
cd apps/cli
uv sync --extra build
uv run python build_tools/build.py

# Verify binary
./dist/remind --version
./dist/remind --help

# Test formula generation
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.0-test
```

## Key Features

### ✅ Cross-Platform Support

- Builds native binaries for 3 platforms
- Each platform uses appropriate runner (macOS for macOS, Linux for Linux)
- No cross-compilation complexity

### ✅ Automated Verification

- SHA256 checksums generated for each binary
- SHA256SUMS file included in release
- Checksums verified before formula generation

### ✅ Homebrew Integration

- Automatic formula generation with correct checksums
- Formula committed to repository
- Optional automatic PR to homebrew-core
- Easy tap installation: `brew tap hamzaplojovic/remind`

### ✅ Production Ready

- Atomic releases (all or nothing)
- Checksums prevent corruption
- Formula automatically keeps in sync
- Clear error messages for debugging

## Next Steps

### Immediate (Before First Release)

1. Review the workflow: `.github/workflows/release-binaries.yml`
2. Read `RELEASE.md` for complete instructions
3. Follow the checklist: `.github/RELEASE_CHECKLIST.md`

### For Your First Release

1. Update version in `apps/cli/pyproject.toml`
2. Test locally: `cd apps/cli && uv run python build_tools/build.py`
3. Commit and tag: `git tag v1.0.0 && git push origin v1.0.0`
4. Watch workflow complete (15-25 minutes)
5. Verify release on GitHub
6. Test installation from release

### Optional Enhancements

1. **Homebrew Tap**:
   - Create repo at `github.com/hamzaplojovic/homebrew-remind`
   - Reference in installation docs

2. **HOMEBREW_GITHUB_TOKEN** (for automatic Homebrew PRs):
   - Create personal access token with `public_repo` scope
   - Add as repository secret
   - Workflow will automatically create Homebrew PR

3. **Website Integration**:
   - Update `remind.dev` with installation instructions
   - Curl script already configured to pull from GitHub releases

## Troubleshooting

### Workflow doesn't trigger

**Check**:
- Tag matches pattern: `v[0-9]+.[0-9]+.[0-9]+*` (e.g., `v1.0.0`, `v1.0.0-rc1`)
- Pushed with: `git push origin v1.0.0`
- Workflow is enabled: Settings → Actions → General

### Build fails on specific platform

**Check**:
- Python 3.12+ available
- Dependencies in `apps/cli/pyproject.toml`
- No platform-specific issues

**Debug**:
```bash
# Test locally on that platform
cd apps/cli
uv sync
uv run python build_tools/build.py
```

### Homebrew formula generation fails

**Check**:
- All three binaries in GitHub release
- SHA256SUMS file present
- Repository name correct

**Debug**:
```bash
cd apps/cli
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.0
```

## Files Reference

```
remind-monorepo/
├── .github/
│   ├── workflows/
│   │   └── release-binaries.yml          ← Main workflow (NEW)
│   └── RELEASE_CHECKLIST.md              ← QA checklist (NEW)
├── apps/cli/
│   ├── build_tools/
│   │   ├── build.py                      ← Builds binaries
│   │   ├── generate_homebrew_formula.py  ← Updated
│   │   └── homebrew_formula.rb           ← Updated
│   └── pyproject.toml                    ← Update version here
├── infrastructure/
│   └── CI_CD_GUIDE.md                    ← CI/CD overview (NEW)
├── RELEASE.md                            ← Release guide (NEW)
└── INSTALLATION.md                       ← Updated
```

## Documentation Map

1. **For Users**:
   - `INSTALLATION.md` - How to install Remind
   - `RELEASE.md` → "Installation Methods" section

2. **For Releases**:
   - `RELEASE.md` - Complete release process
   - `.github/RELEASE_CHECKLIST.md` - Pre-release checklist
   - `apps/cli/build_tools/generate_homebrew_formula.py` - Formula generation

3. **For Development**:
   - `infrastructure/CI_CD_GUIDE.md` - CI/CD architecture and local testing
   - `.github/workflows/release-binaries.yml` - Workflow definition

## Success Criteria

Release automation is complete when:

- ✅ Workflow triggers on version tags
- ✅ All three binaries build successfully
- ✅ GitHub release created with binaries + SHA256SUMS
- ✅ Homebrew formula auto-generated with correct checksums
- ✅ Formula auto-committed to repository
- ✅ Users can install via: `brew install remind-cli`

## Questions?

See these documents:
- **How to create a release?** → `RELEASE.md`
- **How does CI/CD work?** → `infrastructure/CI_CD_GUIDE.md`
- **Pre-release checklist?** → `.github/RELEASE_CHECKLIST.md`
- **How to troubleshoot?** → Look in all three above + GitHub Actions logs

---

**Ready to release?** Go to `RELEASE.md` and follow the "Creating a Release" section.
