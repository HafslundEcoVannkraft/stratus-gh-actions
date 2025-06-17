#!/usr/bin/env python3
"""
Test script for build_scope_analyzer.py
Creates test environments and runs the analyzer against various scenarios.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from build_scope_analyzer import BuildScopeAnalyzer

def create_test_environment(test_dir: str, scenario: str = 'basic'):
    """Create different test environments based on scenario"""

    if scenario == 'basic':
        # Create simple apps
        frontend_dir = Path(test_dir) / 'apps' / 'frontend'
        frontend_dir.mkdir(parents=True)
        (frontend_dir / 'app.yaml').write_text('''name: frontend
template:
  containers:
    - name: frontend
      cpu: 0.5
      memory: "1Gi"
''')
        (frontend_dir / 'Dockerfile').write_text('FROM node:18-alpine')

        backend_dir = Path(test_dir) / 'apps' / 'backend'
        backend_dir.mkdir(parents=True)
        (backend_dir / 'app.yaml').write_text('''name: backend
template:
  containers:
    - name: backend
      cpu: 1.0
      memory: "2Gi"
''')
        (backend_dir / 'Dockerfile').write_text('FROM python:3.11-slim')

    elif scenario == 'multi-container':
        # Create app with multiple containers
        api_dir = Path(test_dir) / 'apps' / 'secure-api'
        api_dir.mkdir(parents=True)
        (api_dir / 'app.yaml').write_text('''name: secure-api
template:
  containers:
    - name: secure-api
      dockerfile: Dockerfile
      cpu: 1.0
      memory: "2Gi"
    - name: secure-api-auth
      dockerfile: Dockerfile.auth
      cpu: 0.5
      memory: "1Gi"
    - name: secure-api-logger
      dockerfile: Dockerfile.logger
      cpu: 0.25
      memory: "0.5Gi"
''')
        (api_dir / 'Dockerfile').write_text('FROM python:3.11-slim')
        (api_dir / 'Dockerfile.auth').write_text('FROM node:18-alpine')
        (api_dir / 'Dockerfile.logger').write_text('FROM fluent/fluentd:latest')

    elif scenario == 'pre-built-only':
        # Create app with only pre-built images
        monitoring_dir = Path(test_dir) / 'apps' / 'monitoring'
        monitoring_dir.mkdir(parents=True)
        (monitoring_dir / 'app.yaml').write_text('''name: monitoring
template:
  containers:
    - name: prometheus
      image: prom/prometheus:v2.45.0
      cpu: 1.0
      memory: "2Gi"
    - name: grafana
      image: grafana/grafana:10.0.0
      cpu: 0.5
      memory: "1Gi"
''')
        # No Dockerfiles for this app

    elif scenario == 'mixed':
        # Create app with both built and pre-built containers
        web_dir = Path(test_dir) / 'apps' / 'web-app'
        web_dir.mkdir(parents=True)
        (web_dir / 'app.yaml').write_text('''name: web-app
template:
  containers:
    - name: web-app
      dockerfile: Dockerfile
      cpu: 1.0
      memory: "2Gi"
    - name: web-app-cache
      dockerfile: Dockerfile.cache
      cpu: 0.5
      memory: "1Gi"
    - name: oauth-proxy
      image: quay.io/oauth2-proxy/oauth2-proxy:v7.5.0
      cpu: 0.25
      memory: "0.5Gi"
''')
        (web_dir / 'Dockerfile').write_text('FROM node:18-alpine')
        (web_dir / 'Dockerfile.cache').write_text('FROM redis:7-alpine')

    elif scenario == 'deletion-ready':
        # Create apps that will be used for deletion testing
        # App with multiple containers
        payment_dir = Path(test_dir) / 'apps' / 'payment-service'
        payment_dir.mkdir(parents=True)
        (payment_dir / 'app.yaml').write_text('''name: payment-service
template:
  containers:
    - name: payment-service
      cpu: 1.0
      memory: "2Gi"
    - name: payment-service-monitor
      dockerfile: Dockerfile.monitor
      cpu: 0.25
      memory: "0.5Gi"
''')
        (payment_dir / 'Dockerfile').write_text('FROM python:3.11-slim')
        (payment_dir / 'Dockerfile.monitor').write_text('FROM prom/node-exporter:latest')

        # App that will have its app.yaml deleted
        legacy_dir = Path(test_dir) / 'apps' / 'legacy-service'
        legacy_dir.mkdir(parents=True)
        (legacy_dir / 'app.yaml').write_text('''name: legacy-service
template:
  containers:
    - name: legacy-service
      cpu: 0.5
      memory: "1Gi"
''')
        (legacy_dir / 'Dockerfile').write_text('FROM node:16-alpine')

        # App that will be completely deleted
        deprecated_dir = Path(test_dir) / 'apps' / 'deprecated-service'
        deprecated_dir.mkdir(parents=True)
        (deprecated_dir / 'app.yaml').write_text('''name: deprecated-service
template:
  containers:
    - name: deprecated-service
      cpu: 0.25
      memory: "0.5Gi"
''')
        (deprecated_dir / 'Dockerfile').write_text('FROM node:14-alpine')

    return test_dir

def test_basic_functionality():
    """Test basic app detection and matrix generation"""
    print("\n=== Test 1: Basic Functionality ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'basic')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        # Mock git command to return changed files
        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/frontend/app.yaml\nM\tapps/backend/Dockerfile'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            updated_app_names = [app['app_name'] for app in result['apps']['updated']]
            assert set(updated_app_names) == {'frontend', 'backend'}, "Should detect both frontend and backend as changed apps"
            updated_container_names = [c['app_name'] for c in result['containers']['updated']]
            assert set(updated_container_names) == {'frontend', 'backend'}, "Should detect both frontend and backend as changed containers"
            assert not result['apps']['deleted'], "No deleted apps"
            assert not result['containers']['deleted'], "No deleted containers"
            # Assert new output structure for containers
            for c in result['containers']['all']:
                assert 'container_name' in c, f"container_name missing in: {c}"
                assert 'context' in c, f"context missing in: {c}"
                assert isinstance(c['dockerfile'], dict), f"dockerfile not dict in: {c}"

def test_multi_container():
    """Test multi-container app detection"""
    print("\n=== Test 2: Multi-Container App ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'multi-container')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'A\tapps/secure-api/Dockerfile.logger'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            assert len(result['apps']['updated']) == 1, "Should detect 1 changed app (secure-api)"
            assert result['apps']['updated'][0]['app_name'] == 'secure-api'
            # All Dockerfiles should be in containers.all
            all_dockerfiles = [c['dockerfile']['name'] for c in result['containers']['all'] if c['app_name'] == 'secure-api']
            assert set(all_dockerfiles) == {'Dockerfile', 'Dockerfile.auth', 'Dockerfile.logger'}
            updated_dockerfiles = [c['dockerfile']['name'] for c in result['containers']['updated'] if c['app_name'] == 'secure-api']
            assert set(updated_dockerfiles) == {'Dockerfile', 'Dockerfile.auth', 'Dockerfile.logger'}, \
                "All Dockerfiles should be in updated for secure-api when any file changes"
            # Assert new output structure for containers
            for c in result['containers']['all']:
                assert 'container_name' in c, f"container_name missing in: {c}"
                assert 'context' in c, f"context missing in: {c}"
                assert isinstance(c['dockerfile'], dict), f"dockerfile not dict in: {c}"

def test_pre_built_only():
    """Test app with only pre-built images"""
    print("\n=== Test 3: Pre-built Images Only ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'pre-built-only')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/monitoring/app.yaml'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            assert any(app['app_name'] == 'monitoring' for app in result['apps']['all']), "Should find monitoring app"
            assert not result['containers']['all'], "Should have no containers for monitoring"

def test_deletions():
    """Test various deletion scenarios"""
    print("\n=== Test 4: Deletion Scenarios ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'deletion-ready')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        # Test 4a: Deleted Dockerfile (sidecar container)
        print("\n--- Test 4a: Deleted Sidecar Container ---")
        def mock_git_deleted_dockerfile(cmd):
            if '--name-status' in cmd:
                return 'D\tapps/payment-service/Dockerfile.monitor\nM\tapps/payment-service/app.yaml'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_deleted_dockerfile):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            deleted = result['containers']['deleted']
            assert any(c['container_name'] == 'payment-service-monitor' for c in deleted), "Should cleanup deleted container image for Dockerfile.monitor"
            # Assert deleted container structure
            for c in deleted:
                assert 'container_name' in c, f"container_name missing in: {c}"
                assert 'dockerfile' in c, f"dockerfile missing in: {c}"

        # Test 4b: Deleted app.yaml
        print("\n--- Test 4b: Deleted app.yaml ---")
        def mock_git_deleted_app_yaml(cmd):
            if '--name-status' in cmd:
                return 'D\tapps/legacy-service/app.yaml'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_deleted_app_yaml):
            # Simulate app.yaml being deleted
            (Path(test_dir) / 'apps' / 'legacy-service' / 'app.yaml').unlink()

            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            deleted = result['apps']['deleted']
            assert any(a['app_name'] == 'legacy-service' for a in deleted), "Should cleanup deleted app when app.yaml is deleted"

        # Test 4c: Entire folder deleted
        print("\n--- Test 4c: Entire Folder Deleted ---")
        def mock_git_deleted_folder(cmd):
            if '--name-status' in cmd:
                return 'D\tapps/deprecated-service/app.yaml\nD\tapps/deprecated-service/Dockerfile'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_deleted_folder):
            # Simulate entire folder being deleted
            shutil.rmtree(Path(test_dir) / 'apps' / 'deprecated-service')

            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            assert any(a['app_name'] == 'deprecated-service' for a in result['apps']['deleted']), "Should cleanup deleted app for folder deletion"
            deleted_containers = result['containers']['deleted']
            for c in deleted_containers:
                assert 'container_name' in c, f"container_name missing in: {c}"
                assert 'dockerfile' in c, f"dockerfile missing in: {c}"

def test_mixed_changes_and_deletions():
    """Test scenario with both changes and deletions"""
    print("\n=== Test 5: Mixed Changes and Deletions ===")

    with tempfile.TemporaryDirectory() as test_dir:
        # Create multiple apps
        create_test_environment(test_dir, 'basic')
        create_test_environment(test_dir, 'multi-container')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        def mock_git_mixed(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/frontend/app.yaml\nA\tapps/secure-api/Dockerfile.logger\nD\tapps/backend/Dockerfile.cache\nD\tapps/old-service/app.yaml\nD\tapps/old-service/Dockerfile'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_mixed):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            assert any(a['app_name'] == 'frontend' for a in result['apps']['updated']), "Should detect frontend as changed app"
            assert any(c['dockerfile']['name'] == 'Dockerfile.logger' for c in result['containers']['updated']), "Should detect Dockerfile.logger as new container"
            assert any(c['container_name'] == 'backend-cache' for c in result['containers']['deleted']), "Should cleanup deleted backend-cache container"
            assert any(a['app_name'] == 'old-service' for a in result['apps']['deleted']), "Should cleanup deleted old-service app"
            # Assert deleted container structure
            for c in result['containers']['deleted']:
                assert 'container_name' in c, f"container_name missing in: {c}"
                assert 'dockerfile' in c, f"dockerfile missing in: {c}"

def test_exclude_pattern():
    """Test exclude pattern functionality"""
    print("\n=== Test 6: Exclude Pattern ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'basic')

        # Create additional test app
        test_app_dir = Path(test_dir) / 'apps' / 'test-app'
        test_app_dir.mkdir(parents=True)
        (test_app_dir / 'Dockerfile').write_text('FROM alpine:latest')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*',
            exclude_pattern='apps/test-*'
        )

        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/frontend/app.yaml\nM\tapps/test-app/Dockerfile'
            return ''

        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()

            print(json.dumps(result, indent=2))

            app_names = [app['app_name'] for app in result['apps']['updated']]
            assert 'frontend' in app_names, "Should include frontend"
            assert 'test-app' not in app_names, "Should exclude test-app"

def test_workflow_dispatch_event():
    """Test workflow_dispatch event handling"""
    print("\n=== Test 7: Workflow Dispatch Event ===")

    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'basic')

        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )

        # Mock workflow_dispatch event
        with patch.dict(os.environ, {'GITHUB_EVENT_NAME': 'workflow_dispatch'}):
            # Mock git command should not be called for workflow_dispatch
            def mock_git_command(cmd):
                if '--name-status' in cmd and 'HEAD~1' in cmd:
                    raise Exception("Should not try to diff against HEAD~1 for workflow_dispatch")
                return ''

            with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
                result = analyzer.generate_matrix_output()

                print(json.dumps(result, indent=2))

                assert not result['apps']['updated'], "No changed apps for workflow_dispatch"
                assert not result['containers']['updated'], "No changed containers for workflow_dispatch"
                assert result['apps']['all'], "Should list all apps in all"
                assert result['containers']['all'], "Should list all containers in all"
                for c in result['containers']['all']:
                    assert 'container_name' in c, f"container_name missing in: {c}"
                    assert 'context' in c, f"context missing in: {c}"
                    assert isinstance(c['dockerfile'], dict), f"dockerfile not dict in: {c}"

def run_all_tests():
    """Run all tests"""
    print("Running Build Scope Analyzer V3 Tests")
    print("=" * 50)

    try:
        test_basic_functionality()
        test_multi_container()
        test_pre_built_only()
        test_deletions()
        test_mixed_changes_and_deletions()
        test_exclude_pattern()
        test_workflow_dispatch_event()

        print("\n" + "=" * 50)
        print("✅ All tests passed!")

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    run_all_tests()