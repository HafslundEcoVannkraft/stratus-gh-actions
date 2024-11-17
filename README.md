# Stratus GitHub Actions

Welcome to `stratus-gh-actions`! This repository hosts a collection of reusable composite GitHub Actions to streamline workflows across repositories. The repository is public, you can easily share actions with any repository, ensuring consistency and reducing duplicated code.

## Table of Contents

- [About](#about)
- [Repository Structure](#repository-structure)
- [Available Actions](#available-actions)
  - [Version Bump and Release](#version-bump-and-release)
- [Usage](#usage)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## About

The `stratus-gh-actions` repository is designed to simplify and standardize workflows across projects by providing a central source of reusable composite GitHub Actions. Each action is defined within its own folder under `.github/actions`, making it easy to reference them directly from any repository.

### Key Benefits

- **Reusable**: Use the same action in multiple workflows and repositories, improving consistency.
- **Public Access**: As a public repository, actions here can be used in both public and private/internal repositories.
- **Version Control**: Keep track of changes to actions across repositories, ensuring stability with tagged versions.
- **AI-Powered**: Utilizes Azure OpenAI for generating comprehensive release notes.

## Repository Structure

The repository is organized to support multiple actions, each defined in its own folder under `.github/actions`. Here's the current structure:

```plaintext
stratus-gh-actions/
├── .github/
│   └── actions/
│       ├── release/
│       │   ├── action.yml
│       │   └── README.md
│       ├── hello-world/
│       │   ├── action.yml
│       │   ├── entrypoint.sh
│       │   └── README.md
└── README.md
```

Each action has its own documentation explaining its specific usage and configuration options.

## Available Actions

### Version Bump and Release

A sophisticated action that automates version management and release creation with AI-powered release notes using Azure OpenAI. The action:

1. Analyzes commit messages to determine version bumps (major, minor, patch)
2. Supports pre-release versions (alpha, beta, rc, preview)
3. Generates comprehensive release notes using Azure OpenAI
4. Creates and manages Git tags
5. Publishes GitHub releases with configurable settings

**Key Features:**
- 🔄 Automatic version bumping based on commit messages
- 📝 AI-generated release notes
- 🔑 Azure RBAC and API key authentication support
- 🏷️ Pre-release version support
- 📋 Customizable release notes format

For detailed information about this action, see the [release action documentation](.github/actions/release/README.md).

### Hello World Action

A simple example action that demonstrates the basic structure and usage of composite actions. For more information, see the [hello-world action documentation](.github/actions/hello-world/README.md).

## Usage

To use an action from this repository, reference it in your workflow file with the following syntax:

```yaml
uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/[action-name]@main
```

Replace:
- `[action-name]` with the specific action folder name (e.g., `release`)
- `@main` with the desired version tag or branch

### Version Bumping Rules

The release action uses these commit message prefixes to determine version changes:
- **Major** (`vX.y.z`): `breaking change:` or `major:`
- **Minor** (`vx.Y.z`): `feat:` or `minor:`
- **Patch** (`vx.y.Z`): `fix:` or `patch:`
- **Pre-release**: `alpha:`, `beta:`, `rc:`, or `preview:`

## Examples

### Basic Release Workflow with Azure RBAC

```yaml
name: Release

on:
  push:
    branches:
      - main

jobs:
  release:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Create Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
        with:
          azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
          azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
          azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
          azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### Creating a Pre-Release

```yaml
name: Preview Release

on:
  push:
    branches:
      - develop

jobs:
  preview-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - name: Create Preview Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
        with:
          azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
          azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
          azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
          azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          prerelease: true
```

### Using Hello World Action

```yaml
name: Hello World Example

on:
  workflow_dispatch:

jobs:
  hello:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Say Hello
        uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/hello-world@main
```

## Contributing

Contributions are welcome! If you'd like to add an action, improve existing ones, or report an issue, please follow these guidelines:

1. **Fork the Repository**: Create a fork and make your changes.
2. **Follow Commit Conventions**: Use conventional commit messages to control version bumping:
   - `major:` or `breaking change:` for breaking changes (vX.0.0)
   - `feat:` or `minor:` for new features (v0.X.0)
   - `fix:` or `patch:` for bug fixes (v0.0.X)
   - `preview:`, `alpha:`, `beta:`, or `rc:` for pre-releases
3. **Open a Pull Request**: Submit a PR with a clear description of your changes.
4. **Action Documentation**: Ensure each action has a `README.md` in its folder explaining its usage.

### Release Process

This repository uses an automated release process:

1. When changes are merged to `main`, the release action automatically:
   - Analyzes commit messages to determine version bump type
   - Creates a new version tag
   - Generates AI-powered release notes
   - Creates a GitHub release

2. The version bump is determined by:
   - Commit message prefixes (major, feat, fix, etc.)
   - If no matching prefix is found and no default is set, the action exits without creating a release

3. Release notes are automatically generated using Azure OpenAI, including:
   - Summary of changes
   - New features
   - Bug fixes
   - Improvements
   - List of contributors

### Development Guidelines

- Test actions in a separate branch or fork before merging to `main`
- Use meaningful commit messages following the conventional commit format
- Each action should have comprehensive documentation
- Update examples in documentation to reflect any changes
- Test changes with workflows in your fork before submitting PRs

### Version Control

The repository automatically handles versioning through the release action. You don't need to manually create tags or releases. Just follow these practices:

1. Use conventional commit messages to indicate change type
2. For pre-releases, use appropriate prefixes in commit messages
3. Let the automated pipeline handle version bumping and release creation
4. Check the generated release notes and edit if necessary

---

**Note:** Since releases are automated, manually creating tags or releases is not necessary. The system will handle versioning based on your commit messages when changes are merged to `main`.

## License

MIT

---
