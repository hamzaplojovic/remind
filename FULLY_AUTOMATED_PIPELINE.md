# Fully Automated Homebrew Release Pipeline

Complete end-to-end automation: **One command triggers everything.**

## The Pipeline

```
You: git push origin v1.0.0
        │
        ▼
┌─────────────────────────────────────┐
│  release-binaries.yml               │ ← Main workflow
├─────────────────────────────────────┤
│                                     │
│  Builds 3 platforms in parallel:   │
│  • macOS x86_64                     │
│  • macOS arm64                      │
│  • Linux x86_64                     │
│                                     │
│  Creates GitHub release with:       │
│  • All binaries                     │
│  • SHA256SUMS file                  │
│                                     │
│  Updates Homebrew formula:          │
│  • Fetches checksums from release   │
│  • Updates version                  │
│  • Commits & pushes                 │
└────┬──────────────────────────────┬─┘
     │                              │
     ▼                              ▼
┌──────────────────────┐    ┌──────────────────────┐
│ sync-homebrew-tap.yml│    │submit-homebrew-core│
├──────────────────────┤    ├──────────────────────┤
│                      │    │                      │
│ Syncs formula to:    │    │ Creates PR to:       │
│ hamzaplojovic/       │    │ Homebrew/homebrew-  │
│ homebrew-remind      │    │ core (stable only)   │
│                      │    │                      │
│ Enables immediate:   │    │ Automatic:           │
│ brew tap ...         │    │ • Formula validation │
│ brew install ...     │    │ • Test results       │
│                      │    │ • Platform detection │
│                      │    │ • PR creation        │
└──────────────────────┘    └──────────────────────┘
     │                              │
     └──────────────┬───────────────┘
                    │
                    ▼
         ✅ COMPLETE & LIVE

Users can immediately:
  1. brew tap hamzaplojovic/remind
  2. brew install remind-cli

Later (after review):
  3. brew install remind-cli (from homebrew-core)
```

## What Gets Automated

### ✅ Build Stage
- Compile binaries for 3 platforms
- Generate SHA256 checksums
- Verify integrity
- Create GitHub release

### ✅ Validation Stage
- Verify each binary
- Check SHA256 checksums
- Test execution
- Validate formula syntax
- Check binary format

### ✅ Homebrew Tap Stage
- Auto-sync to community tap
- Keep formula in sync
- Enable immediate installation
- Users can use: `brew tap hamzaplojovic/remind`

### ✅ Homebrew Core Stage
- Auto-submit to homebrew-core
- Create PR with validation results
- Include platform detection
- Add installation instructions
- Wait for maintainer review

## Setup Required

### Minimal Setup (Just release-binaries.yml)

Works immediately:
```bash
git push origin v1.0.0
```

Automatically creates:
- GitHub release ✅
- Updated formula ✅

### Recommended Setup (All workflows)

Add these secrets to your repository:

1. **`HOMEBREW_TAP_TOKEN`** (optional but recommended)
   - For auto-syncing to `hamzaplojovic/homebrew-remind` tap
   - Create: GitHub Settings → Developer settings → Personal access tokens
   - Scope: `repo` (full control of private repositories)
   - Without this: Manual tap updates required

2. **`HOMEBREW_GITHUB_TOKEN`** (optional)
   - For auto-creating PRs to homebrew-core
   - Scope: `public_repo`
   - Without this: homebrew-core submission is skipped

### Quick Setup (1 minute)

```bash
# 1. Create Personal Access Token:
# https://github.com/settings/tokens/new
# - Name: "HOMEBREW_TAP_TOKEN"
# - Scopes: repo (full control)
# - Copy the token

# 2. Add to repository secrets:
# https://github.com/hamzaplojovic/remind/settings/secrets/actions
# Click "New repository secret"
# Name: HOMEBREW_TAP_TOKEN
# Value: (paste the token)

# 3. Done! Everything is automated now
```

## First Time Setup

### Create Homebrew Tap Repository (One-time)

```bash
# 1. Create new repo at GitHub
# https://github.com/new
# Name: homebrew-remind
# Description: Homebrew tap for Remind CLI
# Public: Yes

# 2. Initialize locally
git clone https://github.com/YOUR_USERNAME/homebrew-remind.git
cd homebrew-remind

# 3. Create Formula directory and initial formula
mkdir -p Formula
cp ../remind/apps/cli/build_tools/homebrew_formula.rb Formula/remind-cli.rb

# 4. Push initial formula
git add Formula/
git commit -m "Initial formula"
git push origin main
```

That's it! Subsequent releases will auto-sync.

## Using It

### Release v1.0.0

```bash
# 1. Update version in apps/cli/pyproject.toml
# 2. Commit
git commit -am "chore: bump version to 1.0.0"

# 3. Tag and push (THIS TRIGGERS EVERYTHING)
git tag v1.0.0
git push origin v1.0.0

# 4. Watch the magic happen! ✨
# GitHub Actions performs:
# ✓ Builds binaries (5-10 min per platform)
# ✓ Creates GitHub release (1 min)
# ✓ Updates & commits formula (2 min)
# ✓ Syncs to tap repository (2 min)
# ✓ Submits to homebrew-core (1 min)
```

### Monitor Progress

```
https://github.com/hamzaplojovic/remind/actions
```

Watch these workflows complete in order:
1. `release-binaries` (builds + releases) - 15-25 min
2. `sync-homebrew-tap` (automatically starts after) - 2-5 min
3. `submit-to-homebrew-core` (automatically starts after) - 2-5 min

## Installation After Release

### Immediate (Works in 5 minutes)
```bash
brew tap hamzaplojovic/remind
brew install remind-cli
remind --version
```

### After Homebrew Core Approval (1-7 days)
```bash
brew install remind-cli
```

## What Happens Behind the Scenes

### Release-Binaries Workflow

**Triggered by**: Pushing tag matching `v[0-9]+.[0-9]+.[0-9]+*`

**Jobs**:
1. `build` (3 parallel jobs)
   - Download dependencies
   - Run PyInstaller
   - Generate SHA256 checksum
   - Upload artifacts

2. `create-release`
   - Download all artifacts
   - Organize files
   - Create GitHub release
   - Upload binaries + checksums

3. `update-homebrew-formula`
   - Fetch checksums from release
   - Generate formula
   - Commit & push to main repo

### Sync-Homebrew-Tap Workflow

**Triggered by**: `release-binaries` completing successfully

**Actions**:
- Checkout `hamzaplojovic/homebrew-remind` tap
- Copy updated formula
- Commit & push to tap
- Users can immediately install via tap

### Submit-to-Homebrew-Core Workflow

**Triggered by**: `release-binaries` completing successfully

**Actions** (only for stable releases, not pre-releases):
1. Validate it's a stable release (v1.0.0, not v1.0.0-rc1)
2. Create PR to Homebrew/homebrew-core
3. Include validation results
4. Add platform detection info
5. Include installation instructions

**Homebrew maintainers then**:
- Review the PR
- Run their tests
- Merge if approved

## Troubleshooting

### Workflow doesn't trigger

**Check**:
- Tag format: Must be `v1.0.0` (matches `v[0-9]+.[0-9]+.[0-9]+*`)
- Not `v1.0.0-rc1` or other pre-release formats
- Push command: `git push origin v1.0.0`

**Solution**:
```bash
git tag -d v1.0.0  # Delete local tag
git push origin :refs/tags/v1.0.0  # Delete remote tag
git tag v1.0.0  # Recreate
git push origin v1.0.0  # Push
```

### Tap sync fails

**Check**:
- `HOMEBREW_TAP_TOKEN` secret is set
- Token has `repo` scope
- Token hasn't expired

**Without token**:
- Workflow logs warning
- Manual sync required:
  ```bash
  git clone https://github.com/YOUR_USERNAME/homebrew-remind.git
  cp apps/cli/build_tools/homebrew_formula.rb homebrew-remind/Formula/remind-cli.rb
  cd homebrew-remind && git push
  ```

### Homebrew core submission fails

**Common issues**:
- Pre-release tag (use stable versions only)
- Formula syntax errors (checked by automation)
- Binary not accessible (verified by automation)

**Solution**:
- Fix any formula errors
- Delete tag and recreate stable release

## Files Involved

```
.github/workflows/
├── release-binaries.yml          ← Main workflow
├── sync-homebrew-tap.yml         ← Auto-sync tap
├── submit-to-homebrew-core.yml   ← Auto-submit homebrew
└── validate-formula.yml          ← Validation checks

apps/cli/build_tools/
├── build.py                      ← Binary builder
├── generate_homebrew_formula.py  ← Formula generator
└── homebrew_formula.rb           ← Formula template
```

## Secrets Configuration

### In GitHub Repository

**Settings → Secrets and variables → Actions**

Required for full automation:
```
HOMEBREW_TAP_TOKEN = (personal access token with repo scope)
```

Optional (for PR creation):
```
HOMEBREW_GITHUB_TOKEN = (personal access token with public_repo scope)
```

Without tokens:
- `release-binaries` works fully
- `sync-homebrew-tap` requires manual setup
- `submit-homebrew-core` is skipped

## Performance

| Stage | Duration | Parallel |
|-------|----------|----------|
| Build macOS x86_64 | 5-10 min | ✅ Yes |
| Build macOS arm64 | 5-10 min | ✅ Yes |
| Build Linux x86_64 | 5-10 min | ✅ Yes |
| Create Release | 1 min | After build |
| Update Formula | 2 min | After release |
| Sync Tap | 2-5 min | After formula |
| Submit Core | 1-2 min | After formula |
| **Total** | **15-30 min** | Parallel builds |

## Success Checklist

After pushing a tag, verify:

- [ ] **Builds complete** (15-25 min)
  - https://github.com/hamzaplojovic/remind/actions
  - All 3 platform builds succeed

- [ ] **GitHub release created**
  - 3 binaries present
  - SHA256SUMS file present
  - Release notes generated

- [ ] **Formula updated**
  - Check: `apps/cli/build_tools/homebrew_formula.rb`
  - Verify: Correct version, checksums, URLs

- [ ] **Tap synced** (if HOMEBREW_TAP_TOKEN set)
  - Formula pushed to `hamzaplojovic/homebrew-remind`
  - Users can `brew tap hamzaplojovic/remind`

- [ ] **Homebrew PR created** (if stable release)
  - PR on `Homebrew/homebrew-core`
  - Awaiting maintainer review

## Testing Before First Release

### Dry Run

```bash
# Create pre-release tag to test automation
git tag v1.0.0-rc1
git push origin v1.0.0-rc1

# Monitor: https://github.com/hamzaplojovic/remind/actions
# (homebrew-core submit will be skipped since it's pre-release)

# Delete tag after testing
git tag -d v1.0.0-rc1
git push origin :refs/tags/v1.0.0-rc1
```

### Local Testing

```bash
# Test that workflows syntax is valid
cd .github/workflows
for f in *.yml; do
  echo "Validating $f..."
  # GitHub validates automatically, but you can use:
  # actionlint $f (if installed)
done

# Test formula generation locally
cd apps/cli
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.0-test
```

## Next Release

Future releases are even simpler:

```bash
# Update version
vim apps/cli/pyproject.toml

# Commit and tag
git commit -am "chore: bump to 1.1.0"
git tag v1.1.0
git push origin v1.1.0

# Everything happens automatically! ✨
```

## Questions?

- **How do I create a release?** → This document
- **What if something fails?** → Check GitHub Actions logs
- **Can I use without tokens?** → Yes, partially (just use release-binaries)
- **How long does it take?** → 15-30 minutes total
- **Is it really automatic?** → Yes! Just push the tag

---

**Status**: ✅ Fully Automated | Ready for Production Hunt Launch 🚀
