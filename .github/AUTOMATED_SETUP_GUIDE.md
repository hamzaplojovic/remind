# ⚡ 5-Minute Automated Setup Guide

Complete end-to-end Homebrew automation in 5 minutes.

## What You Get

```
You: git push origin v1.0.0
  ↓
Automatic:
  ✓ Build binaries (3 platforms)
  ✓ Create GitHub release
  ✓ Update Homebrew formula
  ✓ Sync to community tap
  ✓ Submit to homebrew-core
  ↓
Users can: brew install remind-cli
```

## Step 1: Create Homebrew Tap (1 min)

Go to: https://github.com/new

Fill in:
- **Repository name**: `homebrew-remind`
- **Description**: Homebrew tap for Remind CLI
- **Visibility**: Public

Click "Create repository"

## Step 2: Initialize Tap (2 min)

```bash
# Clone your new tap repo
git clone https://github.com/YOUR_USERNAME/homebrew-remind.git
cd homebrew-remind

# Copy the formula
mkdir -p Formula
cp ../remind/apps/cli/build_tools/homebrew_formula.rb Formula/remind-cli.rb

# Push it
git add Formula/
git commit -m "Initial formula"
git push origin main
```

## Step 3: Add GitHub Secrets (2 min)

Go to: https://github.com/hamzaplojovic/remind/settings/secrets/actions

Click "New repository secret"

### Secret 1: HOMEBREW_TAP_TOKEN

1. Create token: https://github.com/settings/tokens/new
   - **Name**: HOMEBREW_TAP_TOKEN
   - **Scopes**: Check `repo`
   - Click "Generate token"
   - Copy the token (shows only once!)

2. Add to repository:
   - **Name**: HOMEBREW_TAP_TOKEN
   - **Secret**: Paste the token
   - Click "Add secret"

### Secret 2: HOMEBREW_GITHUB_TOKEN (Optional)

Same process but for homebrew-core PRs:
- **Name**: HOMEBREW_GITHUB_TOKEN
- **Scope**: Check `public_repo`

Done! ✅

## Step 4: Create First Release

```bash
# 1. Update version
vim apps/cli/pyproject.toml
# Change: version = "1.0.0"

# 2. Commit and tag
git commit -am "chore: bump to 1.0.0"
git tag v1.0.0
git push origin v1.0.0

# 3. Watch the magic! ✨
# https://github.com/hamzaplojovic/remind/actions
```

**Total time**: 15-30 minutes (mostly automated)

## What Happens Automatically

| Time | What | Where |
|------|------|-------|
| T+0 | Workflow triggered | GitHub Actions |
| T+5-10 | macOS x86_64 built | Actions logs |
| T+5-10 | macOS arm64 built | Actions logs |
| T+5-10 | Linux x86_64 built | Actions logs |
| T+15 | Release created | GitHub Releases |
| T+17 | Formula updated | Main repo |
| T+20 | Synced to tap | hamzaplojovic/homebrew-remind |
| T+22 | PR to homebrew-core | Homebrew/homebrew-core |
| T+30 | ✅ Complete | Users can install! |

## Immediate Installation (After Release)

```bash
# Works immediately (5 min after push)
brew tap hamzaplojovic/remind
brew install remind-cli

# Works after Homebrew approval (1-7 days)
brew install remind-cli
```

## Future Releases

```bash
# Update version
vim apps/cli/pyproject.toml

# Commit and push tag
git commit -am "chore: bump to 1.1.0"
git tag v1.1.0
git push origin v1.1.0

# Done! Everything else is automatic ✨
```

## Verify Everything Works

After your first release, check:

- [ ] GitHub Actions page shows green checkmarks
- [ ] Release on GitHub has 3 binaries + SHA256SUMS
- [ ] `hamzaplojovic/homebrew-remind` repo has updated formula
- [ ] PR on `Homebrew/homebrew-core` exists (if stable release)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Workflow doesn't start | Check tag format: must be `v1.0.0` (not `1.0.0` or `v1.0.0-rc1`) |
| Tap sync fails | Check `HOMEBREW_TAP_TOKEN` secret exists and is valid |
| No PR to homebrew-core | Check if it's a stable release (not pre-release) |
| Can't install with tap | Run: `brew tap hamzaplojovic/remind` first |

## Support

- **Full automation docs**: [`FULLY_AUTOMATED_PIPELINE.md`](../FULLY_AUTOMATED_PIPELINE.md)
- **Release guide**: [`RELEASE.md`](../RELEASE.md)
- **Release checklist**: [`RELEASE_CHECKLIST.md`](RELEASE_CHECKLIST.md)
- **CI/CD details**: [`../infrastructure/CI_CD_GUIDE.md`](../infrastructure/CI_CD_GUIDE.md)

## Success Example

```
$ git tag v1.0.0 && git push origin v1.0.0

# ... wait 15-30 minutes ...

$ brew tap hamzaplojovic/remind
$ brew install remind-cli
$ remind --version
remind v1.0.0

✅ Done!
```

---

**You're all set!** 🚀

**Next step**: Push your first tag: `git tag v1.0.0 && git push origin v1.0.0`
