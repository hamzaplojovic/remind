# Quick Reference: Remind Release & Homebrew Setup

## One-Liner Release Command

```bash
git tag v1.0.0 && git push origin v1.0.0
```

Then watch: https://github.com/hamzaplojovic/remind/actions/workflows/release-binaries.yml

---

## What Happens When You Push a Tag

```
Your Git Push (v1.0.0)
         │
         ▼
GitHub Actions Triggered
         │
    ┌────┴────┐
    ▼    ▼    ▼
  Mac  Mac  Linux  (3 parallel builds)
  x86  arm  x64
    │    │    │
    └────┴────┘
         │
         ▼
GitHub Release Created
(with 3 binaries + SHA256SUMS)
         │
         ▼
Homebrew Formula Updated
(with correct checksums)
         │
         ▼
Done! ✓
```

---

## Installation Methods (Post-Release)

### 🏠 Homebrew (Recommended)
```bash
brew install remind-cli
```

### 🍺 Homebrew Tap (Until in homebrew-core)
```bash
brew tap hamzaplojovic/remind
brew install remind-cli
```

### 📥 Direct Download
```bash
wget https://github.com/hamzaplojovic/remind/releases/download/v1.0.0/remind-linux-x86_64
chmod +x remind-linux-x86_64
sudo mv remind-linux-x86_64 /usr/local/bin/remind
```

### 🔧 Curl Script
```bash
curl -sSL https://remind.hamzaplojovic.blog/install.sh | bash
```

---

## Documentation Map

| Document | Purpose | Read When |
|----------|---------|-----------|
| **`RELEASE.md`** | Full release guide | Creating a release |
| **`.github/RELEASE_CHECKLIST.md`** | Pre-release checklist | Before pushing tag |
| **`infrastructure/CI_CD_GUIDE.md`** | CI/CD deep-dive | Understanding workflow |
| **`INSTALLATION.md`** | Installation methods | For users |
| **`.github/workflows/release-binaries.yml`** | Workflow definition | Debugging build |
| **`HOMEBREW_SETUP_SUMMARY.md`** | Full summary | Getting started |

---

## Pre-Release Checklist (5 min)

- [ ] Update version: `apps/cli/pyproject.toml`
- [ ] Commit: `git commit -am "chore: bump version to 1.0.0"`
- [ ] Tag: `git tag v1.0.0`
- [ ] Push tag: `git push origin v1.0.0`
- [ ] Monitor: GitHub Actions tab

---

## Files Created

```
.github/
├── workflows/
│   └── release-binaries.yml       ← Main workflow
├── RELEASE_CHECKLIST.md           ← QA checklist
└── QUICK_REFERENCE.md             ← This file

apps/cli/build_tools/
├── build.py                       (no change)
├── generate_homebrew_formula.py   ← Updated
└── homebrew_formula.rb            ← Updated

infrastructure/
└── CI_CD_GUIDE.md                 ← CI/CD guide

Root/
├── RELEASE.md                     ← Release guide
├── HOMEBREW_SETUP_SUMMARY.md      ← Full summary
└── INSTALLATION.md                ← Updated
```

---

## First Release Timeline

```
T+0min   │ You: git push origin v1.0.0
         │
T+1min   │ ✓ Workflow starts
         │   - Checkout code
         │   - Set up Python 3.13
         │
T+5min   │ ✓ Three builds start in parallel
         │   - macOS x86_64 (macos-13)
         │   - macOS arm64 (macos-latest)
         │   - Linux x86_64 (ubuntu-latest)
         │
T+10min  │ ✓ Builds complete
         │   - Binaries renamed
         │   - SHA256 checksums created
         │   - Artifacts uploaded
         │
T+12min  │ ✓ GitHub Release created
         │   - 3 binaries uploaded
         │   - SHA256SUMS uploaded
         │   - Release published
         │
T+15min  │ ✓ Homebrew formula generated
         │   - Fetches checksums from release
         │   - Updates formula file
         │   - Commits and pushes
         │
T+20min  │ ✓ COMPLETE
         │   All binaries ready
         │   Formula in sync
         │   Users can install!
```

---

## Troubleshooting at a Glance

| Problem | Solution |
|---------|----------|
| Workflow doesn't trigger | Check tag format: `v1.0.0` (must match `v[0-9]+.[0-9]+.[0-9]+*`) |
| Build fails | Check Python 3.12+ installed. Review action logs. |
| Release missing binaries | All builds must pass first. Check "build" job logs. |
| SHA256 mismatch | Formula generation pulls from release. Ensure upload succeeded. |
| Can't install from Homebrew | Formula not merged yet. Use tap: `brew tap hamzaplojovic/remind` |

---

## Success Indicators

✓ Release created on GitHub
✓ All 3 binaries present
✓ SHA256SUMS file included
✓ Homebrew formula updated
✓ Formula committed to repo
✓ Users can `brew install remind-cli` (once in homebrew-core)

---

## Key Commands

```bash
# Create release
git tag v1.0.0
git push origin v1.0.0

# Test binary locally
cd apps/cli
uv sync --extra build
uv run python build_tools/build.py
./dist/remind --version

# Generate formula manually
uv run python build_tools/generate_homebrew_formula.py hamzaplojovic/remind v1.0.0

# Test Homebrew installation
brew install --build-from-source ./apps/cli/build_tools/homebrew_formula.rb

# Delete tag if something goes wrong
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

---

## Next Step

👉 Read: [`RELEASE.md`](../RELEASE.md)

Or jump straight to: [`RELEASE_CHECKLIST.md`](.github/RELEASE_CHECKLIST.md)

---

## Need More Details?

- **Full release walkthrough** → `RELEASE.md`
- **Pre-release checklist** → `.github/RELEASE_CHECKLIST.md`
- **CI/CD architecture** → `infrastructure/CI_CD_GUIDE.md`
- **Workflow definition** → `.github/workflows/release-binaries.yml`
- **Installation guide** → `INSTALLATION.md`
