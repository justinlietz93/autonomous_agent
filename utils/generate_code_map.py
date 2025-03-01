#!/usr/bin/env python3
"""
Code Map Generator

Generates a comprehensive Markdown representation of the repository structure,
saving it to docs/code_map.md.

Usage:
    python utils/generate_code_map.py [--detailed]
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to Python path to ensure imports work correctly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Now we can safely import the module
from utils.code_mapper import RepositoryCrawler

def parse_args():
    parser = argparse.ArgumentParser(description="Generate a code map of the repository")
    parser.add_argument("--detailed", action="store_true", 
                        help="Include file sizes and additional information")
    parser.add_argument("--output", default="docs/code_map.md",
                        help="Output file path (default: docs/code_map.md)")
    return parser.parse_args()

def format_tree_as_markdown(tree: Dict, indent: int = 0, detailed: bool = False) -> List[str]:
    """Convert the tree dictionary to Markdown format."""
    lines = []
    
    # Only process the 'contents' part if this is the root
    if 'contents' in tree:
        tree = tree['contents']
    
    # Process directories first, then files
    dirs = []
    files = []
    
    for name, value in sorted(tree.items()):
        if name.startswith('__') and name.endswith('__'):
            continue  # Skip special entries like __error__
            
        if value is None:
            # This is a file
            files.append(name)
        else:
            # This is a directory
            dirs.append((name, value))
    
    # Add directories to output
    for name, subtree in dirs:
        indent_str = "    " * indent
        lines.append(f"{indent_str}* **{name}/**")
        subtree_lines = format_tree_as_markdown(subtree, indent + 1, detailed)
        lines.extend(subtree_lines)
    
    # Add files to output
    for name in files:
        indent_str = "    " * indent
        lines.append(f"{indent_str}* {name}")
    
    return lines

def collect_file_info(crawler: RepositoryCrawler, detailed: bool) -> Dict[str, Any]:
    """Collect information about the repository files."""
    info = {}
    
    if detailed:
        # Get file sizes and other details
        files_info = crawler.walk()
        for rel_path, size in files_info:
            info[str(rel_path)] = {
                "size": size,
                "size_formatted": format_size(size)
            }
    
    return info

def format_size(size_bytes: int) -> str:
    """Format bytes to human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024 or unit == 'GB':
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024

def add_header_and_metadata(lines: List[str], repo_path: str) -> List[str]:
    """Add header and metadata to the code map."""
    header = [
        "# Repository Code Map",
        "",
        f"Repository: `{os.path.basename(repo_path)}`",
        f"Generated: {Path().absolute()}",
        "",
        "## Directory Structure",
        ""
    ]
    return header + lines

def main():
    args = parse_args()
    
    # Get repository root (assuming script is run from repo root)
    repo_root = os.getcwd()
    
    # Configure the crawler with appropriate ignore patterns
    config = {
        'ignore_patterns': {
            'directories': [
                '.git', '__pycache__', 'venv', '.venv', 'env',
                '.idea', '.vscode', 'node_modules', '.pytest_cache'
            ],
            'files': [
                '*.pyc', '*.pyo', '*.pyd', 
                '*.so', '*.dll', '*.exe',
                '*.log', '*.cache', '*.bak', '*.swp', '*.tmp',
                '*.egg-info', '*.egg'
            ]
        }
    }
    
    # Initialize crawler
    crawler = RepositoryCrawler(repo_root, config)
    
    # Get file tree
    tree = crawler.get_file_tree()
    
    # Format as markdown
    md_lines = format_tree_as_markdown(tree, detailed=args.detailed)
    
    # Add header
    md_lines = add_header_and_metadata(md_lines, repo_root)
    
    # Ensure output directory exists
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    print(f"Code map generated at {output_path}")

if __name__ == "__main__":
    main() 