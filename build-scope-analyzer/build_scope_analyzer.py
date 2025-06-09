#!/usr/bin/env python3
"""
Build Scope Analyzer - Analyze git changes and generate strategy matrix for GitHub Actions

This script analyzes git diff to identify what needs to be built and generates
output suitable for GitHub Actions strategy matrix.
"""

import os
import sys
import json
import yaml
import subprocess
import argparse
import fnmatch
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple


class BuildScopeAnalyzer:
    """Analyzes git changes and generates strategy matrix output"""
    
    def __init__(self, root_path: str, include_pattern: str = '', exclude_pattern: str = ''):
        self.root_path = Path(root_path).resolve()
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
        self.changed_files: Set[Path] = set()
        self.deleted_files: Set[Path] = set()
        
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
        else:
            # For push events, compare against previous commit
            return "HEAD~1"
            
    def get_changed_files(self) -> Tuple[Set[Path], Set[Path]]:
        """Get list of changed and deleted files from git diff"""
        ref = self.get_comparison_ref()
        
        # Get changed files
        diff_output = self.run_git_command(['git', 'diff', '--name-only', ref])
        changed = set()
        for line in diff_output.splitlines():
            if line:
                changed.add(Path(line))
                
        # Get deleted files
        diff_deleted = self.run_git_command(['git', 'diff', '--diff-filter=D', '--name-only', ref])
        deleted = set()
        for line in diff_deleted.splitlines():
            if line:
                deleted.add(Path(line))
                
        return changed, deleted
        
    def should_include_path(self, path: Path) -> bool:
        """Check if path should be included based on patterns"""
        path_str = str(path)
        
        if self.include_pattern and self.exclude_pattern:
            raise ValueError("Cannot specify both include and exclude patterns")
            
        if self.include_pattern:
            return fnmatch.fnmatch(path_str, self.include_pattern)
            
        if self.exclude_pattern:
            return not fnmatch.fnmatch(path_str, self.exclude_pattern)
            
        return True
        
    def find_app_folders(self) -> Dict[Path, Dict]:
        """Find folders containing changed files and analyze them"""
        self.changed_files, self.deleted_files = self.get_changed_files()
        
        # Group files by their parent directories
        changed_folders: Dict[Path, Set[Path]] = {}
        deleted_folders: Set[Path] = set()
        
        for file_path in self.changed_files:
            if self.should_include_path(file_path):
                folder = file_path.parent
                if folder not in changed_folders:
                    changed_folders[folder] = set()
                changed_folders[folder].add(file_path)
                
        for file_path in self.deleted_files:
            if self.should_include_path(file_path):
                deleted_folders.add(file_path.parent)
                
        # Analyze each folder
        apps = {}
        for folder, files in changed_folders.items():
            app_info = self.analyze_folder(folder, files)
            if app_info:
                apps[folder] = app_info
                
        return {
            'apps': apps,
            'deleted_folders': list(str(f) for f in deleted_folders),
            'ref': self.get_comparison_ref()
        }
        
    def analyze_folder(self, folder: Path, changed_files: Set[Path]) -> Optional[Dict]:
        """Analyze a folder for app configuration and Docker files"""
        full_folder = self.root_path / folder
        
        # Look for app.yml or app.yaml
        app_config_path = None
        app_config = None
        for config_name in ['app.yml', 'app.yaml']:
            config_path = full_folder / config_name
            if config_path.exists():
                app_config_path = folder / config_name
                try:
                    with open(config_path, 'r') as f:
                        app_config = yaml.safe_load(f)
                except Exception as e:
                    print(f"Warning: Failed to parse {config_path}: {e}", file=sys.stderr)
                break
                
        # Look for Dockerfile
        dockerfile_path = None
        dockerfile_full = full_folder / 'Dockerfile'
        if dockerfile_full.exists():
            dockerfile_path = folder / 'Dockerfile'
            
        # Skip folders without app config or Dockerfile
        if not app_config_path and not dockerfile_path:
            return None
            
        # Extract app name
        app_name = None
        if app_config and isinstance(app_config, dict):
            # Try to find app name in config
            app_name = app_config.get('name')
            if not app_name:
                # Try to find primary source name
                template = app_config.get('template', {})
                containers = template.get('containers', [])
                if containers and isinstance(containers, list):
                    app_name = containers[0].get('name')
                    
        # Fallback to folder basename
        if not app_name:
            app_name = folder.name
            
        return {
            'path': str(folder),
            'app_name': app_name,
            'app_config': str(app_config_path) if app_config_path else None,
            'dockerfile': str(dockerfile_path) if dockerfile_path else None,
            'changed_files': [str(f) for f in changed_files]
        }
        
    def generate_docker_tags(self, app_info: Dict) -> List[str]:
        """Generate Docker tags for an app"""
        tags = []
        
        # Basic tags based on git context
        sha = os.environ.get('GITHUB_SHA', 'latest')[:7]
        ref_name = os.environ.get('GITHUB_REF_NAME', 'main')
        
        # Add SHA tag
        tags.append(sha)
        
        # Add branch/tag based tags
        if ref_name:
            # Clean ref name for use as Docker tag
            clean_ref = ref_name.replace('/', '-').replace('_', '-')
            tags.append(clean_ref)
            
            # If it's main/master, also tag as latest
            if ref_name in ['main', 'master']:
                tags.append('latest')
                
        # Add timestamp tag
        import datetime
        timestamp = datetime.datetime.utcnow().strftime('%Y%m%d-%H%M%S')
        tags.append(timestamp)
        
        return tags
        
    def generate_matrix_output(self) -> Dict:
        """Generate output suitable for GitHub Actions matrix"""
        analysis = self.find_app_folders()
        
        matrix_items = []
        for folder, app_info in analysis['apps'].items():
            if app_info['dockerfile']:  # Only include apps with Dockerfiles
                item = {
                    'path': app_info['path'],
                    'app_name': app_info['app_name'],
                    'dockerfile': app_info['dockerfile']
                }
                if app_info['app_config']:
                    item['app_config'] = app_info['app_config']
                    
                matrix_items.append(item)
                
        return {
            'matrix': {
                'include': matrix_items
            },
            'deleted_folders': analysis['deleted_folders'],
            'ref': analysis['ref'],
            'has_changes': len(matrix_items) > 0
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
    
    args = parser.parse_args()
    
    # Validate pattern arguments
    if args.include_pattern and args.exclude_pattern:
        parser.error("Cannot specify both --include-pattern and --exclude-pattern")
    
    analyzer = BuildScopeAnalyzer(
        root_path=args.root_path,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern
    )
    
    output = analyzer.generate_matrix_output()
    
    if args.output_format == 'github':
        # Output in GitHub Actions format (using new format)
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                f.write(f"matrix={json.dumps(output['matrix'])}\n")
                f.write(f"deleted_folders={json.dumps(output['deleted_folders'])}\n")
                f.write(f"ref={output['ref']}\n")
                f.write(f"has_changes={str(output['has_changes']).lower()}\n")
        else:
            # Fallback to console output for testing
            print(f"matrix={json.dumps(output['matrix'])}")
            print(f"deleted_folders={json.dumps(output['deleted_folders'])}")
            print(f"ref={output['ref']}")
            print(f"has_changes={str(output['has_changes']).lower()}")
    else:
        # Output as JSON
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main() 