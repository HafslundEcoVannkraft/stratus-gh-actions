#!/usr/bin/env python3
"""
Example outputs from the Build Scope Analyzer V3
Shows what the analyzer outputs for different scenarios
"""

import json

def print_scenario(title, description, output):
    """Pretty print a scenario"""
    print(f"\n{'=' * 60}")
    print(f"SCENARIO: {title}")
    print(f"Description: {description}")
    print(f"{'=' * 60}")
    print("\nAnalyzer Output:")
    print(json.dumps(output, indent=2))
    print("\nGitHub Actions Matrix:")
    print(f"matrix={json.dumps(output['matrix'])}")
    if output.get('has_deletions'):
        print(f"deleted_apps={json.dumps(output['deletions']['apps'])}")
        print(f"deleted_containers={json.dumps(output['deletions']['containers'])}")
        print(f"deleted_folders={json.dumps(output['deletions']['folders'])}")

# Scenario 1: Simple app with changes
scenario1 = {
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
    "has_changes": True,
    "has_deletions": False
}

print_scenario(
    "Simple App Change",
    "Modified files in a single-container app",
    scenario1
)

# Scenario 2: Multi-container app
scenario2 = {
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
    "has_changes": True,
    "has_deletions": False
}

print_scenario(
    "Multi-Container App",
    "App with main container and two sidecars",
    scenario2
)

# Scenario 3: Deleted sidecar
scenario3 = {
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
    "has_changes": True,
    "has_deletions": True
}

print_scenario(
    "Deleted Sidecar Container",
    "Removed monitoring sidecar from payment service",
    scenario3
)

# Scenario 4: Deleted app (app.yaml removed)
scenario4 = {
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
    "has_changes": False,
    "has_deletions": True
}

print_scenario(
    "Deleted App Configuration",
    "app.yaml removed but folder still exists",
    scenario4
)

# Scenario 5: Complete folder deletion
scenario5 = {
    "matrix": {
        "include": []
    },
    "deletions": {
        "apps": [],
        "containers": [],
        "folders": [
            {
                "path": "apps/deprecated-service",
                "app_name": "deprecated-service"
            }
        ]
    },
    "ref": "HEAD~1",
    "has_changes": False,
    "has_deletions": True
}

print_scenario(
    "Complete Folder Deletion",
    "Entire app folder removed from repository",
    scenario5
)

# Scenario 6: Pre-built images only
scenario6 = {
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
    "has_changes": True,
    "has_deletions": False
}

print_scenario(
    "Pre-built Images Only",
    "App using only external images (no Dockerfiles)",
    scenario6
)

# Scenario 7: Complex mixed scenario
scenario7 = {
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
                    },
                    {
                        "path": "apps/new-service/Dockerfile.worker",
                        "name": "Dockerfile.worker",
                        "suffix": "worker"
                    }
                ]
            }
        ]
    },
    "deletions": {
        "apps": [
            {
                "path": "apps/old-api",
                "app_name": "old-api",
                "deleted_config": "apps/old-api/app.yaml"
            }
        ],
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
    "has_changes": True,
    "has_deletions": True
}

print_scenario(
    "Complex Mixed Changes",
    "Multiple apps changed, containers deleted, folders removed",
    scenario7
)

print("\n" + "=" * 60)
print("WORKFLOW USAGE EXAMPLES")
print("=" * 60)

print("""
# Building changed apps:
strategy:
  matrix: ${{ fromJson(needs.analyze.outputs.matrix) }}

# Cleaning up deleted apps (Terraform destroy):
strategy:
  matrix:
    app: ${{ fromJson(needs.analyze.outputs.deleted_apps) }}

# Cleaning up deleted containers (ACR cleanup):
strategy:
  matrix:
    container: ${{ fromJson(needs.analyze.outputs.deleted_containers) }}

# Handling complete folder deletions:
strategy:
  matrix:
    folder: ${{ fromJson(needs.analyze.outputs.deleted_folders) }}
""") 