# Build Scope Analyzer v3.0.0

A GitHub Action that analyzes git changes to identify what needs to be built and generates a strategy matrix for GitHub Actions workflows. Version 3.0.0 introduces multi-container support and enhanced deletion tracking.

## Features

- **Multi-Container Support**: Detects all `Dockerfile*` files in each app folder
- **Enhanced Deletion Tracking**: Categorizes deletions for targeted cleanup operations
- **Workflow Dispatch Support**: Provides `all_apps` output for building everything
- **Container Apps Mode**: Supports apps with only pre-built images
- **Smart Git Handling**: Safe handling of workflow_dispatch events
- **Include/Exclude Patterns**: Fine-grained control over what to analyze

## What's New in v3.0.0

### 🐳 Multi-Container Support
- Automatically finds all Dockerfiles: `Dockerfile`, `Dockerfile.sidecar`, `Dockerfile.auth`, etc.
- Provides suffix information for container naming conventions
- Supports modern microservices architectures with sidecar patterns

### 🗑️ Enhanced Deletion Tracking
Two categories of deletions for precise cleanup:

| Deletion Type | Description | Use Case |
|--------------|-------------|----------|
| `deleted_apps` | app.yaml was deleted or entire folder removed | Terraform destroy needed |
| `deleted_containers` | Individual Dockerfile deleted or all containers in deleted folder | ACR image cleanup |

When an entire folder is deleted, the analyzer automatically populates both `deleted_apps` and `deleted_containers` to ensure proper cleanup.

### 🚀 Workflow Dispatch Support
- New `all_apps` output lists all apps regardless of changes
- Perfect for manual deployments via workflow_dispatch
- No git comparison needed, avoiding potential errors

## Usage

### Basic Usage

```yaml
- name: Analyze changes
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3.0.0
  with:
    include-pattern: 'apps/*'
```

### Container Apps Mode

```yaml
- name: Analyze changes
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3.0.0
  with:
    include-pattern: 'apps/*'
    require-app-config: true  # Include apps with only pre-built images
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `root-path` | Root path to search for changes | No | `${{ github.workspace }}` |
| `include-pattern` | Glob pattern for paths to include (e.g., `apps/*`) | No | `''` |
| `exclude-pattern` | Glob pattern for paths to exclude (e.g., `tests/*`) | No | `''` |
| `ref` | Git ref to compare against | No | Auto-detected |
| `require-app-config` | Require app.yaml/app.yml files (Container Apps mode) | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `matrix` | JSON matrix of changed apps for GitHub Actions strategy |
| `all_apps` | JSON matrix of all apps (for workflow_dispatch) |
| `has_changes` | Boolean indicating if any changes were detected |
| `has_deletions` | Boolean indicating if any deletions were detected |
| `deleted_apps` | JSON array of apps where app.yaml was deleted or folder was removed |
| `deleted_containers` | JSON array of deleted container images |
| `ref` | Git ref used for comparison |

## Output Formats

### Matrix Output (Changed Apps)

```json
{
  "include": [
    {
      "path": "apps/web-app",
      "app_name": "web-app",
      "app_config": "apps/web-app/app.yaml",
      "dockerfiles": [
        {
          "path": "apps/web-app/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        },
        {
          "path": "apps/web-app/Dockerfile.sidecar",
          "name": "Dockerfile.sidecar",
          "suffix": "sidecar"
        }
      ]
    }
  ]
}
```

### Deletion Outputs

```json
{
  "deleted_apps": [
    {
      "path": "apps/old-service",
      "app_name": "old-service",
      "deleted_config": "apps/old-service/app.yaml"
    },
    {
      "path": "apps/deprecated-service",
      "app_name": "deprecated-service",
      "deleted_config": "folder_deleted"
    }
  ],
  "deleted_containers": [
    {
      "app_name": "web-app",
      "container_name": "web-app-cache",
      "dockerfile": "apps/web-app/Dockerfile.cache",
      "image_name": "web-app-cache"
    },
    {
      "app_name": "deprecated-service",
      "container_name": "deprecated-service",
      "dockerfile": "apps/deprecated-service/Dockerfile",
      "image_name": "deprecated-service"
    }
  ]
}
```

## Example Workflows

### Multi-Container Build with Cleanup

```yaml
name: Build and Deploy

on:
  push:
    branches: [main]
  pull_request:
  workflow_dispatch:

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.final.outputs.matrix }}
      has_changes: ${{ steps.final.outputs.has_changes }}
      has_deletions: ${{ steps.analyze.outputs.has_deletions }}
      deleted_apps: ${{ steps.analyze.outputs.deleted_apps }}
      deleted_containers: ${{ steps.analyze.outputs.deleted_containers }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - id: analyze
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3.0.0
        with:
          include-pattern: 'apps/*'
          require-app-config: true
      
      - id: final
        run: |
          # Use all_apps for workflow_dispatch, matrix for other events
          if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
            echo "matrix=${{ steps.analyze.outputs.all_apps }}" >> $GITHUB_OUTPUT
            echo "has_changes=true" >> $GITHUB_OUTPUT
          else
            echo "matrix=${{ steps.analyze.outputs.matrix }}" >> $GITHUB_OUTPUT
            echo "has_changes=${{ steps.analyze.outputs.has_changes }}" >> $GITHUB_OUTPUT
          fi

  build:
    needs: analyze
    if: needs.analyze.outputs.has_changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        include: ${{ fromJson(needs.analyze.outputs.matrix).include }}
        dockerfile: ${{ matrix.dockerfiles }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Build container
        if: matrix.dockerfile != null
        run: |
          # Container name based on suffix
          if [[ -z "${{ matrix.dockerfile.suffix }}" ]]; then
            CONTAINER_NAME="${{ matrix.app_name }}"
          else
            CONTAINER_NAME="${{ matrix.app_name }}-${{ matrix.dockerfile.suffix }}"
          fi
          
          docker build -f "${{ matrix.dockerfile.path }}" \
            -t "myregistry.azurecr.io/$CONTAINER_NAME:latest" \
            "${{ matrix.path }}"

  cleanup-containers:
    needs: analyze
    if: needs.analyze.outputs.deleted_containers != '[]'
    runs-on: ubuntu-latest
    steps:
      - name: Cleanup deleted containers
        run: |
          DELETED='${{ needs.analyze.outputs.deleted_containers }}'
          for container in $(echo "$DELETED" | jq -c '.[]'); do
            IMAGE=$(echo "$container" | jq -r '.image_name')
            echo "Cleaning up container image: $IMAGE"
            # Add your ACR cleanup logic here
          done

  terraform-destroy:
    needs: analyze
    if: needs.analyze.outputs.deleted_apps != '[]'
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.deleted_apps) }}
    steps:
      - name: Destroy infrastructure
        run: |
          echo "Destroying app: ${{ matrix.app.app_name }}"
          # Add your Terraform destroy logic here
```

### Simple Docker Build

```yaml
name: Build Changed Services

on:
  push:
    branches: [main]

jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.analyze.outputs.matrix }}
      has-changes: ${{ steps.analyze.outputs.has-changes }}
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          
      - id: analyze
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3.0.0
        with:
          include-pattern: 'services/*'

  build:
    needs: analyze
    if: needs.analyze.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Build all containers for app
        run: |
          for dockerfile in $(echo '${{ toJson(matrix.dockerfiles) }}' | jq -r '.[].path'); do
            docker build -f "$dockerfile" "${{ matrix.path }}"
          done
```

## Behavior by Event Type

### Push/Pull Request Events
- Analyzes git diff to find changes
- Returns only changed apps in `matrix` output
- Provides deletion information for cleanup

### Workflow Dispatch Events
- No git comparison performed (avoids HEAD~1 issues)
- `matrix` output is empty
- Use `all_apps` output to build everything
- No deletion tracking (not applicable)

## Container Naming Convention

When building multi-container apps, use this naming pattern:

| Dockerfile Name | Container/Image Name |
|----------------|---------------------|
| `Dockerfile` | `{app-name}` |
| `Dockerfile.sidecar` | `{app-name}-sidecar` |
| `Dockerfile.auth` | `{app-name}-auth` |

## Best Practices

### 1. Always Use Full Git History
```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0  # Required for accurate git diff
```

### 2. Handle Workflow Dispatch
```yaml
# Use all_apps output for manual triggers
if [[ "${{ github.event_name }}" == "workflow_dispatch" ]]; then
  MATRIX="${{ steps.analyze.outputs.all_apps }}"
else
  MATRIX="${{ steps.analyze.outputs.matrix }}"
fi
```

### 3. Implement Cleanup Jobs
- Monitor `deleted_apps` for Terraform destroy
- Monitor `deleted_containers` for registry cleanup
- When a folder is deleted, both outputs are populated automatically

### 4. Use Matrix Strategy for Dockerfiles
```yaml
strategy:
  matrix:
    include: ${{ fromJson(needs.analyze.outputs.matrix).include }}
    dockerfile: ${{ matrix.dockerfiles }}
```

## Testing

Run the comprehensive test suite:

```bash
# Set up test environment
./setup_test_env.sh

# Activate virtual environment
source venv/bin/activate

# Run all tests
python test_build_scope_analyzer.py
```

Tests cover:
- Basic functionality
- Multi-container apps
- Pre-built only apps
- All deletion scenarios
- Workflow dispatch handling
- Include/exclude patterns

## Troubleshooting

### No changes detected
- Ensure `fetch-depth: 0` in checkout action
- Check if files match your include/exclude patterns
- For workflow_dispatch, use `all_apps` output instead

### Git command fails
- Workflow dispatch events don't perform git diff
- First commits are handled gracefully
- Force pushes won't break the analyzer

### Multi-container builds
- Each Dockerfile creates a separate matrix entry
- Use `matrix.dockerfile` to access specific Dockerfile info
- Container names follow the suffix convention

## Migration from v2

1. **Output changes**: 
   - Simplified deletion tracking: only `deleted_apps` and `deleted_containers`
   - New `all_apps` output for workflow_dispatch
   - Folder deletions now populate both deletion outputs

2. **Multi-container support**:
   - Matrix now includes dockerfile details
   - Adjust build logic to handle multiple Dockerfiles

3. **Workflow dispatch**:
   - Use `all_apps` output instead of custom logic

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

