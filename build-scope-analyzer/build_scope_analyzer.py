#!/usr/bin/env python3
"""
Build Scope Analyzer V3 - Enhanced deletion tracking

This script analyzes git diff to identify what needs to be built and what was deleted.
It provides detailed deletion information for proper cleanup in CI/CD pipelines.
"""

import os
import sys
import json
import subprocess
import argparse
import fnmatch
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any


class BuildScopeAnalyzer:
    """Analyzes git changes and generates strategy matrix output"""
    
    def __init__(self, root_path: str, include_pattern: str = '', exclude_pattern: str = '', 
                 require_app_config: bool = False):
        self.root_path = Path(root_path).resolve()
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.require_app_config = require_app_config
        self.changed_files: Set[Path] = set()
        self.deleted_files: Set[Path] = set()
        self.renamed_files: Dict[Path, Path] = {}  # old_path -> new_path
        
    def run_git_command(self, cmd: List[str]) -> str:
        """Execute a git command and return output"""
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Git command failed: {' '.join(cmd)}", file=sys.stderr)
            print(f"Error: {e.stderr}", file=sys.stderr)
            sys.exit(1)
            
    def get_event_type(self) -> str:
        """Get GitHub event type from environment"""
        return os.environ.get('GITHUB_EVENT_NAME', 'push')
        
    def get_comparison_ref(self) -> str:
        """Determine the reference to compare against"""
        event_type = self.get_event_type()
        
        if event_type == 'pull_request':
            # For PRs, compare against the base branch
            base_ref = os.environ.get('GITHUB_BASE_REF', 'main')
            return f"origin/{base_ref}"
        elif event_type == 'workflow_dispatch':
            # For workflow_dispatch, we don't need to compare against anything
            # since we'll use all_apps output anyway
            # Return empty string to indicate no comparison needed
            return ""
        else:
            # For push events, compare against previous commit
            return "HEAD~1"
            
    def get_changed_files(self) -> Tuple[Set[Path], Set[Path], Dict[Path, Path]]:
        """Get list of changed, deleted, and renamed files from git diff"""
        ref = self.get_comparison_ref()
        
        # If ref is empty (workflow_dispatch), return empty sets
        if not ref:
            return set(), set(), {}
        
        # Get all changes with status
        diff_output = self.run_git_command(['git', 'diff', '--name-status', ref])
        
        changed = set()
        deleted = set()
        renamed = {}
        
        for line in diff_output.splitlines():
            if not line:
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            status = parts[0]
            
            if status == 'D':  # Deleted
                deleted.add(Path(parts[1]))
            elif status == 'R':  # Renamed
                if len(parts) >= 3:
                    old_path = Path(parts[1])
                    new_path = Path(parts[2])
                    renamed[old_path] = new_path
                    changed.add(new_path)
            elif status in ['A', 'M']:  # Added or Modified
                changed.add(Path(parts[1]))
                
        return changed, deleted, renamed
        
    def should_include_path(self, path: Path) -> bool:
        """Check if path should be included based on patterns"""
        path_str = str(path)
        
        # First check include pattern if specified
        if self.include_pattern:
            if not fnmatch.fnmatch(path_str, self.include_pattern):
                return False
                
        # Then check exclude pattern if specified
        if self.exclude_pattern:
            if fnmatch.fnmatch(path_str, self.exclude_pattern):
                return False
                
        return True
        
    def find_dockerfiles(self, folder: Path) -> List[Dict[str, str]]:
        """Find all Dockerfiles in a folder and return info about them"""
        dockerfiles = []
        full_folder = self.root_path / folder
        
        # Look for all files starting with "Dockerfile"
        for file in full_folder.glob("Dockerfile*"):
            if file.is_file():
                dockerfile_info = {
                    'path': str(folder / file.name),
                    'name': file.name
                }
                
                # Determine the container name based on Dockerfile name
                if file.name == "Dockerfile":
                    dockerfile_info['suffix'] = ''
                else:
                    # Extract suffix (e.g., "sidecar" from "Dockerfile.sidecar")
                    dockerfile_info['suffix'] = file.name.replace("Dockerfile.", "")
                    
                dockerfiles.append(dockerfile_info)
                
        return dockerfiles
        
    def find_app_yaml(self, folder: Path) -> Optional[str]:
        """Check if app.yaml or app.yml exists in folder"""
        full_folder = self.root_path / folder
        
        for config_name in ['app.yaml', 'app.yml']:
            config_path = full_folder / config_name
            if config_path.exists():
                return str(folder / config_name)
                
        return None
        
    def analyze_deletions(self) -> Dict[str, Any]:
        """Analyze deleted files to determine what cleanup is needed"""
        deletions = {
            'apps': [],  # Apps that need terraform destroy
            'containers': [],  # Container images that need ACR cleanup
        }
        
        # Group deletions by folder
        deleted_by_folder: Dict[Path, Dict[str, List[Path]]] = {}
        
        for file_path in self.deleted_files:
            if not self.should_include_path(file_path):
                continue
                
            folder = file_path.parent
            if folder not in deleted_by_folder:
                deleted_by_folder[folder] = {
                    'dockerfiles': [],
                    'app_configs': [],
                    'other_files': []
                }
                
            filename = file_path.name
            if filename.startswith('Dockerfile'):
                deleted_by_folder[folder]['dockerfiles'].append(file_path)
            elif filename in ['app.yaml', 'app.yml']:
                deleted_by_folder[folder]['app_configs'].append(file_path)
            else:
                deleted_by_folder[folder]['other_files'].append(file_path)
                
        # Process deletions
        for folder_path, deleted_items in deleted_by_folder.items():
            app_name = folder_path.name
            
            # Check if the folder itself was deleted
            if not (self.root_path / folder_path).exists():
                # Folder was deleted - add to deleted_apps
                deletions['apps'].append({
                    'path': str(folder_path),
                    'app_name': app_name,
                    'deleted_config': 'folder_deleted'
                })
                
                # Also need to determine what containers were in this folder
                # Since the folder is gone, we need to infer from deleted files
                for dockerfile in deleted_items['dockerfiles']:
                    dockerfile_name = dockerfile.name
                    if dockerfile_name == 'Dockerfile':
                        container_name = app_name
                    else:
                        suffix = dockerfile_name.replace('Dockerfile.', '')
                        container_name = f"{app_name}-{suffix}"
                        
                    deletions['containers'].append({
                        'app_name': app_name,
                        'container_name': container_name,
                        'dockerfile': str(dockerfile),
                        'image_name': container_name
                    })
            else:
                # Folder still exists - handle partial deletions
                # If app.yaml was deleted, the app needs to be destroyed
                if deleted_items['app_configs']:
                    deletions['apps'].append({
                        'path': str(folder_path),
                        'app_name': app_name,
                        'deleted_config': str(deleted_items['app_configs'][0])
                    })
                    
                # Track deleted containers (Dockerfiles)
                for dockerfile in deleted_items['dockerfiles']:
                    dockerfile_name = dockerfile.name
                    if dockerfile_name == 'Dockerfile':
                        container_name = app_name
                    else:
                        suffix = dockerfile_name.replace('Dockerfile.', '')
                        container_name = f"{app_name}-{suffix}"
                        
                    deletions['containers'].append({
                        'app_name': app_name,
                        'container_name': container_name,
                        'dockerfile': str(dockerfile),
                        'image_name': container_name
                    })
                
        return deletions
        
    def analyze_folder(self, folder: Path, changed_files: Set[Path]) -> Optional[Dict]:
        """Analyze a folder for Dockerfiles and optionally app configuration"""
        dockerfiles = self.find_dockerfiles(folder)
        app_config = self.find_app_yaml(folder)
        
        # Determine if we should include this folder based on mode
        if self.require_app_config:
            # Container Apps mode: need either app.yaml or Dockerfiles
            if not app_config and not dockerfiles:
                return None
        else:
            # Docker build mode: only need Dockerfiles
            if not dockerfiles:
                return None
            
        # Use folder name as app name
        app_name = folder.name
            
        return {
            'path': str(folder),
            'app_name': app_name,
            'app_config': app_config,  # Can be None
            'dockerfiles': dockerfiles,  # Can be empty if require_app_config=True
            'changed_files': [str(f) for f in changed_files]
        }
        
    def find_app_folders(self) -> Dict[str, Any]:
        """Find folders containing changed files and analyze them"""
        self.changed_files, self.deleted_files, self.renamed_files = self.get_changed_files()
        
        # Group files by their parent directories
        changed_folders: Dict[Path, Set[Path]] = {}
        
        for file_path in self.changed_files:
            if self.should_include_path(file_path):
                folder = file_path.parent
                if folder not in changed_folders:
                    changed_folders[folder] = set()
                changed_folders[folder].add(file_path)
                
        # Analyze each folder
        apps = {}
        for folder, files in changed_folders.items():
            app_info = self.analyze_folder(folder, files)
            if app_info:
                apps[folder] = app_info
                
        # Analyze deletions
        deletions = self.analyze_deletions()
                
        return {
            'apps': apps,
            'deletions': deletions,
            'ref': self.get_comparison_ref()
        }
        
    def analyze_all_apps(self) -> List[Dict]:
        """Analyze all apps in the include pattern, regardless of changes"""
        all_apps = []
        
        # If we have an include pattern like "apps/*", we need to find matching directories
        if self.include_pattern:
            # Convert glob pattern to find directories
            # For pattern like "apps/*", we want to find all direct subdirectories of "apps"
            pattern_parts = self.include_pattern.split('/')
            
            if '*' in pattern_parts[-1]:
                # Pattern ends with *, so we want directories at this level
                parent_path = '/'.join(pattern_parts[:-1]) if len(pattern_parts) > 1 else '.'
                parent_dir = self.root_path / parent_path
                
                if parent_dir.exists() and parent_dir.is_dir():
                    # Find all subdirectories
                    for path in parent_dir.iterdir():
                        if path.is_dir():
                            relative_path = path.relative_to(self.root_path)
                            if self.should_include_path(relative_path):
                                app_info = self.analyze_folder(relative_path, set())
                                if app_info:
                                    all_apps.append({
                                        'path': app_info['path'],
                                        'app_name': app_info['app_name'],
                                        'dockerfiles': app_info['dockerfiles'],
                                        'app_config': app_info['app_config']
                                    })
            else:
                # Pattern is a specific directory
                specific_dir = self.root_path / self.include_pattern
                if specific_dir.exists() and specific_dir.is_dir():
                    relative_path = specific_dir.relative_to(self.root_path)
                    app_info = self.analyze_folder(relative_path, set())
                    if app_info:
                        all_apps.append({
                            'path': app_info['path'],
                            'app_name': app_info['app_name'],
                            'dockerfiles': app_info['dockerfiles'],
                            'app_config': app_info['app_config']
                        })
        else:
            # No include pattern, check all directories at root level
            for path in self.root_path.iterdir():
                if path.is_dir() and not path.name.startswith('.'):
                    relative_path = path.relative_to(self.root_path)
                    if self.should_include_path(relative_path):
                        app_info = self.analyze_folder(relative_path, set())
                        if app_info:
                            all_apps.append({
                                'path': app_info['path'],
                                'app_name': app_info['app_name'],
                                'dockerfiles': app_info['dockerfiles'],
                                'app_config': app_info['app_config']
                            })
                
        return all_apps
        
    def generate_matrix_output(self) -> Dict:
        """Generate output suitable for GitHub Actions matrix"""
        analysis = self.find_app_folders()
        
        # Generate matrix items - one per app
        matrix_items = []
        for folder, app_info in analysis['apps'].items():
            item = {
                'path': app_info['path'],
                'app_name': app_info['app_name'],
                'dockerfiles': app_info['dockerfiles']  # Can be empty for pre-built only apps
            }
            if app_info['app_config']:
                item['app_config'] = app_info['app_config']
                
            matrix_items.append(item)
        
        # Also generate all_apps for workflow_dispatch scenarios
        all_apps = self.analyze_all_apps()
                
        return {
            'matrix': {
                'include': matrix_items
            },
            'all_apps': {
                'include': all_apps
            },
            'deletions': analysis['deletions'],
            'ref': analysis['ref'],
            'has_changes': len(matrix_items) > 0,
            'has_deletions': any(analysis['deletions'].values())
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Analyze git changes for build scope')
    parser.add_argument('--root-path', default=os.environ.get('GITHUB_WORKSPACE', '.'),
                        help='Root path to search for changes')
    parser.add_argument('--include-pattern', help='Pattern for paths to include')
    parser.add_argument('--exclude-pattern', help='Pattern for paths to exclude')
    parser.add_argument('--ref', help='Git ref to compare against')
    parser.add_argument('--output-format', choices=['json', 'github'], default='github',
                        help='Output format')
    parser.add_argument('--require-app-config', action='store_true',
                        help='Require app.yaml/app.yml for Container Apps mode')
    
    args = parser.parse_args()
    
    analyzer = BuildScopeAnalyzer(
        root_path=args.root_path,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern,
        require_app_config=args.require_app_config
    )
    
    output = analyzer.generate_matrix_output()
    
    if args.output_format == 'github':
        # Output in GitHub Actions format
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"matrix={json.dumps(output['matrix'])}\n")
                f.write(f"all_apps={json.dumps(output['all_apps'])}\n")
                f.write(f"deletions={json.dumps(output['deletions'])}\n")
                f.write(f"ref={output['ref']}\n")
                f.write(f"has_changes={str(output['has_changes']).lower()}\n")
                f.write(f"has_deletions={str(output['has_deletions']).lower()}\n")
                
                # Also output specific deletion types for easier consumption
                f.write(f"deleted_apps={json.dumps(output['deletions']['apps'])}\n")
                f.write(f"deleted_containers={json.dumps(output['deletions']['containers'])}\n")
        else:
            # Fallback to console output for testing
            print(f"matrix={json.dumps(output['matrix'])}")
            print(f"all_apps={json.dumps(output['all_apps'])}")
            print(f"deletions={json.dumps(output['deletions'])}")
            print(f"ref={output['ref']}")
            print(f"has_changes={str(output['has_changes']).lower()}")
            print(f"has_deletions={str(output['has_deletions']).lower()}")
            print(f"deleted_apps={json.dumps(output['deletions']['apps'])}")
            print(f"deleted_containers={json.dumps(output['deletions']['containers'])}")
    else:
        # Output as JSON
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main() 