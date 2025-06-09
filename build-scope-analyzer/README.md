# Build Scope Analyzer

A GitHub Action that analyzes git changes to identify what needs to be built, generating a strategy matrix for efficient CI/CD pipelines.

## Features

- 🔍 **Smart Change Detection**: Analyzes git diff to identify changed folders
- 📦 **App Detection**: Finds apps by looking for `app.yaml`/`app.yml` and `Dockerfile`
- 🏷️ **Smart App Naming**: Extracts app names from configuration or uses folder names
- 🎯 **Path Filtering**: Include or exclude paths using glob patterns
- 📊 **Matrix Output**: Generates GitHub Actions strategy matrix for parallel builds
- 🗑️ **Deletion Tracking**: Identifies deleted folders for cleanup operations

## Usage

### Basic Usage

```yaml
name: Build Changed Apps

on:
  push:
    branches: [main]
  pull_request:

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

      - name: Analyze changes
        id: scope
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@main

  build:
    needs: analyze
    if: needs.analyze.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/${{ matrix.app_name }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha
      
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.path }}
          file: ${{ matrix.dockerfile }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
```

### With Path Filtering

```yaml
- name: Analyze changes
  id: scope
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@main
  with:
    include-pattern: 'apps/*'  # Only analyze apps folder
    # OR
    exclude-pattern: 'tests/*' # Exclude test folders
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `root-path` | Root path to search for changes | No | `${{ github.workspace }}` |
| `include-pattern` | Glob pattern for paths to include | No | `''` |
| `exclude-pattern` | Glob pattern for paths to exclude | No | `''` |
| `ref` | Git ref to compare against | No | Auto-detected |

## Outputs

| Output | Description | Example |
|--------|-------------|---------|
| `matrix` | JSON matrix for GitHub Actions | `{"include":[{"path":"app1","app_name":"frontend","dockerfile":"app1/Dockerfile"}]}` |
| `has-changes` | Boolean indicating if changes detected | `true` |
| `deleted-folders` | JSON array of deleted folders | `["old-app"]` |
| `ref` | Git ref used for comparison | `origin/main` |

## How It Works

1. **Git Diff Detection**: Compares current commit against:
   - Base branch for pull requests
   - Previous commit for push events

2. **App Discovery**: For each changed folder, looks for:
   - `app.yaml` or `app.yml` configuration files
   - `Dockerfile` for container builds

3. **App Name Resolution**:
   - First tries to extract from `app.yaml` (`name` field)
   - Falls back to folder name if not found

4. **Matrix Generation**: Creates a matrix entry for each app with:
   - `path`: Folder path
   - `app_name`: Resolved app name
   - `dockerfile`: Path to Dockerfile
   - `app_config`: Path to app configuration (if exists)

## Best Practices

### Separation of Concerns

This action focuses solely on **what** needs to be built, not **how** it should be tagged or deployed. Use specialized actions for:

- **Docker Tagging**: Use `docker/metadata-action` in your build job
- **Deployment**: Use deployment-specific actions with the matrix output
- **Registry Management**: Handle authentication and pushing in the build job

### Example: Complete Workflow

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main]
  pull_request:

jobs:
  # 1. Identify what changed
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.scope.outputs.matrix }}
      has-changes: ${{ steps.scope.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - id: scope
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@main

  # 2. Build changed apps
  build:
    needs: analyze
    if: needs.analyze.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      
      # Generate tags based on your strategy
      - id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}/${{ matrix.app_name }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=sha,prefix={{branch}}-
            type=raw,value=latest,enable={{is_default_branch}}
      
      # Build with your preferred method
      - uses: docker/build-push-action@v5
        with:
          context: ${{ matrix.path }}
          file: ${{ matrix.dockerfile }}
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}

  # 3. Deploy to your platform
  deploy:
    needs: [analyze, build]
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      # Use the matrix to deploy each app
      - run: echo "Deploy apps from matrix"
```

## Testing

Run the test script to see the analyzer in action:

```bash
# Set up test environment
./setup_test_env.sh

# Activate virtual environment
source venv/bin/activate

# Run tests
python test_build_scope_analyzer.py
```

## Requirements

- Python 3.x
- PyYAML
- Git repository with history

## Troubleshooting

### No changes detected
- Ensure `fetch-depth: 0` in checkout action
- Check if files match your include/exclude patterns
- Verify apps have `Dockerfile` or `app.yaml`

### Wrong comparison ref
- For PRs: Checks against base branch
- For pushes: Checks against previous commit
- Override with `ref` input if needed

### Pattern matching
- Use `*` for single directory level
- Use `**` for multiple directory levels
- Cannot use both include and exclude patterns

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

