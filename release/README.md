# Simple Version Bump and Release Action

A lightweight GitHub Action that automates version bumping, tag creation, and release generation using GitHub's native release notes.

## Features

- 🔄 Automatic version bumping based on PR labels or commit messages
- 🏷️ Git tag creation and management
- 📝 Native GitHub release notes generation (no external dependencies)
- 🎯 Simple and reliable
- 📋 Zero configuration required

## How It Works

1. **For Pull Requests**: Reads PR labels to determine version bump
2. **For Push Events**: Parses commit messages for version keywords
3. Creates a new semantic version tag
4. Generates a GitHub release with native release notes

## Version Bumping Rules

### PR Labels (Priority)
- `breaking-change` or `major` → Major version (vX.0.0)
- `enhancement`, `feature`, or `minor` → Minor version (v0.X.0)
- Any other labels or no labels → Patch version (v0.0.X)

### Commit Messages (Fallback)
- `breaking change:` or `major:` → Major version
- `feat:` or `minor:` → Minor version
- `fix:` or `patch:` → Patch version
- Default → Patch version

## Usage

### Basic Usage

```yaml
name: Release

on:
  push:
    branches: [main]
  pull_request:
    types: [closed]
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release:
    if: github.event_name == 'push' || github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Create Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/release@main
```

### With Options

```yaml
- name: Create Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/release@main
  with:
    draft: false      # Create as published release (default: false)
    prerelease: true  # Mark as pre-release
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `draft` | Create release as draft | No | `false` |
| `prerelease` | Mark as pre-release | No | `false` |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `new_version` | Generated semantic version | `v1.2.3` |
| `previous_version` | Previous version | `v1.2.2` |
| `bump_type` | Version increment type | `major`, `minor`, or `patch` |
| `release_url` | URL of created release | `https://github.com/owner/repo/releases/tag/v1.2.3` |

## Examples

### Release on Merge to Main

```yaml
name: Release on Merge

on:
  pull_request:
    types: [closed]
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  release:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Create Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/release@main
```

### Release on Direct Push

```yaml
name: Release on Push

on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Create Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/release@main
```

### Draft Release for Review

```yaml
- name: Create Draft Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/release@main
  with:
    draft: true
```

## Release Notes

This action uses GitHub's native release notes generation, which:
- Automatically categorizes PRs based on labels
- Lists contributors
- Provides a full changelog
- Can be configured via `.github/release.yml`

To customize release notes categories, create `.github/release.yml`:

```yaml
changelog:
  categories:
    - title: 🚀 Features
      labels:
        - enhancement
        - feature
    - title: 🐛 Bug Fixes
      labels:
        - bug
        - bugfix
```

## Migration from v1

The v2 release removes all AI-powered features and external dependencies:

**Removed:**
- Azure OpenAI integration
- AI-generated release notes
- Complex configuration options
- External API dependencies

**What stays the same:**
- Version bumping logic
- Tag creation
- Basic release creation

**What's new:**
- Uses GitHub's native release notes
- Zero configuration required
- More reliable and faster
- No API costs

## Why Use This Action?

- **Simple**: No complex configuration or external dependencies
- **Reliable**: Uses only GitHub's native features
- **Fast**: No external API calls
- **Free**: No costs for AI or external services
- **Maintainable**: Minimal code, easy to understand

## License

MIT

