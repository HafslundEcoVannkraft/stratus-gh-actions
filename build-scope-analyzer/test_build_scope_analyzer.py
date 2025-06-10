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
            
            print(f"Has changes: {result['has_changes']}")
            print(f"Has deletions: {result['has_deletions']}")
            print(f"Number of apps found: {len(result['matrix']['include'])}")
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert result['has_changes'], "Should detect changes"
            assert not result['has_deletions'], "Should not have deletions"
            assert len(result['matrix']['include']) == 2, "Should find 2 apps"

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
            
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert len(result['matrix']['include']) == 1, "Should find 1 app"
            app = result['matrix']['include'][0]
            assert app['app_name'] == 'secure-api'
            assert len(app['dockerfiles']) == 3, "Should find 3 Dockerfiles"
            
            # Check dockerfile names
            dockerfile_names = [df['name'] for df in app['dockerfiles']]
            assert 'Dockerfile' in dockerfile_names
            assert 'Dockerfile.auth' in dockerfile_names
            assert 'Dockerfile.logger' in dockerfile_names

def test_pre_built_only():
    """Test app with only pre-built images"""
    print("\n=== Test 3: Pre-built Images Only (Container Apps mode) ===")
    
    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'pre-built-only')
        
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*',
            require_app_config=True  # Container Apps mode
        )
        
        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/monitoring/app.yaml'
            return ''
        
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()
            
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert len(result['matrix']['include']) == 1, "Should find monitoring app"
            app = result['matrix']['include'][0]
            assert app['app_name'] == 'monitoring'
            assert len(app['dockerfiles']) == 0, "Should have no Dockerfiles"

def test_deletions():
    """Test various deletion scenarios"""
    print("\n=== Test 4: Deletion Scenarios ===")
    
    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'deletion-ready')
        
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*',
            require_app_config=True
        )
        
        # Test 4a: Deleted Dockerfile (sidecar container)
        print("\n--- Test 4a: Deleted Sidecar Container ---")
        def mock_git_deleted_dockerfile(cmd):
            if '--name-status' in cmd:
                return 'D\tapps/payment-service/Dockerfile.monitor\nM\tapps/payment-service/app.yaml'
            return ''
        
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_deleted_dockerfile):
            result = analyzer.generate_matrix_output()
            
            print("Deletions output:")
            print(json.dumps(result['deletions'], indent=2))
            
            assert result['has_deletions'], "Should have deletions"
            assert len(result['deletions']['containers']) == 1, "Should have 1 deleted container"
            deleted_container = result['deletions']['containers'][0]
            assert deleted_container['container_name'] == 'payment-service-monitor'
            assert deleted_container['image_name'] == 'payment-service-monitor'
        
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
            
            print("Deletions output:")
            print(json.dumps(result['deletions'], indent=2))
            
            assert len(result['deletions']['apps']) == 1, "Should have 1 deleted app"
            deleted_app = result['deletions']['apps'][0]
            assert deleted_app['app_name'] == 'legacy-service'
            assert 'app.yaml' in deleted_app['deleted_config']
        
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
            
            print("Deletions output:")
            print(json.dumps(result['deletions'], indent=2))
            
            assert len(result['deletions']['folders']) == 1, "Should have 1 deleted folder"
            deleted_folder = result['deletions']['folders'][0]
            assert deleted_folder['app_name'] == 'deprecated-service'

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
                return '''M\tapps/frontend/app.yaml
A\tapps/secure-api/Dockerfile.logger
D\tapps/backend/Dockerfile.cache
D\tapps/old-service/app.yaml
D\tapps/old-service/Dockerfile'''
            return ''
        
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_mixed):
            result = analyzer.generate_matrix_output()
            
            print("\nFull output:")
            print(json.dumps(result, indent=2))
            
            # Check changes
            assert result['has_changes'], "Should have changes"
            assert result['has_deletions'], "Should have deletions"
            assert len(result['matrix']['include']) >= 2, "Should have at least 2 apps with changes"
            
            # Check deletions
            assert len(result['deletions']['containers']) >= 1, "Should have deleted containers"
            assert len(result['deletions']['folders']) >= 1, "Should have deleted folders"

def test_github_actions_output():
    """Test GitHub Actions output format"""
    print("\n=== Test 6: GitHub Actions Output Format ===")
    
    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir, 'mixed')
        
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='apps/*'
        )
        
        def mock_git_command(cmd):
            if '--name-status' in cmd:
                return 'M\tapps/web-app/app.yaml\nD\tapps/web-app/Dockerfile.old'
            return ''
        
        # Mock GITHUB_OUTPUT environment variable
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as output_file:
            os.environ['GITHUB_OUTPUT'] = output_file.name
            
            with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
                # Run main function
                from build_scope_analyzer import main
                with patch('sys.argv', ['analyzer', '--include-pattern', 'apps/*', '--root-path', test_dir]):
                    main()
            
            # Read the output file
            output_file.seek(0)
            output_content = output_file.read()
            print("\nGitHub Actions output:")
            print(output_content)
            
            # Verify output format
            assert 'matrix=' in output_content
            assert 'has_changes=' in output_content
            assert 'has_deletions=' in output_content
            assert 'deleted_apps=' in output_content
            assert 'deleted_containers=' in output_content
            assert 'deleted_folders=' in output_content
            
            os.unlink(output_file.name)

def test_exclude_pattern():
    """Test exclude pattern functionality"""
    print("\n=== Test 7: Exclude Pattern ===")
    
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
            
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            app_names = [app['app_name'] for app in result['matrix']['include']]
            assert 'frontend' in app_names, "Should include frontend"
            assert 'test-app' not in app_names, "Should exclude test-app"

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
        test_github_actions_output()
        test_exclude_pattern()
        
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