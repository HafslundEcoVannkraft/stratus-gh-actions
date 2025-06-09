# Stratus GitHub Actions

Welcome to `stratus-gh-actions`! This repository hosts a collection of reusable composite GitHub Actions to streamline workflows across repositories. The repository is public, you can easily share actions with any repository, ensuring consistency and reducing duplicated code.

## Table of Contents

- [About](#about)
- [Repository Structure](#repository-structure)
- [Available Actions](#available-actions)
  - [Hello World](#hello-world-action)
  - [Simple Version Bump and Release](#simple-version-bump-and-release-action)
  - [Build Scope Analyzer](#build-scope-analyzer-action)
- [Usage](#usage)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## About

The `stratus-gh-actions` repository is designed to simplify and standardize workflows across projects by providing a central source of reusable composite GitHub Actions. Each action is defined within its own folder at the repository root, making it easy to reference them directly from any repository.

### Key Benefits

- **Reusable**: Use the same action in multiple workflows and repositories, improving consistency.
- **Public Access**: As a public repository, actions here can be used in both public and private/internal repositories.
- **Version Control**: Keep track of changes to actions across repositories, ensuring stability with tagged versions.
- **Simple and Reliable**: Actions use GitHub's native features without external dependencies.

## Repository Structure

The repository is organized with each action in its own folder at the root level:

```plaintext
stratus-gh-actions/
├── build-scope-analyzer/
│   ├── action.yml
│   ├── build_scope_analyzer.py
│   └── README.md
├── release/
│   ├── action.yml
│   └── README.md
├── hello-world/
│   ├── action.yml
│   ├── entrypoint.sh
│   └── README.md
├── .github/
│   └── workflows/
└── README.md
```

Each action has its own documentation explaining its specific usage and configuration options.

## Usage

To use an action from this repository, reference it in your workflow file with the following syntax:

```yaml
uses: HafslundEcoVannkraft/stratus-gh-actions/[action-name]@main
```

Replace:
- `[action-name]` with the specific action folder name (e.g., `release`, `hello-world`, `build-scope-analyzer`)
- `@main` with the desired version tag or branch

## Available Actions

### Hello World Action

A simple example action that demonstrates the basic structure and usage of composite actions. For more information, see the [hello-world action documentation](hello-world/README.md).

#### Example Using Hello World Action

```yaml
name: Hello World Example

on:
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - name: Say Hello
        uses: HafslundEcoVannkraft/stratus-gh-actions/hello-world@main
```

### Simple Version Bump and Release Action

A lightweight action that automates version management and release creation using GitHub's native features:

**Key Features:**
- 🔄 Automatic version bumping based on PR labels or commit messages
- 📝 Native GitHub release notes (no external dependencies)
- 🏷️ Semantic versioning support
- 🎯 Zero configuration required
- 📋 Simple and reliable

For detailed information about this action, see the [release action documentation](release/README.md).

### Build Scope Analyzer Action

An intelligent action that analyzes git changes to determine what needs to be built, generating a strategy matrix for GitHub Actions workflows. This action helps optimize CI/CD pipelines by only building what has changed.

**Key Features:**
- 🔍 Analyzes git changes to identify modified directories
- 📊 Generates GitHub Actions strategy matrix
- 🗑️ Identifies deleted folders for cleanup
- 🎯 Supports include/exclude patterns for fine-grained control

For detailed information about this action, see the [build-scope-analyzer action documentation](build-scope-analyzer/README.md).

### Basic Release Workflow Example

```yaml
name: Release

on:
  pull_request:
    types: [closed]
    branches: [ main ]

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

### Build Scope Analyzer Workflow Example

```yaml
name: Build Changed Components

on:
  pull_request:
    branches: [ main ]
  push:
    branches: [ main ]

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.scope.outputs.matrix }}
      has-changes: ${{ steps.scope.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Analyze Build Scope
        id: scope
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@main
        with:
          include-pattern: 'apps/*'
          exclude-pattern: 'apps/*/tests'
          
  build:
    needs: analyze
    if: needs.analyze.outputs.has-changes == 'true'
    strategy:
      matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build ${{ matrix.folder }}
        run: |
          echo "Building ${{ matrix.folder }}"
          # Your build commands here
```

## Contributing

Contributions are welcome! If you'd like to add an action, improve existing ones, or report an issue, please follow these guidelines:

1. **Fork the Repository**: Create a fork and make your changes.
2. **Follow Commit Conventions**: Use conventional commit messages:
   - `feat:` or `feat()` for new features
   - `fix:` or `fix()` for bug fixes
   - Include `BREAKING` in PR title for breaking changes
3. **Open a Pull Request**: Submit a PR with a clear description of your changes.
4. **Action Documentation**: Ensure each action has a `README.md` in its folder explaining its usage.

### Release Process

This repository uses an automated release process with two distinct components:

#### 1. Version Bumping (Workflow Logic)
When a Pull Request is merged to `main`, the workflow determines the version bump based on PR labels:
- **Major** (vX.0.0): PRs with `breaking-change` or `major` label
- **Minor** (v0.X.0): PRs with `enhancement`, `feature`, or `minor` label
- **Patch** (v0.0.X): All other PRs (default)

#### 2. Release Notes Categorization (`.github/release.yml`)
GitHub automatically categorizes merged PRs in release notes based on labels:
- PRs with `enhancement` or `feature` labels → 🚀 Features
- PRs with `bug` or `bugfix` labels → 🐛 Bug Fixes
- PRs with `documentation` label → 📚 Documentation
- PRs with `breaking-change` label → ⚠️ Breaking Changes
- PRs with `maintenance` or `chore` labels → 🔧 Maintenance

**Important**: The `.github/release.yml` file ONLY controls how release notes are displayed. It does NOT determine version numbers - that's handled by the workflow logic.

### Development Guidelines

- Test actions in a separate branch or fork before merging to `main`
- Use meaningful commit messages following the conventional commit format
- Each action should have README.md documentation
- Update examples in documentation to reflect any changes
- Test changes with workflows in your fork before submitting PRs

### Version Control

The repository automatically handles versioning through the release action. You don't need to manually create tags or releases. Just follow these practices:

1. Use conventional commit messages to indicate change type
2. For pre-releases, use appropriate prefixes in commit messages
3. Let the automated pipeline handle version bumping and release creation
4. Check the generated release notes and edit if necessary

## License

MIT
