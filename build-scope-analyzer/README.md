# Build Scope Analyzer

## Overview

This GitHub Action analyzes changes in a repository to determine what applications need to be built, deployed, or cleaned up in a multi-app repository. It's particularly designed for containerized applications and helps optimize CI/CD workflows by building only what has changed.

## Key Features

- **Smart Change Detection**: Analyzes Git diffs to identify changed files and folders
- **Deletion Tracking**: Detects deleted apps or containers for proper cleanup
- **Multi-Container Support**: Handles repositories with multiple apps and containers
- **Custom Docker Build Context**: Supports custom Docker build contexts via a `# @context: ...` comment in Dockerfiles
- **Specialized Outputs**: Separate matrices for container builds vs app deployments
- **Workflow Optimization**: Generates strategy matrices for parallel builds
- **Image Name Reference**: Each container output includes an `image_name` field, derived from the app config or folder name and Dockerfile suffix.
- **Explicit Container Output**: Each container output includes `context` (build context), `container_name`, and detailed Dockerfile info.

## Usage

### Basic Usage

```yaml
- name: Analyze changes
  id: analyze
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
  with:
    root-path: ${{ github.workspace }}
    include-pattern: "src/*"
```

> **Note:** If no `app.yaml` or `app.yml` is found in any folder, the `apps` list in the output will simply be empty.

## Example Matrix Structure

The output structure provides specialized outputs for different use cases:

```json
{
  "apps": {
    "updated": [ ... ],        // Changed apps with app.yaml/app.yml
    "all": [ ... ],            // All apps with app.yaml/app.yml
    "deleted": [ ... ],        // Deleted apps (previously had app.yaml/app.yml)
    "has_updates": true|false,    // Whether there are any changed apps
    "has_deletions": true|false   // Whether there are any deleted apps
  },
  "containers": {
    "updated": [ ... ],        // Changed containers (with Dockerfiles)
    "all": [ ... ],            // All containers (with Dockerfiles)
    "deleted": [ ... ],        // Deleted containers (previously had Dockerfiles)
    "has_updates": true|false,    // Whether there are any changed containers
    "has_deletions": true|false   // Whether there are any deleted containers
  },
  "ref": "origin/main"  // Git ref used for comparison
}
```

### Container Item Structure

```json
{
  "path": "apps/web-api",
  "app_name": "web-api",
  "dockerfile": {
    "path": "apps/web-api/Dockerfile",
    "name": "Dockerfile",
    "suffix": ""
  },
  "image_name": "web-api",
  "container_name": "web-api",
  "context": "apps/web-api" // Build context (may differ if custom context is set)
}
```

- `context`: The build context directory for the Docker build. If a Dockerfile contains a `# @context: ...` comment, this value will reflect the custom context.
- `container_name`: The name of the container (from app.yaml name property or folder basename if no app.yaml, suffixed with Dockerfile suffix).

### Deleted Container Structure

```json
{
  "app_name": "old-service",
  "container_name": "old-service-monitor",
  "dockerfile": "apps/old-service/Dockerfile.monitor",
  "image_name": "old-service-monitor",
  "context": "apps/old-service", // (if available)
  "commit_sha": "abc123def456789test0commit0sha0for0testing" // The commit SHA for the version with this container
}
```

### Deleted App Structure

```json
{
  "path": "apps/old-service",
  "app_name": "old-service",
  "app_config": "apps/old-service/app.yaml",
  "commit_sha": "abc123def456789test0commit0sha0for0testing" // The commit SHA for the version with this app
}
```

## Production Pipeline Example

```yaml
# This example is based on a real-world production workflow
jobs:
  analyze:
    name: Analyze Repo Changes
    runs-on: ubuntu-latest
    outputs:
      apps_updated: ${{ steps.set-matrix.outputs.apps_updated }}
      apps_deleted: ${{ steps.set-matrix.outputs.apps_deleted }}
      apps_has_deletions: ${{ steps.set-matrix.outputs.apps_has_deletions }}
      containers_updated: ${{ steps.set-matrix.outputs.containers_updated }}
      containers_deleted: ${{ steps.set-matrix.outputs.containers_deleted }}
      containers_has_deletions: ${{ steps.set-matrix.outputs.containers_has_deletions }}
      comparison_ref: ${{ steps.set-matrix.outputs.ref }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Run build-scope-analyzer
        id: analyze
        uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@v3
        with:
          root-path: ${{ github.workspace }}
          include-pattern: "src/*"

      - name: Set matrix outputs
        id: set-matrix
        run: |
          MATRIX_JSON='${{ steps.analyze.outputs.matrix }}'
          echo "apps_updated=$(echo $MATRIX_JSON | jq -c '.apps.updated')" >> $GITHUB_OUTPUT
          echo "apps_deleted=$(echo $MATRIX_JSON | jq -c '.apps.deleted')" >> $GITHUB_OUTPUT
          echo "apps_has_deletions=$(echo $MATRIX_JSON | jq -r '.apps.has_deletions')" >> $GITHUB_OUTPUT
          echo "containers_updated=$(echo $MATRIX_JSON | jq -c '.containers.updated')" >> $GITHUB_OUTPUT
          echo "containers_deleted=$(echo $MATRIX_JSON | jq -c '.containers.deleted')" >> $GITHUB_OUTPUT
          echo "containers_has_deletions=$(echo $MATRIX_JSON | jq -r '.containers.has_deletions')" >> $GITHUB_OUTPUT
          echo "ref=$(echo $MATRIX_JSON | jq -c '.ref')" >> $GITHUB_OUTPUT

  app-destroy:
    name: Destroy App (${{ matrix.app.app_name }})
    needs: [analyze]
    if: needs.analyze.outputs.apps_has_deletions == 'true'
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.apps_deleted) }}
    steps:
      - name: Destroy App
        run: |
          echo "Destroying app: ${{ matrix.app.app_name }}"
          echo "Path: ${{ matrix.app.path }}"
          echo "App config: ${{ matrix.app.app_config }}"
          echo "Commit SHA: ${{ matrix.app.commit_sha }}"
          # Destroy app logic here

  docker-cleanup:
    name: Docker Cleanup (${{ matrix.container.container_name }})
    needs: [analyze]
    if: needs.analyze.outputs.containers_has_deletions == 'true'
    strategy:
      matrix:
        container: ${{ fromJson(needs.analyze.outputs.containers_deleted) }}
      max-parallel: 50
    steps:
      - name: Delete from Container Registry
        run: |
          echo "Deleting container: ${{ matrix.container.container_name }}"
          echo "From app: ${{ matrix.container.app_name }}"
          echo "Dockerfile: ${{ matrix.container.dockerfile }}"
          echo "Commit SHA: ${{ matrix.container.commit_sha }}"
          # Container registry cleanup logic here

  container-build:
    name: Docker Build (${{ matrix.container.container_name }})
    needs: [analyze, docker-cleanup]
    if: always() && needs.analyze.outputs.containers_updated != '[]' && (needs.docker-cleanup.result == 'success' || needs.docker-cleanup.result == 'skipped')
    strategy:
      matrix:
        container: ${{ fromJson(needs.analyze.outputs.containers_updated) }}
      max-parallel: 50
    steps:
      - name: Build Container
        run: |
          echo "Building container: ${{ matrix.container.container_name }}"
          echo "For app: ${{ matrix.container.app_name }}"
          echo "Context: ${{ matrix.container.context }}"
          echo "Dockerfile: ${{ matrix.container.dockerfile.path }}"
          # docker build -f ${{ matrix.container.dockerfile.path }} -t ${{ matrix.container.container_name }} ${{ matrix.container.context }}

  app-deploy:
    name: Deploy App (${{ matrix.app.app_name }})
    needs: [analyze, app-destroy, container-build]
    if: always() && needs.analyze.outputs.apps_updated != '[]' && (needs.container-build.result == 'success' || needs.container-build.result == 'skipped') && (needs.app-destroy.result == 'success' || needs.app-destroy.result == 'skipped')
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.apps_updated) }}
      max-parallel: 50
    steps:
      - name: Deploy App
        run: |
          echo "Deploying app: ${{ matrix.app.app_name }}"
          echo "From path: ${{ matrix.app.path }}"
          echo "Using config: ${{ matrix.app.app_config }}"
          # Deployment logic here
```

## Notes

- The `image_name`, `container_name`, and `context` fields are always present for containers. `context` is derived from a `# @context: ...` comment in the Dockerfile if present, otherwise defaults to the app folder.
- Only folders with real file changes (not just renames) are included in `updated`.
- Deleted containers and apps are only included if truly deleted, not just renamed.
- For multi-container apps, each container is listed separately with its own `container_name`, `dockerfile`, and `context`.
