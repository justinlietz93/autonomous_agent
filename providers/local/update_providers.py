"""Script to update all local Ollama providers to the new format."""

import os
import sys
import argparse
from pathlib import Path
import re
from difflib import unified_diff

def get_header_comment(model_name: str) -> str:
    """Generate a relevant header comment for the provider."""
    return f"""# {model_name}_ollama_provider.py
# Adapter for local Ollama {model_name} instance.
#
# This provider supports:
# - Tool integration via tool_manager
# - Streaming with chunking and smoothing
# - Connection validation
# - Error handling
"""

def get_template_content():
    """Get the new template content."""
    template_path = Path(__file__).parent / "ollama_provider_template.py"
    with open(template_path, 'r') as f:
        return f.read()

def update_provider(provider_path: Path, template: str, dry_run: bool = False, show_changes: bool = False):
    """Update a provider file to the new format."""
    with open(provider_path, 'r') as f:
        old_content = f.read()
    
    # Extract key info from old provider
    class_name_match = re.search(r'class (\w+)Provider\(Tool\):', old_content)
    model_name_match = re.search(r'model="([^"]+)"', old_content)
    
    if not class_name_match or not model_name_match:
        print(f"Could not extract info from {provider_path}")
        return
        
    class_name = class_name_match.group(1)
    model_name = model_name_match.group(1)
    
    # Create header and new content
    header = get_header_comment(model_name)
    new_content = (header + template
        .replace('MODEL_NAMEProvider', f'{class_name}Provider')
        .replace('MODEL_NAME', model_name)
        .replace('# Template for Ollama model providers\n# To use:\n# 1. Copy this file and rename it (e.g. my_model_provider.py)\n# 2. Update the class name and model_name\n# 3. Implement _get_model_name()\n', ''))
    
    if dry_run:
        print(f"\nWould update {provider_path}:")
        print(f"  Class: {class_name}Provider")
        print(f"  Model: {model_name}")
        print("  Changes:")
        print("    - Add tool manager support")
        print("    - Add streaming components")
        print("    - Add connection checking")
        print("    - Update response format")
        print("    - Update header comments")
        
        if show_changes:
            print("\nFile changes:")
            diff = unified_diff(
                old_content.splitlines(keepends=True),
                new_content.splitlines(keepends=True),
                fromfile=str(provider_path),
                tofile=f"{provider_path}.new"
            )
            print(''.join(diff))
    else:
        # Write updated provider
        with open(provider_path, 'w') as f:
            f.write(new_content)
        print(f"Updated {provider_path}")

def main():
    parser = argparse.ArgumentParser(description="Update Ollama providers to new format")
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--dry-run', action='store_true', 
                      help="Show what would be updated without making changes")
    group.add_argument('--show-changes', action='store_true',
                      help="Show actual file changes in dry run")
    args = parser.parse_args()

    provider_dir = Path(__file__).parent
    template = get_template_content()
    
    # Get all provider files except template and this script
    provider_files = [
        f for f in provider_dir.glob("*_ollama_provider.py")
        if f.name not in ["ollama_provider_template.py", "update_providers.py"]
    ]
    
    dry_run = args.dry_run or args.show_changes
    if dry_run:
        print("\nDRY RUN - No changes will be made")
        
        # Show first file as example
        if provider_files:
            update_provider(provider_files[0], template, 
                          dry_run=dry_run,
                          show_changes=args.show_changes)
            
            # Summarize remaining files
            remaining = len(provider_files) - 1
            if remaining > 0:
                print(f"\n... and {remaining} more files would be updated:")
                for f in provider_files[1:]:
                    print(f"  - {f.name}")
    else:
        # Actually update all files
        for provider_file in provider_files:
            update_provider(provider_file, template, 
                          dry_run=dry_run,
                          show_changes=args.show_changes)
    
    count = len(provider_files)    
    if dry_run:
        print(f"\nWould update {count} providers")
    else:
        print(f"\nUpdated {count} providers")

if __name__ == "__main__":
    main() 