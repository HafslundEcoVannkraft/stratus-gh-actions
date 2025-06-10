# Build Scope Analyzer

A GitHub Action that analyzes git changes to identify what needs to be built and generates a strategy matrix for GitHub Actions workflows.

## Features

- Detects changed folders based on git diff
- Finds all Dockerfiles in changed folders
- Optionally requires app.yaml/app.yml for Container Apps
- Generates GitHub Actions matrix for parallel builds
- Supports include/exclude patterns

## Usage

### For Generic Docker Builds

Use this mode when you want to build any Dockerfile found in changed folders:

```yaml
- name: Analyze changes
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
  with:
    include-pattern: 'services/*'
```

This will find all folders under `services/` that have changes and contain Dockerfiles.

### For Azure Container Apps

Use this mode when building for Container Apps that require app.yaml configuration:

```yaml
- name: Analyze changes
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
  with:
    include-pattern: 'apps/*'
    require-app-config: true
```

With `require-app-config: true`, the analyzer will include folders that have:
- Dockerfiles to build, OR
- app.yaml/app.yml with pre-built images only

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `root-path` | Root path to search for changes | No | `${{ github.workspace }}` |
| `include-pattern` | Glob pattern for paths to include (e.g., `apps/*`) | No | `''` |
| `exclude-pattern` | Glob pattern for paths to exclude (e.g., `tests/*`) | No | `''` |
| `ref` | Git ref to compare against | No | Auto-detected |
| `require-app-config` | Require app.yaml/app.yml files | No | `false` |

## Outputs

| Output | Description |
|--------|-------------|
| `matrix` | JSON matrix for GitHub Actions strategy |
| `deleted-folders` | JSON array of folders that were deleted |
| `ref` | Git ref used for comparison |
| `has-changes` | Boolean indicating if any changes were detected |

## Matrix Output Format

The matrix output includes an array of apps with their Dockerfiles:

```json
{
  "include": [
    {
      "path": "services/api",
      "app_name": "api",
      "app_config": "services/api/app.yaml",  // May be null
      "dockerfiles": [
        {
          "path": "services/api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        },
        {
          "path": "services/api/Dockerfile.sidecar",
          "name": "Dockerfile.sidecar",
          "suffix": "sidecar"
        }
      ]
    }
  ]
}
```

## Example Workflows

### Simple Docker Build

```yaml
name: Build Docker Images

on:
  push:
    branches: [main]
  pull_request:

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
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
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
      
      - name: Build images
        run: |
          for dockerfile in $(echo '${{ toJson(matrix.dockerfiles) }}' | jq -r '.[].path'); do
            docker build -f "$dockerfile" -t "myimage:latest" .
          done
```

### Container Apps Deployment

```yaml
name: Deploy Container Apps

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
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
        with:
          include-pattern: 'apps/*'
          require-app-config: true

  deploy:
    needs: analyze
    if: needs.analyze.outputs.has-changes == 'true'
    runs-on: ubuntu-latest
    strategy:
      matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
    steps:
      - uses: actions/checkout@v4
      
      - name: Build and deploy
        run: |
          # Build only if Dockerfiles exist
          if [ $(echo '${{ toJson(matrix.dockerfiles) }}' | jq '. | length') -gt 0 ]; then
            echo "Building Docker images..."
            # Build logic here
          fi
          
          # Deploy using app.yaml
          if [ -n "${{ matrix.app_config }}" ]; then
            echo "Deploying with ${{ matrix.app_config }}"
            # Deploy logic here
          fi
```

## Behavior by Mode

### Default Mode (`require-app-config: false`)
- Includes any folder with Dockerfiles
- app.yaml is optional
- Best for generic Docker workflows

### Container Apps Mode (`require-app-config: true`)
- Includes folders with Dockerfiles
- Includes folders with app.yaml/app.yml (even without Dockerfiles)
- Best for Azure Container Apps workflows

## Git Comparison Logic

- **Pull Requests**: Compares against the base branch
- **Push Events**: Compares against the previous commit
- **Manual Ref**: Use the `ref` input to specify a custom comparison point

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

