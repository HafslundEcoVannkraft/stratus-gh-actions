#!/usr/bin/env python3
"""
Test script for build_scope_analyzer.py
Creates a test environment and runs the analyzer against it.
"""

import os
import sys
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch
from build_scope_analyzer import BuildScopeAnalyzer

def create_test_environment(test_dir: str):
    """Create a test environment with sample apps"""
    # Create frontend app
    frontend_dir = Path(test_dir) / 'frontend'
    frontend_dir.mkdir(parents=True)
    (frontend_dir / 'app.yaml').write_text('''
name: frontend
type: frontend
''')
    (frontend_dir / 'Dockerfile').write_text('FROM node:18-alpine')
    
    # Create backend app
    backend_dir = Path(test_dir) / 'backend'
    backend_dir.mkdir(parents=True)
    (backend_dir / 'app.yaml').write_text('''
name: backend
type: backend
''')
    (backend_dir / 'Dockerfile').write_text('FROM python:3.11-slim')
    
    # Create worker app
    worker_dir = Path(test_dir) / 'worker'
    worker_dir.mkdir(parents=True)
    (worker_dir / 'app.yaml').write_text('''
name: worker
type: worker
''')
    (worker_dir / 'Dockerfile').write_text('FROM python:3.11-slim')
    
    return test_dir

def test_analyzer():
    """Test the analyzer"""
    with tempfile.TemporaryDirectory() as test_dir:
        create_test_environment(test_dir)
        
        # Mock environment variables
        os.environ['GITHUB_SHA'] = 'abc123456789'
        os.environ['GITHUB_REF_NAME'] = 'main'
        os.environ['GITHUB_EVENT_NAME'] = 'push'
        
        print("=== Test 1: No filters ===")
        # Test with no filters
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir)
        )
        
        # Mock git commands to return changed files
        def mock_git_command(cmd):
            if '--name-only' in cmd and '--diff-filter=D' not in cmd:
                # Return changed files
                return 'frontend/app.yaml\nbackend/Dockerfile\nworker/app.yaml'
            elif '--diff-filter=D' in cmd:
                # Return deleted files (none in this test)
                return ''
            return ''
        
        # Test basic functionality with mocked git
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()
            
            print(f"Has changes: {result['has_changes']}")
            print(f"Number of apps found: {len(result['matrix']['include'])}")
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert result['has_changes'], "Should detect changes"
            assert len(result['matrix']['include']) == 3, "Should find all apps"
            
            app_names = [app['app_name'] for app in result['matrix']['include']]
            assert 'frontend' in app_names, "Should find frontend app"
            assert 'backend' in app_names, "Should find backend app"
            assert 'worker' in app_names, "Should find worker app"
        
        print("\n=== Test 2: Include pattern (frontend/*) ===")
        # Test include pattern
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            include_pattern='frontend/*'
        )
        
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()
            
            print(f"Has changes: {result['has_changes']}")
            print(f"Number of apps found: {len(result['matrix']['include'])}")
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert len(result['matrix']['include']) == 1, "Should only find frontend app"
            assert result['matrix']['include'][0]['app_name'] == 'frontend', "Should find frontend app"
        
        print("\n=== Test 3: Exclude pattern (worker/*) ===")
        # Test exclude pattern
        analyzer = BuildScopeAnalyzer(
            root_path=str(test_dir),
            exclude_pattern='worker/*'
        )
        
        with patch.object(analyzer, 'run_git_command', side_effect=mock_git_command):
            result = analyzer.generate_matrix_output()
            
            print(f"Has changes: {result['has_changes']}")
            print(f"Number of apps found: {len(result['matrix']['include'])}")
            print("Matrix output:")
            print(json.dumps(result['matrix'], indent=2))
            
            assert len(result['matrix']['include']) == 2, "Should find frontend and backend apps"
            app_names = [app['app_name'] for app in result['matrix']['include']]
            assert 'worker' not in app_names, "Should not find worker app"
        
        print("\n=== All tests passed! ===")

def example_github_workflow():
    """Example GitHub Actions workflow using the analyzer"""
    return '''
name: Build and Deploy Changed Apps

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  analyze-changes:
    runs-on: ubuntu-latest
    outputs:
      matrix: ${{ steps.scope.outputs.matrix }}
      has-changes: ${{ steps.scope.outputs.has-changes }}
      deleted-folders: ${{ steps.scope.outputs.deleted-folders }}
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Extract Docker metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ vars.REGISTRY_URL }}/${{ matrix.app_name }}
          tags: |
            type=sha,format=short
            type=ref,event=branch
            type=ref,event=tag
            type=raw,value=latest,enable=${{ github.ref == 'refs/heads/main' }}

      - name: Analyze changes
        id: scope
        uses: ./.github/actions/build-scope-analyzer
        with:
          root-path: .
          docker-metadata: ${{ steps.meta.outputs.json }}
'''

if __name__ == '__main__':
    test_analyzer()
    example_github_workflow() 