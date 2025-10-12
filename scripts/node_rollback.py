#!/usr/bin/env python3
"""
ComfyUI Custom Nodes Rollback Manager
Manages safe rollback of problematic custom node additions
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse
import tempfile

@dataclass
class NodeState:
    """State information for a custom node"""
    name: str
    url: str
    path: str
    commit_hash: Optional[str] = None
    branch: Optional[str] = None
    timestamp: str = ""
    is_active: bool = True
    backup_path: Optional[str] = None
    size_mb: float = 0.0
    file_count: int = 0

@dataclass
class RollbackPoint:
    """A rollback point containing multiple node states"""
    id: str
    timestamp: str
    description: str
    nodes: List[NodeState]
    custom_nodes_content: str  # Content of custom_nodes.txt at this point

class RollbackManager:
    """Manages rollback functionality for custom nodes"""

    def __init__(self,
                 custom_nodes_dir: str = "/workspace/ComfyUI/custom_nodes",
                 state_file: str = "/tmp/custom_nodes_state.json",
                 backup_dir: str = "/tmp/custom_nodes_backups"):
        self.custom_nodes_dir = Path(custom_nodes_dir)
        self.state_file = Path(state_file)
        self.backup_dir = Path(backup_dir)
        self.custom_nodes_file = self.custom_nodes_dir.parent / "custom_nodes.txt"

        # Ensure directories exist
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def load_state(self) -> Dict[str, RollbackPoint]:
        """Load rollback state from file"""
        if not self.state_file.exists():
            return {}

        try:
            with open(self.state_file, 'r') as f:
                data = json.load(f)

            rollback_points = {}
            for rp_id, rp_data in data.items():
                nodes = []
                for node_data in rp_data.get('nodes', []):
                    nodes.append(NodeState(**node_data))

                rollback_points[rp_id] = RollbackPoint(
                    id=rp_data['id'],
                    timestamp=rp_data['timestamp'],
                    description=rp_data['description'],
                    nodes=nodes,
                    custom_nodes_content=rp_data['custom_nodes_content']
                )

            return rollback_points
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            return {}

    def save_state(self, rollback_points: Dict[str, RollbackPoint]):
        """Save rollback state to file"""
        try:
            data = {}
            for rp_id, rollback_point in rollback_points.items():
                nodes_data = [asdict(node) for node in rollback_point.nodes]
                data[rp_id] = {
                    'id': rollback_point.id,
                    'timestamp': rollback_point.timestamp,
                    'description': rollback_point.description,
                    'nodes': nodes_data,
                    'custom_nodes_content': rollback_point.custom_nodes_content
                }

            with open(self.state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving state file: {e}")

    def get_current_nodes(self) -> List[NodeState]:
        """Get current state of all custom nodes"""
        nodes = []

        if not self.custom_nodes_dir.exists():
            return nodes

        # Read custom_nodes.txt to get URLs
        urls = []
        if self.custom_nodes_file.exists():
            with open(self.custom_nodes_file, 'r') as f:
                urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        url_to_name = {}
        for url in urls:
            name = Path(url).stem.replace('ComfyUI-', '').replace('comfyui-', '')
            url_to_name[name] = url

        # Scan the custom_nodes directory
        for node_path in self.custom_nodes_dir.iterdir():
            if not node_path.is_dir() or node_path.name.startswith('.'):
                continue

            name = node_path.name
            url = url_to_name.get(name, "")

            # Get git information
            commit_hash = None
            branch = None
            try:
                if (node_path / '.git').exists():
                    result = subprocess.run(
                        ['git', 'rev-parse', 'HEAD'],
                        cwd=node_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        commit_hash = result.stdout.strip()

                    result = subprocess.run(
                        ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                        cwd=node_path,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        branch = result.stdout.strip()
            except:
                pass

            # Calculate size and file count
            size_mb = 0.0
            file_count = 0
            try:
                for file_path in node_path.rglob('*'):
                    if file_path.is_file():
                        file_count += 1
                        size_mb += file_path.stat().st_size / (1024 * 1024)
            except:
                pass

            nodes.append(NodeState(
                name=name,
                url=url,
                path=str(node_path),
                commit_hash=commit_hash,
                branch=branch,
                timestamp=datetime.now().isoformat(),
                is_active=True,
                size_mb=size_mb,
                file_count=file_count
            ))

        return nodes

    def create_backup(self, nodes: List[NodeState]) -> str:
        """Create a backup of the specified nodes"""
        backup_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / backup_id
        backup_path.mkdir(exist_ok=True)

        for node in nodes:
            if not os.path.exists(node.path):
                continue

            node_backup_path = backup_path / node.name
            try:
                # Copy the entire node directory
                if node_backup_path.exists():
                    shutil.rmtree(node_backup_path)
                shutil.copytree(node.path, node_backup_path)
                node.backup_path = str(node_backup_path)
            except Exception as e:
                print(f"Warning: Could not backup {node.name}: {e}")

        return str(backup_path)

    def create_rollback_point(self, description: str) -> str:
        """Create a new rollback point"""
        print(f"📦 Creating rollback point: {description}")

        # Get current nodes
        current_nodes = self.get_current_nodes()

        # Read current custom_nodes.txt content
        custom_nodes_content = ""
        if self.custom_nodes_file.exists():
            with open(self.custom_nodes_file, 'r') as f:
                custom_nodes_content = f.read()

        # Create backup
        backup_path = self.create_backup(current_nodes)

        # Generate rollback point ID
        rollback_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create rollback point
        rollback_point = RollbackPoint(
            id=rollback_id,
            timestamp=datetime.now().isoformat(),
            description=description,
            nodes=current_nodes,
            custom_nodes_content=custom_nodes_content
        )

        # Load existing state
        rollback_points = self.load_state()
        rollback_points[rollback_id] = rollback_point

        # Keep only last 10 rollback points
        if len(rollback_points) > 10:
            sorted_points = sorted(rollback_points.items(), key=lambda x: x[1].timestamp)
            for old_id, old_point in sorted_points[:-10]:
                # Remove old backup directory
                try:
                    for node in old_point.nodes:
                        if node.backup_path and os.path.exists(node.backup_path):
                            shutil.rmtree(node.backup_path)
                except:
                    pass
                del rollback_points[old_id]

        # Save state
        self.save_state(rollback_points)

        print(f"✅ Rollback point created: {rollback_id}")
        print(f"   Backup location: {backup_path}")
        print(f"   Nodes backed up: {len(current_nodes)}")

        return rollback_id

    def rollback_to_point(self, rollback_id: str, dry_run: bool = False) -> bool:
        """Rollback to a specific rollback point"""
        rollback_points = self.load_state()

        if rollback_id not in rollback_points:
            print(f"❌ Rollback point not found: {rollback_id}")
            return False

        rollback_point = rollback_points[rollback_id]
        print(f"🔄 Rolling back to: {rollback_point.description}")
        print(f"   Timestamp: {rollback_point.timestamp}")
        print(f"   Nodes to restore: {len(rollback_point.nodes)}")

        if dry_run:
            print("🔍 DRY RUN - No changes will be made")
            for node in rollback_point.nodes:
                print(f"   Would restore: {node.name} ({node.url})")
            return True

        # Create current state backup before rollback
        current_backup_id = self.create_rollback_point(f"Before rollback to {rollback_id}")

        try:
            # Remove existing custom nodes
            if self.custom_nodes_dir.exists():
                for item in self.custom_nodes_dir.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        try:
                            shutil.rmtree(item)
                        except Exception as e:
                            print(f"Warning: Could not remove {item}: {e}")

            # Restore custom_nodes.txt
            with open(self.custom_nodes_file, 'w') as f:
                f.write(rollback_point.custom_nodes_content)

            # Restore nodes from backup
            for node in rollback_point.nodes:
                if node.backup_path and os.path.exists(node.backup_path):
                    target_path = self.custom_nodes_dir / node.name
                    try:
                        shutil.copytree(node.backup_path, target_path)
                        print(f"✅ Restored: {node.name}")
                    except Exception as e:
                        print(f"❌ Failed to restore {node.name}: {e}")
                else:
                    print(f"⚠️  No backup available for {node.name}")

            print(f"✅ Rollback completed successfully")
            print(f"   Current backup ID: {current_backup_id}")
            return True

        except Exception as e:
            print(f"❌ Rollback failed: {e}")
            return False

    def remove_node(self, node_name: str, create_backup: bool = True) -> bool:
        """Safely remove a custom node"""
        print(f"🗑️  Removing custom node: {node_name}")

        # Find the node
        node_path = self.custom_nodes_dir / node_name
        if not node_path.exists():
            print(f"❌ Node not found: {node_name}")
            return False

        # Create backup if requested
        if create_backup:
            backup_id = self.create_rollback_point(f"Before removing {node_name}")
            print(f"   Backup created: {backup_id}")

        try:
            # Remove the node directory
            shutil.rmtree(node_path)
            print(f"✅ Node removed: {node_name}")

            # Update custom_nodes.txt
            if self.custom_nodes_file.exists():
                with open(self.custom_nodes_file, 'r') as f:
                    lines = f.readlines()

                with open(self.custom_nodes_file, 'w') as f:
                    for line in lines:
                        # Keep lines that don't reference this node
                        if node_name not in line or line.strip().startswith('#'):
                            f.write(line)

            return True

        except Exception as e:
            print(f"❌ Failed to remove node: {e}")
            return False

    def list_rollback_points(self) -> List[RollbackPoint]:
        """List all available rollback points"""
        rollback_points = self.load_state()
        return sorted(rollback_points.values(), key=lambda x: x.timestamp, reverse=True)

    def print_rollback_points(self):
        """Print all available rollback points"""
        rollback_points = self.list_rollback_points()

        if not rollback_points:
            print("No rollback points available")
            return

        print("\n📋 Available Rollback Points:")
        print("=" * 80)

        for rp in rollback_points:
            print(f"\n🆔 ID: {rp.id}")
            print(f"📅 Timestamp: {rp.timestamp}")
            print(f"📝 Description: {rp.description}")
            print(f"📦 Nodes: {len(rp.nodes)}")

            # Show first few nodes
            if rp.nodes:
                print(f"   Nodes: {', '.join([n.name for n in rp.nodes[:3]])}")
                if len(rp.nodes) > 3:
                    print(f"   ... and {len(rp.nodes) - 3} more")

    def cleanup_old_backups(self, keep_count: int = 5):
        """Clean up old backup directories"""
        rollback_points = self.load_state()

        if len(rollback_points) <= keep_count:
            return

        # Sort by timestamp and remove oldest
        sorted_points = sorted(rollback_points.items(), key=lambda x: x[1].timestamp)
        to_remove = sorted_points[:-keep_count]

        removed_count = 0
        for rp_id, rp in to_remove:
            try:
                # Remove backup directory
                for node in rp.nodes:
                    if node.backup_path and os.path.exists(node.backup_path):
                        shutil.rmtree(node.backup_path)
                        removed_count += 1

                # Remove from state
                del rollback_points[rp_id]
            except Exception as e:
                print(f"Warning: Could not remove backup {rp_id}: {e}")

        # Save updated state
        self.save_state(rollback_points)
        print(f"🧹 Cleaned up {len(to_remove)} old rollback points")

def main():
    """Main function to run the rollback manager"""
    parser = argparse.ArgumentParser(description='ComfyUI Custom Nodes Rollback Manager')
    parser.add_argument('--custom-nodes-dir', default='/workspace/ComfyUI/custom_nodes',
                        help='Custom nodes directory')
    parser.add_argument('--state-file', default='/tmp/custom_nodes_state.json',
                        help='State file location')
    parser.add_argument('--backup-dir', default='/tmp/custom_nodes_backups',
                        help='Backup directory location')

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Create rollback point
    create_parser = subparsers.add_parser('create', help='Create a rollback point')
    create_parser.add_argument('description', help='Description of the rollback point')

    # List rollback points
    list_parser = subparsers.add_parser('list', help='List rollback points')

    # Rollback to point
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to a point')
    rollback_parser.add_argument('rollback_id', help='Rollback point ID')
    rollback_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')

    # Remove node
    remove_parser = subparsers.add_parser('remove', help='Remove a custom node')
    remove_parser.add_argument('node_name', help='Name of the node to remove')
    remove_parser.add_argument('--no-backup', action='store_true', help='Skip creating backup')

    # Cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old backups')
    cleanup_parser.add_argument('--keep', type=int, default=5, help='Number of rollback points to keep')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Create rollback manager
    manager = RollbackManager(
        custom_nodes_dir=args.custom_nodes_dir,
        state_file=args.state_file,
        backup_dir=args.backup_dir
    )

    # Execute command
    if args.command == 'create':
        manager.create_rollback_point(args.description)

    elif args.command == 'list':
        manager.print_rollback_points()

    elif args.command == 'rollback':
        success = manager.rollback_to_point(args.rollback_id, dry_run=args.dry_run)
        if not success:
            sys.exit(1)

    elif args.command == 'remove':
        success = manager.remove_node(args.node_name, create_backup=not args.no_backup)
        if not success:
            sys.exit(1)

    elif args.command == 'cleanup':
        manager.cleanup_old_backups(args.keep)

if __name__ == "__main__":
    main()