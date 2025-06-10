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
  "deletions": {
    "apps": [],
    "containers": [],
    "folders": []
  },
  "ref": "origin/main",
  "has_changes": true,
  "has_deletions": false
}
```

**GitHub Actions Outputs:**
```
matrix={"include":[{"path":"apps/web-api","app_name":"web-api","app_config":"apps/web-api/app.yaml","dockerfiles":[{"path":"apps/web-api/Dockerfile","name":"Dockerfile","suffix":""}]}]}
deletions={"apps":[],"containers":[],"folders":[]}
ref=origin/main
has_changes=true
has_deletions=false
deleted_apps=[]
deleted_containers=[]
deleted_folders=[]
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
    "containers": [],
    "folders": []
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
    ],
    "folders": []
  },
  "ref": "HEAD~1",
  "has_changes": true,
  "has_deletions": true
}
```

**GitHub Actions Outputs:**
```
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
    "containers": [],
    "folders": []
  },
  "ref": "HEAD~1",
  "has_changes": false,
  "has_deletions": true
}
```

## Scenario 5: Complete Folder Deletion

**Changes:** Deleted entire `apps/old-service/` folder

**Analyzer Output:**
```json
{
  "matrix": {
    "include": []
  },
  "deletions": {
    "apps": [],
    "containers": [],
    "folders": [
      {
        "path": "apps/old-service",
        "app_name": "old-service"
      }
    ]
  },
  "ref": "HEAD~1",
  "has_changes": false,
  "has_deletions": true
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
    "containers": [],
    "folders": []
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
    "apps": [],
    "containers": [
      {
        "app_name": "api",
        "container_name": "api-cache",
        "dockerfile": "apps/api/Dockerfile.cache",
        "image_name": "api-cache"
      }
    ],
    "folders": [
      {
        "path": "apps/deprecated",
        "app_name": "deprecated"
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
    "containers": [],
    "folders": []
  },
  "ref": "origin/main",
  "has_changes": true,
  "has_deletions": false
}
```

## Usage in GitHub Actions

### Building Changed Apps
```yaml
strategy:
  matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}
```

### Cleaning Up Deleted Apps
```yaml
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.deleted_apps) }}
```

### Cleaning Up Deleted Containers
```yaml
strategy:
  matrix:
    container: ${{ fromJson(needs.analyze.outputs.deleted_containers) }}
```

### Handling Complete Folder Deletions
```yaml
strategy:
  matrix:
    folder: ${{ fromJson(needs.analyze.outputs.deleted_folders) }}
``` 