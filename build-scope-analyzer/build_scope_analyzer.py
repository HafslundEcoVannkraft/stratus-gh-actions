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
import yaml
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple, Any


class BuildScopeAnalyzer:
    """Analyzes git changes and generates strategy matrix output"""

    def __init__(self, root_path: str, include_pattern: str = '', exclude_pattern: str = ''):
        self.root_path = Path(root_path).resolve()
        self.include_pattern = include_pattern
        self.exclude_pattern = exclude_pattern
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

    def get_comparison_ref(self) -> Tuple[str, Optional[str]]:
        """Determine the reference to compare against and resolve its commit SHA

        Returns:
            Tuple containing:
                - ref_name: String with the reference name (e.g., "HEAD~1", "origin/main")
                - commit_sha: String with the resolved commit SHA, or None if no ref
        """
        event_type = self.get_event_type()

        if event_type == 'pull_request':
            # For PRs, compare against the base branch
            base_ref = os.environ.get('GITHUB_BASE_REF', 'main')
            ref_name = f"origin/{base_ref}"
            try:
                # Resolve the commit SHA
                commit_sha = self.run_git_command(['git', 'rev-parse', ref_name])
                return ref_name, commit_sha
            except:
                return ref_name, None
        elif event_type == 'workflow_dispatch':
            # For workflow_dispatch, we don't need to compare against anything
            # since we'll use all_apps output anyway
            return "", None
        else:
            # For push events, compare against previous commit
            ref_name = "HEAD~1"
            try:
                # Resolve the commit SHA
                commit_sha = self.run_git_command(['git', 'rev-parse', ref_name])
                return ref_name, commit_sha
            except:
                return ref_name, None

    def get_changed_files(self) -> Tuple[Set[Path], Set[Path], Dict[Path, Path]]:
        """Get list of changed, deleted, and renamed files from git diff"""
        ref_name, commit_sha = self.get_comparison_ref()

        # If ref is empty (workflow_dispatch), return empty sets
        if not ref_name:
            return set(), set(), {}

        # Get all changes with status
        diff_output = self.run_git_command(['git', 'diff', '--name-status', ref_name])

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
                # For consistent structure with apps.all and apps.updated, construct the expected app.yaml path
                yaml_path = str(folder_path / 'app.yaml')  # Default to app.yaml path
                # Check if we had app.yaml or app.yml in the deleted files
                for app_config in deleted_items['app_configs']:
                    yaml_path = str(app_config)
                    break

                deletions['apps'].append({
                    'path': str(folder_path),
                    'app_name': app_name,
                    'app_config': yaml_path
                })

                # Also need to determine what containers were in this folder
                # Since the folder is gone, we need to infer from deleted files
                for dockerfile in deleted_items['dockerfiles']:
                    dockerfile_name = dockerfile.name
                    # Create a dockerfile dict similar to what other methods use
                    dockerfile_dict = {'name': dockerfile_name}
                    if dockerfile_name == 'Dockerfile':
                        dockerfile_dict['suffix'] = ''
                    else:
                        dockerfile_dict['suffix'] = dockerfile_name.replace('Dockerfile.', '')

                    # Try to find app.yaml/app.yml in the deleted files to get app name
                    app_config_path = None
                    for app_config in deleted_items['app_configs']:
                        app_config_path = str(app_config)
                        break

                    # Use our standard method for consistent container naming
                    container_name = self.get_container_name(app_name, dockerfile_dict, app_config_path)

                    deletions['containers'].append({
                        'app_name': app_name,
                        'container_name': container_name,
                        'dockerfile': str(dockerfile)
                    })
            else:
                # Folder still exists - handle partial deletions
                # If app.yaml was deleted, the app needs to be destroyed
                if deleted_items['app_configs']:
                    deletions['apps'].append({
                        'path': str(folder_path),
                        'app_name': app_name,
                        'app_config': str(deleted_items['app_configs'][0])  # Consistent with apps.all and apps.updated
                    })

                # Track deleted containers (Dockerfiles)
                for dockerfile in deleted_items['dockerfiles']:
                    dockerfile_name = dockerfile.name
                    # Create a dockerfile dict similar to what other methods use
                    dockerfile_dict = {'name': dockerfile_name}
                    if dockerfile_name == 'Dockerfile':
                        dockerfile_dict['suffix'] = ''
                    else:
                        dockerfile_dict['suffix'] = dockerfile_name.replace('Dockerfile.', '')

                    # Find app.yaml or app.yml in the deleted files
                    app_config_path = None
                    for app_config in deleted_items['app_configs']:
                        app_config_path = str(app_config)
                        break

                    # If the folder wasn't deleted, check if app.yaml/app.yml still exists
                    if not app_config_path:
                        potential_app_yaml = self.find_app_yaml(folder_path)
                        if potential_app_yaml:
                            app_config_path = potential_app_yaml

                    # Use our standard method for consistent container naming
                    container_name = self.get_container_name(app_name, dockerfile_dict, app_config_path)

                    deletions['containers'].append({
                        'app_name': app_name,
                        'container_name': container_name,
                        'dockerfile': str(dockerfile)
                    })

        return deletions

    def analyze_folder(self, folder: Path, changed_files: Set[Path]) -> Optional[Dict]:
        """Analyze a folder for Dockerfiles and optionally app configuration"""
        dockerfiles = self.find_dockerfiles(folder)
        app_config = self.find_app_yaml(folder)

        # Only include folders with at least a Dockerfile or app.yaml/app.yml
        if not app_config and not dockerfiles:
            return None

        # Use folder name as app name
        app_name = folder.name

        return {
            'path': str(folder),
            'app_name': app_name,
            'app_config': app_config,  # Can be None
            'dockerfiles': dockerfiles,  # Can be empty
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

        # Get comparison ref and commit SHA
        ref_name, commit_sha = self.get_comparison_ref()

        # Analyze deletions
        deletions = self.analyze_deletions()

        return {
            'apps': apps,
            'deletions': deletions,
            'ref': ref_name,
            'commit_sha': commit_sha
        }

    def analyze_all_builds(self) -> List[Dict]:
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
                                    # Use the same structure as the main matrix
                                    item = {
                                        'path': app_info['path'],
                                        'app_name': app_info['app_name'],
                                        'dockerfiles': app_info['dockerfiles']
                                    }
                                    if app_info['app_config']:
                                        item['app_config'] = app_info['app_config']
                                    all_apps.append(item)
            else:
                # Pattern is a specific directory
                specific_dir = self.root_path / self.include_pattern
                if specific_dir.exists() and specific_dir.is_dir():
                    relative_path = specific_dir.relative_to(self.root_path)
                    app_info = self.analyze_folder(relative_path, set())
                    if app_info:
                        # Use the same structure as the main matrix
                        item = {
                            'path': app_info['path'],
                            'app_name': app_info['app_name'],
                            'dockerfiles': app_info['dockerfiles']
                        }
                        if app_info['app_config']:
                            item['app_config'] = app_info['app_config']
                        all_apps.append(item)
        else:
            # No include pattern, check all directories at root level
            for path in self.root_path.iterdir():
                if path.is_dir() and not path.name.startswith('.'):
                    relative_path = path.relative_to(self.root_path)
                    if self.should_include_path(relative_path):
                        app_info = self.analyze_folder(relative_path, set())
                        if app_info:
                            # Use the same structure as the main matrix
                            item = {
                                'path': app_info['path'],
                                'app_name': app_info['app_name'],
                                'dockerfiles': app_info['dockerfiles']
                            }
                            if app_info['app_config']:
                                item['app_config'] = app_info['app_config']
                            all_apps.append(item)

        return all_apps

    def generate_matrix_output(self) -> Dict:
        """Generate output suitable for GitHub Actions matrix"""
        analysis = self.find_app_folders()
        changed_files = self.changed_files
        renamed_files = self.renamed_files

        # Helper to check if a folder is only renamed (no real file changes)
        def is_only_renamed(folder: Path) -> bool:
            # If all files in this folder are only in renamed_files, and not in changed_files
            for old, new in renamed_files.items():
                if new.parent == folder or old.parent == folder:
                    # If the file is not in changed_files, it's only renamed
                    if new not in changed_files and old not in changed_files:
                        continue
                    else:
                        return False
            return True if renamed_files else False

        # Process changed apps
        updated_apps = []  # Folders with app.yaml/app.yml
        container_items = []  # Folders with Dockerfiles

        for folder, app_info in analysis['apps'].items():
            folder_path = Path(app_info['path'])
            # Only include if any file in folder or subfolders is changed and not just renamed
            if app_info['app_config']:
                if self.folder_has_changes(folder_path, changed_files) and not is_only_renamed(folder_path):
                    app_item = {
                        'path': app_info['path'],
                        'app_name': app_info['app_name'],
                        'app_config': app_info['app_config']
                    }
                    updated_apps.append(app_item)

            # Handle Dockerfiles (containers matrix)
            if app_info['dockerfiles'] and len(app_info['dockerfiles']) > 0:
                for dockerfile in app_info['dockerfiles']:
                    if self.folder_has_changes(folder_path, changed_files) and not is_only_renamed(folder_path):
                        container_name = self.get_container_name(app_info['app_name'], dockerfile, app_info['app_config'])
                        context = self.get_dockerfile_context(dockerfile['path'], app_info['path'])
                        suffix = dockerfile.get('suffix', '')
                        container_item = {
                            'path': app_info['path'],
                            'context': context,
                            'app_name': app_info['app_name'],
                            'dockerfile': dockerfile,
                            'container_name': container_name
                        }
                        container_items.append(container_item)

        # Process all apps (for workflow_dispatch scenarios)
        all_builds = self.analyze_all_builds()

        # Split into app configs and containers
        all_apps = []  # All folders with app.yaml/app.yml
        all_containers = []  # All Dockerfiles

        for app in all_builds:
            if app.get('app_config'):
                app_item = {
                    'path': app['path'],
                    'app_name': app['app_name'],
                    'app_config': app['app_config']
                }
                all_apps.append(app_item)
            if app.get('dockerfiles') and len(app['dockerfiles']) > 0:
                for dockerfile in app['dockerfiles']:
                    container_name = self.get_container_name(app['app_name'], dockerfile, app.get('app_config'))
                    context = self.get_dockerfile_context(dockerfile['path'], app['path'])
                    suffix = dockerfile.get('suffix', '')
                    container_item = {
                        'path': app['path'],
                        'context': context,
                        'app_name': app['app_name'],
                        'dockerfile': dockerfile,
                        'container_name': container_name
                    }
                    all_containers.append(container_item)

        # Check if there are updated or deleted apps/containers
        has_app_updates = len(updated_apps) > 0
        has_app_deletions = len(analysis['deletions']['apps']) > 0
        has_container_updates = len(container_items) > 0
        has_container_deletions = len(analysis['deletions']['containers']) > 0

        # Get the commit SHA for deleted items
        commit_sha = analysis.get('commit_sha')

        # Add commit SHA to each deleted app and container if available
        deleted_apps = analysis['deletions']['apps']
        deleted_containers = analysis['deletions']['containers']

        if commit_sha:
            # Add to deleted apps
            for app in deleted_apps:
                app['commit_sha'] = commit_sha

            # Add to deleted containers
            for container in deleted_containers:
                container['commit_sha'] = commit_sha

        # Create the clean, focused return object
        return {
            'apps': {
                'updated': updated_apps,  # Folders with app.yaml/app.yml that changed
                'all': all_apps,       # All folders with app.yaml/app.yml
                'deleted': deleted_apps,  # Deleted app.yaml/app.yml files
                'has_updates': has_app_updates,
                'has_deletions': has_app_deletions
            },
            'containers': {
                'updated': container_items,  # Changed Dockerfiles
                'all': all_containers,       # All Dockerfiles
                'deleted': analysis['deletions']['containers'],  # Deleted Dockerfiles
                'has_updates': has_container_updates,
                'has_deletions': has_container_deletions
            },
            'ref': analysis['ref']
        }

    def folder_has_changes(self, folder: Path, changed_files: Set[Path]) -> bool:
        """Check if any file in folder or its subfolders is in changed_files"""
        folder_abs = (self.root_path / folder).resolve()
        for changed_file in changed_files:
            changed_abs = (self.root_path / changed_file).resolve()
            try:
                changed_abs.relative_to(folder_abs)
                return True
            except ValueError:
                continue
        return False

    def get_app_name_from_yaml(self, app_yaml_path: Optional[str]) -> Optional[str]:
        """Extract the 'name' property from app.yaml/app.yml if present"""
        if not app_yaml_path:
            return None
        try:
            with open(self.root_path / app_yaml_path, 'r') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict) and 'name' in data:
                    return str(data['name'])
        except Exception:
            pass
        return None

    def get_dockerfile_context(self, dockerfile_path: str, default_context: str) -> str:
        """Read the Dockerfile and extract a custom context if specified via # @context: ..."""
        try:
            with open(self.root_path / dockerfile_path, 'r') as f:
                for _ in range(10):
                    line = f.readline()
                    if not line:
                        break
                    if line.strip().startswith('# @context:'):
                        return line.strip().split(':', 1)[1].strip()
        except Exception:
            pass
        return default_context

    def get_container_name(self, app_name: str, dockerfile: Dict[str, str], app_config: Optional[str] = None) -> str:
        # Try to get name from app.yaml/app.yml first if available
        base_name = self.get_app_name_from_yaml(app_config) or app_name
        suffix = dockerfile.get('suffix', '')
        container_name = base_name if not suffix else f"{base_name}-{suffix}"
        # Ensure container name is lowercase for Azure Container Registry compatibility
        return container_name.lower()


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

    analyzer = BuildScopeAnalyzer(
        root_path=args.root_path,
        include_pattern=args.include_pattern,
        exclude_pattern=args.exclude_pattern
    )

    output = analyzer.generate_matrix_output()

    if args.output_format == 'github':
        # Output in GitHub Actions format
        github_output = os.environ.get('GITHUB_OUTPUT')
        if github_output:
            with open(github_output, 'a') as f:
                # Output the full matrix object
                f.write(f"matrix={json.dumps(output)}\n")
                # Output the reference information
                f.write(f"ref={output['ref']}\n")
        else:
            # Fallback to console output for testing
            print(f"matrix={json.dumps(output)}")
            print(f"ref={output['ref']}")
    else:
        # Output as JSON
        print(json.dumps(output, indent=2))


if __name__ == '__main__':
    main()