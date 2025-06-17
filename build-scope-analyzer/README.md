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
  uses: HafslundEcoVannkraft/stratus-gh-actions/build-scope-analyzer@release/v3.0.0
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
- `container_name`: The name of the container (from app config or derived from Dockerfile suffix).

### Deleted Container Structure

```json
{
  "app_name": "old-service",
  "container_name": "old-service-monitor",
  "dockerfile": "apps/old-service/Dockerfile.monitor",
  "image_name": "old-service-monitor",
  "context": "apps/old-service" // (if available)
}
```

## Pipeline Example

```yaml
jobs:
  analyze-changes:
    # ...analyzer job here...

  cleanup-apps:
    name: Clean up Deleted Apps
    needs: analyze-changes
    if: fromJson(needs.analyze-changes.outputs.matrix).apps.has_deletions == true
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze-changes.outputs.matrix).apps.deleted }}
    steps:
      - name: Remove App
        run: |
          echo "Removing app ${{ matrix.app.app_name }} from ${{ matrix.app.path }}"

  cleanup-containers:
    name: Clean up Deleted Containers
    needs: analyze-changes
    if: fromJson(needs.analyze-changes.outputs.matrix).containers.has_deletions == true
    strategy:
      matrix:
        container: ${{ fromJson(needs.analyze-changes.outputs.matrix).containers.deleted }}
    steps:
      - name: Remove Container
        run: |
          echo "Removing container ${{ matrix.container.container_name }} (image: ${{ matrix.container.image_name }})"
          echo "Dockerfile: ${{ matrix.container.dockerfile }}"
          echo "Context: ${{ matrix.container.context }}"

  build-containers:
    name: Build Updated Containers
    needs: [analyze-changes, cleanup-containers]
    if: |
      always() && (
        fromJson(needs.analyze-changes.outputs.matrix).containers.has_updates == true ||
        github.event_name == 'workflow_dispatch'
      )
    strategy:
      matrix:
        include: ${{ github.event_name == 'workflow_dispatch'
                    ? fromJson(needs.analyze-changes.outputs.matrix).containers.all
                    : fromJson(needs.analyze-changes.outputs.matrix).containers.updated }}
    steps:
      - name: Build Container
        run: |
          echo "Building container for ${{ matrix.container.app_name }}"
          echo "Image name: ${{ matrix.container.image_name }}"
          echo "Container name: ${{ matrix.container.container_name }}"
          echo "Dockerfile: ${{ matrix.container.dockerfile.path }}"
          echo "Context: ${{ matrix.container.context }}"
          # docker build -f ${{ matrix.container.dockerfile.path }} -t ${{ matrix.container.image_name }} ${{ matrix.container.context }}

  deploy-apps:
    name: Deploy Updated Apps
    needs: [analyze-changes, cleanup-apps, build-containers]
    if: |
      always() && (
        fromJson(needs.analyze-changes.outputs.matrix).apps.has_updates == true ||
        github.event_name == 'workflow_dispatch'
      )
    strategy:
      matrix:
        include: ${{ github.event_name == 'workflow_dispatch'
                    ? fromJson(needs.analyze-changes.outputs.matrix).apps.all
                    : fromJson(needs.analyze-changes.outputs.matrix).apps.updated }}
    steps:
      - name: Deploy App
        run: |
          echo "Deploying app ${{ matrix.app_name }} from ${{ matrix.path }}"
```

## Notes

- The `image_name`, `container_name`, and `context` fields are always present for containers. `context` is derived from a `# @context: ...` comment in the Dockerfile if present, otherwise defaults to the app folder.
- Only folders with real file changes (not just renames) are included in `updated`.
- Deleted containers and apps are only included if truly deleted, not just renamed.
- For multi-container apps, each container is listed separately with its own `container_name`, `dockerfile`, and `context`.
