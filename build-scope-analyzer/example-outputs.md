# Build Scope Analyzer - Example Outputs

This document shows example outputs from the build scope analyzer for various scenarios.

## Scenario 1: Simple App with Changes

**Repository structure:**

```
apps/
├── web-api/
│   ├── Dockerfile
│   ├── app.yaml
│   └── src/
└── frontend/
    ├── Dockerfile
    └── src/
```

**Changes:** Modified files in `apps/web-api/`

**Analyzer Output (New Format):**

```json
{
  "apps": {
    "updated": [
      { "path": "apps/web-api", "app_name": "web-api", "app_config": "apps/web-api/app.yaml" }
    ],
    "all": [
      { "path": "apps/web-api", "app_name": "web-api", "app_config": "apps/web-api/app.yaml" },
      { "path": "apps/frontend", "app_name": "frontend", "app_config": null }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "container_name": "web-api",
        "context": "apps/web-api",
        "dockerfile": {
          "path": "apps/web-api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "all": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "container_name": "web-api",
        "context": "apps/web-api",
        "dockerfile": {
          "path": "apps/web-api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      },
      {
        "path": "apps/frontend",
        "app_name": "frontend",
        "container_name": "frontend",
        "context": "apps/frontend",
        "dockerfile": {
          "path": "apps/frontend/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "ref": "origin/main"
}
```

**GitHub Actions Outputs:**

```
matrix={...see above...}
ref=origin/main
```

## Scenario 2: Multi-Container App

**Repository structure:**

```
apps/
└── secure-api/
    ├── Dockerfile
    ├── Dockerfile.auth
    ├── Dockerfile.logger
    ├── app.yaml
    └── src/
```

**Changes:** Added `Dockerfile.logger` to `apps/secure-api/`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "app_config": "apps/secure-api/app.yaml"
      }
    ],
    "all": [
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "app_config": "apps/secure-api/app.yaml"
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "container_name": "secure-api-logger",
        "context": "apps/secure-api",
        "dockerfile": {
          "path": "apps/secure-api/Dockerfile.logger",
          "name": "Dockerfile.logger",
          "suffix": ".logger"
        }
      }
    ],
    "all": [
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "container_name": "secure-api",
        "context": "apps/secure-api",
        "dockerfile": {
          "path": "apps/secure-api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      },
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "container_name": "secure-api-auth",
        "context": "apps/secure-api",
        "dockerfile": {
          "path": "apps/secure-api/Dockerfile.auth",
          "name": "Dockerfile.auth",
          "suffix": ".auth"
        }
      },
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "container_name": "secure-api-logger",
        "context": "apps/secure-api",
        "dockerfile": {
          "path": "apps/secure-api/Dockerfile.logger",
          "name": "Dockerfile.logger",
          "suffix": ".logger"
        }
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "ref": "HEAD~1"
}
```

## Scenario 3: Deleted Sidecar Container

**Repository structure:**

```
apps/
└── payment-service/
    ├── Dockerfile
    ├── app.yaml
    └── src/
```

**Changes:** Deleted `Dockerfile.monitor` from `apps/payment-service/`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "app_config": "apps/payment-service/app.yaml"
      }
    ],
    "all": [
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "app_config": "apps/payment-service/app.yaml"
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "container_name": "payment-service",
        "context": "apps/payment-service",
        "dockerfile": {
          "path": "apps/payment-service/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "all": [
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "container_name": "payment-service",
        "context": "apps/payment-service",
        "dockerfile": {
          "path": "apps/payment-service/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [
      {
        "app_name": "payment-service",
        "container_name": "payment-service-monitor",
        "context": "apps/payment-service",
        "dockerfile": "apps/payment-service/Dockerfile.monitor"
      }
    ],
    "has_updates": true,
    "has_deletions": true
  },
  "ref": "HEAD~1"
}
```

## Scenario 4: Deleted App (app.yaml removed)

**Repository structure:**

```
apps/
└── legacy-service/
    ├── Dockerfile
    └── src/
```

**Changes:** Deleted `app.yaml` from `apps/legacy-service/`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [],
    "all": [],
    "deleted": [
      {
        "path": "apps/legacy-service",
        "app_name": "legacy-service",
        "app_config": "apps/legacy-service/app.yaml",
        "commit_sha": "abc123def456789test0commit0sha0for0testing"
      }
    ],
    "has_updates": false,
    "has_deletions": true
  },
  "containers": {
    "updated": [],
    "all": [
      {
        "path": "apps/legacy-service",
        "app_name": "legacy-service",
        "container_name": "legacy-service",
        "context": "apps/legacy-service",
        "dockerfile": {
          "path": "apps/legacy-service/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [],
    "has_updates": false,
    "has_deletions": false
  },
  "ref": "HEAD~1"
}
```

## Scenario 5: Complete Folder Deletion

**Changes:** Deleted entire `apps/old-service/` folder (which contained Dockerfile, app.yaml, and source files)

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [],
    "all": [],
    "deleted": [
      {
        "path": "apps/old-service",
        "app_name": "old-service",
        "app_config": "apps/old-service/app.yaml",
        "commit_sha": "abc123def456789test0commit0sha0for0testing"
      }
    ],
    "has_updates": false,
    "has_deletions": true
  },
  "containers": {
    "updated": [],
    "all": [],
    "deleted": [
      {
        "app_name": "old-service",
        "container_name": "old-service",
        "context": "apps/old-service",
        "dockerfile": "apps/old-service/Dockerfile"
      }
    ],
    "has_updates": false,
    "has_deletions": true
  },
  "ref": "HEAD~1"
}
```

## Scenario 6: Pre-built Images Only App

**Repository structure:**

```
apps/
└── monitoring-stack/
    └── app.yaml  # No Dockerfiles, only pre-built images
```

**Changes:** Modified `app.yaml` in `apps/monitoring-stack/`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [
      {
        "path": "apps/monitoring-stack",
        "app_name": "monitoring-stack",
        "app_config": "apps/monitoring-stack/app.yaml"
      }
    ],
    "all": [
      {
        "path": "apps/monitoring-stack",
        "app_name": "monitoring-stack",
        "app_config": "apps/monitoring-stack/app.yaml"
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [],
    "all": [],
    "deleted": [],
    "has_updates": false,
    "has_deletions": false
  },
  "ref": "origin/main"
}
```

## Scenario 7: Mixed Changes and Deletions

**Changes:**

- Modified files in `apps/api/`
- Deleted `Dockerfile.cache` from `apps/api/`
- Deleted entire `apps/deprecated/` folder
- Added new `apps/new-service/`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [
      { "path": "apps/api", "app_name": "api", "app_config": "apps/api/app.yaml" },
      {
        "path": "apps/new-service",
        "app_name": "new-service",
        "app_config": "apps/new-service/app.yaml"
      }
    ],
    "all": [
      { "path": "apps/api", "app_name": "api", "app_config": "apps/api/app.yaml" },
      {
        "path": "apps/new-service",
        "app_name": "new-service",
        "app_config": "apps/new-service/app.yaml"
      }
    ],
    "deleted": [
      {
        "path": "apps/deprecated",
        "app_name": "deprecated",
        "app_config": "apps/deprecated/app.yaml",
        "commit_sha": "abc123def456789test0commit0sha0for0testing"
      }
    ],
    "has_updates": true,
    "has_deletions": true
  },
  "containers": {
    "updated": [
      {
        "path": "apps/api",
        "app_name": "api",
        "container_name": "api",
        "context": "apps/api",
        "dockerfile": {
          "path": "apps/api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "all": [
      {
        "path": "apps/api",
        "app_name": "api",
        "container_name": "api",
        "context": "apps/api",
        "dockerfile": {
          "path": "apps/api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      },
      {
        "path": "apps/new-service",
        "app_name": "new-service",
        "container_name": "new-service",
        "context": "apps/new-service",
        "dockerfile": {
          "path": "apps/new-service/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [
      {
        "app_name": "api",
        "container_name": "api-cache",
        "context": "apps/api",
        "dockerfile": "apps/api/Dockerfile.cache"
      },
      {
        "app_name": "deprecated",
        "container_name": "deprecated",
        "context": "apps/deprecated",
        "dockerfile": "apps/deprecated/Dockerfile"
      }
    ],
    "has_updates": true,
    "has_deletions": true
  },
  "ref": "HEAD~1"
}
```

## Scenario 8: Pull Request

**Context:** Pull request from `feature/update-auth` to `main`

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [{ "path": "apps/auth", "app_name": "auth", "app_config": "apps/auth/app.yaml" }],
    "all": [{ "path": "apps/auth", "app_name": "auth", "app_config": "apps/auth/app.yaml" }],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "containers": {
    "updated": [
      {
        "path": "apps/auth",
        "app_name": "auth",
        "container_name": "auth",
        "context": "apps/auth",
        "dockerfile": {
          "path": "apps/auth/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "all": [
      {
        "path": "apps/auth",
        "app_name": "auth",
        "container_name": "auth",
        "context": "apps/auth",
        "dockerfile": {
          "path": "apps/auth/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [],
    "has_updates": true,
    "has_deletions": false
  },
  "ref": "origin/main"
}
```

## Scenario 9: Workflow Dispatch (Manual Trigger)

**Context:** Manual workflow trigger - all apps should be available regardless of changes

**Analyzer Output:**

```json
{
  "apps": {
    "updated": [],
    "all": [
      { "path": "apps/web-api", "app_name": "web-api", "app_config": "apps/web-api/app.yaml" },
      { "path": "apps/frontend", "app_name": "frontend", "app_config": null }
    ],
    "deleted": [],
    "has_updates": false,
    "has_deletions": false
  },
  "containers": {
    "updated": [],
    "all": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "container_name": "web-api",
        "context": "apps/web-api",
        "dockerfile": {
          "path": "apps/web-api/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      },
      {
        "path": "apps/frontend",
        "app_name": "frontend",
        "container_name": "frontend",
        "context": "apps/frontend",
        "dockerfile": {
          "path": "apps/frontend/Dockerfile",
          "name": "Dockerfile",
          "suffix": ""
        }
      }
    ],
    "deleted": [],
    "has_updates": false,
    "has_deletions": false
  },
  "ref": ""
}
```

## Usage in GitHub Actions

### Building Changed Apps

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.analyze.outputs.matrix }}
      ref: ${{ steps.analyze.outputs.ref }}
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0

      - name: Analyze Build Scope
        id: analyze
        uses: your-org/build-scope-analyzer@v2

  build:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).apps.has_updates == true || fromJson(needs.analyze.outputs.matrix).containers.has_updates == true
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.matrix).apps.updated }}
    steps:
      - name: Build App
        run: |
          echo "Building app: ${{ matrix.app.app_name }}"
          echo "Path: ${{ matrix.app.path }}"
          echo "Config: ${{ matrix.app.app_config }}"

  build_containers:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).containers.has_updates == true
    strategy:
      matrix:
        container: ${{ fromJson(needs.analyze.outputs.matrix).containers.updated }}
    steps:
      - name: Build Container
        run: |
          echo "Building container for: ${{ matrix.container.app_name }}"
          echo "Using Dockerfile: ${{ matrix.container.dockerfile.path }}"
```

### Building All Apps (for workflow_dispatch)

```yaml
jobs:
  analyze:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.analyze.outputs.matrix }}
      ref: ${{ steps.analyze.outputs.ref }}
    steps:
      # ...same as above

  build:
    needs: analyze
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.matrix).apps.all }}
    steps:
      - name: Build App
        run: |
          echo "Building app: ${{ matrix.app.app_name }}"
```

### Cleaning Up Deleted Apps

```yaml
jobs:
  cleanup_apps:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).apps.has_deletions == true
    runs-on: ubuntu-latest
    strategy:
      matrix:
        app: ${{ fromJson(needs.analyze.outputs.matrix).apps.deleted }}
    steps:
      - name: Destroy Container App
        run: |
          echo "Destroying app: ${{ matrix.app.app_name }}"
          echo "Path: ${{ matrix.app.path }}"
          echo "App config: ${{ matrix.app.app_config }}"
          echo "Commit SHA: ${{ matrix.app.commit_sha }}"
```

### Cleaning Up Deleted Container Images

```yaml
jobs:
  cleanup_containers:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).containers.has_deletions == true
    runs-on: ubuntu-latest
    strategy:
      matrix:
        container: ${{ fromJson(needs.analyze.outputs.matrix).containers.deleted }}
    steps:
      - name: Delete from ACR
        run: |
          echo "Deleting container image: ${{ matrix.container.image_name }}"
          echo "From app: ${{ matrix.container.app_name }}"
```

### Job Dependency Order

```yaml
jobs:
  analyze:
    # ... analyze build scope

  cleanup_apps:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).apps.has_deletions == true
    # ... cleanup app steps

  cleanup_containers:
    needs: analyze
    if: fromJson(needs.analyze.outputs.matrix).containers.has_deletions == true
    # ... cleanup container steps

  build:
    needs: [analyze, cleanup_apps, cleanup_containers]
    if: fromJson(needs.analyze.outputs.matrix).apps.has_updates == true
    # ... build steps

  deploy:
    needs: [build]
    # ... deploy steps
```

## Output Reference

### Core Outputs

| Output   | Type   | Description                                                |
| -------- | ------ | ---------------------------------------------------------- |
| `matrix` | JSON   | Contains all app and container data in a structured format |
| `ref`    | String | Git reference used for comparison                          |

### Matrix Structure

The `matrix` output contains a JSON object with the following structure:

```typescript
interface Matrix {
  apps: {
    updated: AppItem[];
    all: AppItem[];
    deleted: DeletedApp[];
    has_updates: boolean;
    has_deletions: boolean;
  };
  containers: {
    updated: ContainerItem[];
    all: ContainerItem[];
    deleted: DeletedContainer[];
    has_updates: boolean;
    has_deletions: boolean;
  };
  ref: string;
}
```

### App Item Structure

```typescript
interface AppItem {
  path: string; // Relative path to app folder
  app_name: string; // App name (from config or folder)
  app_config: string | null; // Path to app.yaml/app.yml (null if not found)
}
```

### Container Item Structure

```typescript
interface ContainerItem {
  path: string; // Relative path to app folder
  app_name: string; // App name (from config or folder)
  container_name: string; // Container name (from config or Dockerfile)
  context: string; // Docker build context (from # @context: ... or folder)
  dockerfile: {
    path: string; // Path to Dockerfile
    name: string; // Dockerfile name
    suffix: string; // Suffix (e.g., .auth, .logger)
  };
}
```

### Deleted Container Structure

```typescript
interface DeletedContainer {
  app_name: string; // App name
  container_name: string; // Container name
  context: string; // Docker build context
  dockerfile: string; // Path to Dockerfile
  commit_sha: string; // Commit SHA of the version with this container
}
```

### Deleted App Structure

```typescript
interface DeletedApp {
  path: string; // Relative path to app folder
  app_name: string; // App name
  app_config: string; // Path to app.yaml/app.yml
  commit_sha: string; // Commit SHA of the version with this app
}
```

---

**Note:** All containers now include `container_name` and `context` fields. Deleted containers also include these fields for robust cleanup and traceability.
