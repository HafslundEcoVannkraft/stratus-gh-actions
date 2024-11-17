# Version Bump and Release Action

A GitHub Action that automates version bumping, tag creation, and release generation with AI-powered release notes using Azure OpenAI. This action analyzes your commits and automatically determines the appropriate version bump based on conventional commit messages or a default bump level.

## Features

- 🔄 Automatic version bumping based on commit messages
- 🏷️ Git tag creation and management
- 📝 AI-generated release notes using Azure OpenAI
- 🔑 Support for both Azure RBAC and API key authentication
- 🎯 Configurable version bump rules
- 📋 Custom release note formatting
- 🏗️ Support for pre-release versions (alpha, beta, rc, preview)

## Version Format

This action uses semantic versioning with the following format:
- Regular releases: `vX.Y.Z` (e.g., `v1.0.0`)
- Pre-releases: `vX.Y.Z-type.N` (e.g., `v1.0.0-preview.1`)

The `v` prefix is always included in tags and version numbers for consistency and best practices.

## Initial Release

For the first release in a repository:
- The action starts from `v0.0.0` as the base version
- It includes all changes since the first commit in the release notes
- The first version will be determined based on commit messages or the `default_bump_level`
- Typically results in `v0.1.0` for new features or `v1.0.0` for initial major releases

## Location in Monorepo

```
repository-root/
├── .github/
│   ├── actions/
│   │   ├── release/        # This action
│   │   │   ├── README.md
│   │   │   └── action.yml
│   │   └── other-actions/  # Other composite actions
```

## Usage

```yaml
name: Release

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

## Version Bumping Rules

The action determines the version bump type based on the following commit message prefixes:

- **Major Version** (`vX.y.z`): Triggered by commits containing `breaking change:` or `major:`
- **Minor Version** (`vx.Y.z`): Triggered by commits containing `feat:` or `minor:`
- **Patch Version** (`vx.y.Z`): Triggered by commits containing `fix:` or `patch:`

If no commit message matches these patterns and no `default_bump_level` is set, the action will exit successfully without creating a new version. This allows you to control when versions should be bumped by either using conventional commit messages or explicitly setting a default bump level.

### Pre-release Versions

Pre-release versions can be created using the following prefixes:
- `alpha:` - Creates an alpha pre-release (e.g., `v1.2.3-alpha.1`)
- `beta:` - Creates a beta pre-release (e.g., `v1.2.3-beta.1`)
- `rc:` - Creates a release candidate (e.g., `v1.2.3-rc.1`)
- `preview:` - Creates a preview release (e.g., `v1.2.3-preview.1`)

## Inputs

### Required Inputs

| Name | Description |
|------|-------------|
| `azure_openai_endpoint` | Azure OpenAI endpoint URL (e.g., https://your-resource.openai.azure.com/) |
| `azure_openai_deployment_name` | Azure OpenAI model deployment name |

### Authentication Options

#### Option 1: Azure RBAC Authentication (Recommended)
```yaml
azure_client_id: ${{ secrets.AZURE_CLIENT_ID }}
azure_tenant_id: ${{ secrets.AZURE_TENANT_ID }}
azure_subscription_id: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
```

#### Option 2: API Key Authentication
```yaml
azure_openai_api_key: ${{ secrets.AZURE_OPENAI_API_KEY }}
```

### Optional Inputs

| Name | Description | Default |
|------|-------------|---------|
| `draft` | Set the release as a draft | `true` |
| `prerelease` | Mark the release as a pre-release | `true` |
| `azure_openai_api_version` | Azure OpenAI API version | Latest stable |
| `temperature` | Temperature for text generation (0.0-2.0) | `0.2` |
| `max_tokens` | Maximum number of tokens in the response | `4000` |
| `top_p` | Controls diversity of language model output | `1.0` |
| `frequency_penalty` | Reduces word repetition (-2.0 to 2.0) | `0.1` |
| `presence_penalty` | Influences topic diversity (-2.0 to 2.0) | `0.1` |
| `response_format` | Response format (text or json_object) | `text` |
| `seed` | Random number seed for deterministic outputs | `` |
| `release_prefix` | Prefix for release titles | `` |
| `validate_version_history` | Enable version history validation | `true` |
| `closing_note` | Standardized closing note for Release Notes | See below |
| `append_context` | Additional context for release notes generation | `` |
| `default_bump_level` | Default version bump level if no keywords found | `` |

Default closing note:
```markdown
## Closing Note
A heartfelt thank you to all contributors: $contributors.
```

## Outputs

| Name | Description |
|------|-------------|
| `version` | The new version number that was created |
| `previous_version` | The previous version used for comparison |
| `bump_level` | The type of version bump performed (major, minor, patch, or initial) |

## Examples

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

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
