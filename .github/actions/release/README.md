# Version Bump and Release Action

A GitHub Action that automates version bumping, tag creation, and release generation with AI-powered release notes using Azure OpenAI.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Version Format](#version-format)
- [Initial Release](#initial-release)
- [Version Bumping Rules](#version-bumping-rules)
  - [Commit Message Detection](#commit-message-detection)
  - [Branch Name Detection](#branch-name-detection)
  - [Pre-release Versions](#pre-release-versions)
- [Inputs](#inputs)
- [Outputs](#outputs)
- [Usage Examples](#examples)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features
- 🔄 Automatic version bumping based on commit messages or branch names
- 🏷️ Git tag creation and management
- 📝 AI-generated release notes using Azure OpenAI
- 🔑 Support for both Azure RBAC and API key authentication
- 🎯 Configurable version bump rules
- 📋 Custom release note formatting
- 🏗️ Support for pre-release versions (alpha, beta, rc, preview)

## Requirements
- GitHub Actions runner: Ubuntu Latest
- Repository permissions: `contents: write`, `pull-requests: write` (if commenting on PRs)
- Azure OpenAI: Example with GPT-4o model deployment (for release notes generation)
- Git: Fetch depth 0 for full history (`fetch-depth: 0` in checkout action)

## Version Format
This action uses semantic versioning with the following format:
- Regular releases: `vX.Y.Z` (e.g., `v1.0.0`)
- Pre-releases: `vX.Y.Z-type.N` (e.g., `v1.0.0-preview.1`)

The `v` prefix is always included in tags and version numbers for consistency.

## Initial Release
For the first release in a repository:
- Base version: `v0.0.0`
- Includes all changes since first commit
- Version determined by commit messages, branch name or input `default_bump_level`
- Typically results in `v0.1.0` (features) or `v1.0.0` (major release)

## Version Bumping Rules

### Commit Message Detection
- **Major Version** (`vX.y.z`): `breaking change:` or `major:`
- **Minor Version** (`vx.Y.z`): `feat:` or `minor:`
- **Patch Version** (`vx.y.Z`): `fix:` or `patch:`

### Branch Name Detection
If no commit message keywords are found, checks branch name:
- **Major**: `major/*`
- **Minor**: `feat/*` or `minor/*`
- **Patch**: `fix/*` or `patch/*`

### Pre-release Versions
Create pre-releases with these prefixes:
- `alpha:` → `v1.2.3-alpha.1`
- `beta:` → `v1.2.3-beta.1`
- `rc:` → `v1.2.3-rc.1`
- `preview:` → `v1.2.3-preview.1`

## Examples

### Tag-Only Creation
```yaml
- name: Create Version Tag
  uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
  with:
    create_release: false # Only creates semantic version tag
    default_bump_level: 'minor'
```

### Release Without AI Notes
```yaml
- name: Create Basic Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
  with:
    create_release_notes: false # Creates release without AI-generated notes
    default_bump_level: 'patch'
```

### Basic Usage with Azure RBAC
```yaml
- name: Create Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
  with:
    azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
    azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
    azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
    azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

### First Release with Major Version
```yaml
name: Initial Release

on:
  push:
    branches:
      - main

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Important: Full history needed for first release
          
      - name: Create Initial Release
        uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
        with:
          azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
          azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
          azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
          azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
          azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
          default_bump_level: 'major'  # Creates v1.0.0 as first version
```

### Using API Key Authentication
```yaml
- name: Create Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
  with:
    azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
    azure_openai_api_key: ${{ secrets.AZURE_OPENAI_API_KEY }}
```

### Creating a Preview Release
```yaml
# Commit message should include "preview:" prefix
# e.g., "preview: new feature implementation"
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

### Custom Configuration
```yaml
- name: Create Release
  uses: HafslundEcoVannkraft/stratus-gh-actions/.github/actions/release@main
  with:
    azure_openai_endpoint: ${{ secrets.AZURE_OPENAI_ENDPOINT }}
    azure_openai_deployment_name: ${{ secrets.AZURE_OPENAI_DEPLOYMENT_NAME }}
    azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
    azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
    azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
    draft: false
    prerelease: false
    temperature: 0.5
    max_tokens: 2000
    default_bump_level: 'minor'
    release_prefix: 'Release'
    closing_note: |
      ## Thank You
      Special thanks to our amazing contributors: $contributors
      
      For more information, please visit our [documentation](https://docs.example.com).
```

## Troubleshooting

### Common Issues

#### Missing or Invalid Azure OpenAI Configuration
```
Error: azure_openai_endpoint is required
```
- Verify Azure OpenAI environment variables are set
- Check endpoint URL format (must start with https://)
- Validate API version compatibility

#### Version History Issues
```
Error: Failed to get latest tag
```
- Ensure `fetch-depth: 0` in checkout action
- Verify git tags exist and are accessible
- Check repository permissions

#### Authentication Failures
```
Error: Failed to get Azure token
```
- Verify Azure RBAC role assignments
- Check client ID, tenant ID, and subscription ID and service principals oidc configuration
- Confirm API key if using key authentication

#### Release Creation Failed
```
Error: Failed to create release
```
- Check GitHub token permissions
- Verify tag doesn't already exist
- Ensure release notes were generated successfully

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

