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

**Analyzer Output:**
```json
{
  "matrix": {
    "include": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "app_config": "apps/web-api/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/web-api/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          }
        ]
      }
    ]
  },
  "all_apps": {
    "include": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "app_config": "apps/web-api/app.yaml",
        "dockerfiles": [...]
      },
      {
        "path": "apps/frontend",
        "app_name": "frontend",
        "app_config": null,
        "dockerfiles": [...]
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": []
  },
  "ref": "origin/main",
  "has_changes": true,
  "has_deletions": false
}
```

**GitHub Actions Outputs:**
```
matrix={"include":[{"path":"apps/web-api","app_name":"web-api","app_config":"apps/web-api/app.yaml","dockerfiles":[{"path":"apps/web-api/Dockerfile","name":"Dockerfile","suffix":""}]}]}
all_apps={"include":[{"path":"apps/web-api","app_name":"web-api","app_config":"apps/web-api/app.yaml","dockerfiles":[...]},{"path":"apps/frontend","app_name":"frontend","app_config":null,"dockerfiles":[...]}]}
deletions={"apps":[],"containers":[]}
ref=origin/main
has_changes=true
has_deletions=false
deleted_apps=[]
deleted_containers=[]
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
  "matrix": {
    "include": [
      {
        "path": "apps/secure-api",
        "app_name": "secure-api",
        "app_config": "apps/secure-api/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/secure-api/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          },
          {
            "path": "apps/secure-api/Dockerfile.auth",
            "name": "Dockerfile.auth",
            "suffix": "auth"
          },
          {
            "path": "apps/secure-api/Dockerfile.logger",
            "name": "Dockerfile.logger",
            "suffix": "logger"
          }
        ]
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": []
  },
  "ref": "HEAD~1",
  "has_changes": true,
  "has_deletions": false
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
  "matrix": {
    "include": [
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "app_config": "apps/payment-service/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/payment-service/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          }
        ]
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": [
      {
        "app_name": "payment-service",
        "container_name": "payment-service-monitor",
        "dockerfile": "apps/payment-service/Dockerfile.monitor",
        "image_name": "payment-service-monitor"
      }
    ]
  },
  "ref": "HEAD~1",
  "has_changes": true,
  "has_deletions": true
}
```

**GitHub Actions Outputs:**
```
matrix={"include":[{"path":"apps/payment-service","app_name":"payment-service","app_config":"apps/payment-service/app.yaml","dockerfiles":[{"path":"apps/payment-service/Dockerfile","name":"Dockerfile","suffix":""}]}]}
has_changes=true
has_deletions=true
deleted_apps=[]
deleted_containers=[{"app_name":"payment-service","container_name":"payment-service-monitor","dockerfile":"apps/payment-service/Dockerfile.monitor","image_name":"payment-service-monitor"}]
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
  "matrix": {
    "include": []
  },
  "deletions": {
    "apps": [
      {
        "path": "apps/legacy-service",
        "app_name": "legacy-service",
        "deleted_config": "apps/legacy-service/app.yaml"
      }
    ],
    "containers": []
  },
  "ref": "HEAD~1",
  "has_changes": false,
  "has_deletions": true
}
```

**GitHub Actions Outputs:**
```
matrix={"include":[]}
has_changes=false
has_deletions=true
deleted_apps=[{"path":"apps/legacy-service","app_name":"legacy-service","deleted_config":"apps/legacy-service/app.yaml"}]
deleted_containers=[]
```

## Scenario 5: Complete Folder Deletion

**Changes:** Deleted entire `apps/old-service/` folder (which contained Dockerfile, app.yaml, and source files)

**Analyzer Output:**
```json
{
  "matrix": {
    "include": []
  },
  "deletions": {
    "apps": [
      {
        "path": "apps/old-service",
        "app_name": "old-service",
        "deleted_config": "folder_deleted"
      }
    ],
    "containers": [
      {
        "app_name": "old-service",
        "container_name": "old-service",
        "dockerfile": "apps/old-service/Dockerfile",
        "image_name": "old-service"
      }
    ]
  },
  "ref": "HEAD~1",
  "has_changes": false,
  "has_deletions": true
}
```

**GitHub Actions Outputs:**
```
matrix={"include":[]}
has_changes=false
has_deletions=true
deleted_apps=[{"path":"apps/old-service","app_name":"old-service","deleted_config":"folder_deleted"}]
deleted_containers=[{"app_name":"old-service","container_name":"old-service","dockerfile":"apps/old-service/Dockerfile","image_name":"old-service"}]
```

## Scenario 6: Pre-built Images Only App

**Repository structure:**
```
apps/
└── monitoring-stack/
    └── app.yaml  # No Dockerfiles, only pre-built images
```

**Changes:** Modified `app.yaml` in `apps/monitoring-stack/`

**Analyzer Output (with `require-app-config: true`):**
```json
{
  "matrix": {
    "include": [
      {
        "path": "apps/monitoring-stack",
        "app_name": "monitoring-stack",
        "app_config": "apps/monitoring-stack/app.yaml",
        "dockerfiles": []
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": []
  },
  "ref": "origin/main",
  "has_changes": true,
  "has_deletions": false
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
  "matrix": {
    "include": [
      {
        "path": "apps/api",
        "app_name": "api",
        "app_config": "apps/api/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/api/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          }
        ]
      },
      {
        "path": "apps/new-service",
        "app_name": "new-service",
        "app_config": "apps/new-service/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/new-service/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          }
        ]
      }
    ]
  },
  "deletions": {
    "apps": [
      {
        "path": "apps/deprecated",
        "app_name": "deprecated",
        "deleted_config": "folder_deleted"
      }
    ],
    "containers": [
      {
        "app_name": "api",
        "container_name": "api-cache",
        "dockerfile": "apps/api/Dockerfile.cache",
        "image_name": "api-cache"
      },
      {
        "app_name": "deprecated",
        "container_name": "deprecated",
        "dockerfile": "apps/deprecated/Dockerfile",
        "image_name": "deprecated"
      }
    ]
  },
  "ref": "HEAD~1",
  "has_changes": true,
  "has_deletions": true
}
```

## Scenario 8: Pull Request

**Context:** Pull request from `feature/update-auth` to `main`

**Analyzer Output:**
```json
{
  "matrix": {
    "include": [
      {
        "path": "apps/auth-service",
        "app_name": "auth-service",
        "app_config": "apps/auth-service/app.yaml",
        "dockerfiles": [
          {
            "path": "apps/auth-service/Dockerfile",
            "name": "Dockerfile",
            "suffix": ""
          }
        ]
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": []
  },
  "ref": "origin/main",
  "has_changes": true,
  "has_deletions": false
}
```

## Scenario 9: Workflow Dispatch (Manual Trigger)

**Context:** Manual workflow trigger - all apps should be available regardless of changes

**Analyzer Output:**
```json
{
  "matrix": {
    "include": []
  },
  "all_apps": {
    "include": [
      {
        "path": "apps/web-api",
        "app_name": "web-api",
        "app_config": "apps/web-api/app.yaml",
        "dockerfiles": [...]
      },
      {
        "path": "apps/auth-service",
        "app_name": "auth-service",
        "app_config": "apps/auth-service/app.yaml",
        "dockerfiles": [...]
      },
      {
        "path": "apps/payment-service",
        "app_name": "payment-service",
        "app_config": "apps/payment-service/app.yaml",
        "dockerfiles": [...]
      }
    ]
  },
  "deletions": {
    "apps": [],
    "containers": []
  },
  "ref": "",
  "has_changes": false,
  "has_deletions": false
}
```

## Usage in GitHub Actions

### Building Changed Apps
```yaml
strategy:
  matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
```

### Building All Apps (for workflow_dispatch)
```yaml
strategy:
  matrix: ${{ fromJson(needs.analyze.outputs.all_apps) }}
```

### Cleaning Up Deleted Apps
```yaml
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.deleted_apps) }}
steps:
  - name: Destroy Container App
    run: |
      echo "Destroying app: ${{ matrix.app.app_name }}"
      echo "Path: ${{ matrix.app.path }}"
      echo "Deletion reason: ${{ matrix.app.deleted_config }}"
```

### Cleaning Up Deleted Container Images
```yaml
strategy:
  matrix:
    container: ${{ fromJson(needs.analyze.outputs.deleted_containers) }}
steps:
  - name: Delete from ACR
    run: |
      echo "Deleting container image: ${{ matrix.container.image_name }}"
      echo "From app: ${{ matrix.container.app_name }}"
```

### Conditional Workflows
```yaml
jobs:
  build:
    if: needs.analyze.outputs.has_changes == 'true'
    # ... build steps

  cleanup:
    if: needs.analyze.outputs.has_deletions == 'true'
    # ... cleanup steps
```

## Output Reference

### Core Outputs

| Output | Type | Description |
|--------|------|-------------|
| `matrix` | JSON | Apps with changes that need to be built |
| `all_apps` | JSON | All apps in the repository (for workflow_dispatch) |
| `deletions` | JSON | Complete deletion information object |
| `deleted_apps` | JSON Array | Apps that need to be destroyed |
| `deleted_containers` | JSON Array | Container images that need ACR cleanup |
| `ref` | String | Git reference used for comparison |
| `has_changes` | Boolean | Whether any changes were detected |
| `has_deletions` | Boolean | Whether any deletions were detected |

### Matrix Item Structure

```typescript
interface MatrixItem {
  path: string;           // Relative path to app folder
  app_name: string;       // Name of the app (folder name)
  app_config?: string;    // Path to app.yaml/app.yml (optional)
  dockerfiles: Array<{
    path: string;         // Path to Dockerfile
    name: string;         // Dockerfile name (e.g., "Dockerfile.sidecar")
    suffix: string;       // Container suffix (e.g., "sidecar", empty for main)
  }>;
}
```

### Deleted App Structure

```typescript
interface DeletedApp {
  path: string;           // Path to app folder
  app_name: string;       // Name of the app
  deleted_config: string; // Either file path or "folder_deleted"
}
```

### Deleted Container Structure

```typescript
interface DeletedContainer {
  app_name: string;       // Parent app name
  container_name: string; // Full container name (app-suffix)
  dockerfile: string;     // Path to deleted Dockerfile
  image_name: string;     // Image name for ACR cleanup
}
``` 