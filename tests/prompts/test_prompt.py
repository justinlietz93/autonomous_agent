#!/usr/bin/env python3
"""Test script to display full prompts from the prompt manager."""

import argparse
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from prompts.prompt_manager import PromptManager

def save_prompt(content: str, prompt_name: str = "default") -> str:
    """Save prompt content to a timestamped file."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"prompt_{prompt_name}_{timestamp}.txt"
    
    # Create prompts directory in tests/prompts/generated_prompts
    prompts_dir = Path(__file__).parent / "generated_prompts"
    prompts_dir.mkdir(exist_ok=True)
    
    # Save prompt to file
    prompt_file = prompts_dir / filename
    with open(prompt_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return str(prompt_file)

def main():
    parser = argparse.ArgumentParser(description='Display full prompt from prompt manager')
    parser.add_argument('--prompt', type=str,
                       help='Name of the prompt to display (e.g. SELF_OPTIMIZATION)')
    parser.add_argument('--list', '-l',
                       action='store_true',
                       help='List available prompts')
    
    args = parser.parse_args()
    
    # Initialize prompt manager with specified prompt
    prompt_manager = PromptManager(default_prompt=args.prompt if args.prompt else None)
    
    # Handle prompt listing
    if args.list:
        print("Available prompts:")
        for prompt in prompt_manager.list_prompts():
            print(f"  - {prompt}")
        return
    
    # Get full prompt
    full_prompt = prompt_manager.get_full_prompt()
    
    # Save to file
    saved_file = save_prompt(full_prompt, args.prompt.lower() if args.prompt else "default")
    
    # Display prompt and file location
    print("\n=== FULL PROMPT ===\n")
    print(full_prompt)
    print("\n=== END PROMPT ===\n")
    print(f"Prompt saved to: {saved_file}")

if __name__ == "__main__":
    main() 