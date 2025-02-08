#!/usr/bin/env python3
"""Test script to display full prompts from the prompt manager."""

import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path to allow imports
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))

from prompts.prompt_manager import PromptManager
from memory.context_manager import ContextStorage

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

def get_latest_context(context_dir: str = "memory/context_logs", lines: int = 300) -> str:
    """Get the most recent context from actual log files."""
    # Get the most recent context file
    context_dir = project_root / context_dir
    if not context_dir.exists():
        return "[No context logs found]"
        
    context_files = sorted(context_dir.glob("context_*.txt"), reverse=True)
    if not context_files:
        return "[No context files found]"
        
    latest_file = context_files[0]
    
    # Read the context using the same logic as main_autonomous
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            all_lines = f.readlines()
        snippet = all_lines[-lines:] if len(all_lines) > lines else all_lines
        context = "".join(snippet).strip()
        
        # Format it like the LLM sees it
        return f"""
Current goal: FOLLOW ALL INSTRUCTIONS EXPLICITLY. FORMAT TOOL CALLS CORRECTLY.

Here is the recent context (last {lines} lines of logs):
----------------------------------------
{context}
----------------------------------------

Plan your next step. You can call any tool if needed. 
Do not stop until you have achieved your goal.
You will have amnesia at the beginning of each session, so you must review the provided context 
and use it to achieve your goal.

The main prompts do not know how far you've made it into your goal, so don't assume you're starting
from scratch.
"""
    except Exception as e:
        return f"[ERROR reading context: {e}]"

def main():
    parser = argparse.ArgumentParser(description='Display full prompt from prompt manager')
    parser.add_argument('--prompt', type=str,
                       help='Name of the prompt to display (e.g. SELF_OPTIMIZATION)')
    parser.add_argument('--list', '-l',
                       action='store_true',
                       help='List available prompts')
    parser.add_argument('--with-context', '-c',
                       action='store_true',
                       help='Include actual latest context as seen by LLM')
    parser.add_argument('--lines', type=int, default=300,
                       help='Number of context lines to include (default: 300)')
    
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
    
    # Add context if requested
    if args.with_context:
        full_prompt = f"{full_prompt}\n\n{get_latest_context(lines=args.lines)}"
    
    # Save to file
    saved_file = save_prompt(full_prompt, args.prompt.lower() if args.prompt else "default")
    
    # Display prompt and file location
    print("\n=== FULL PROMPT ===\n")
    print(full_prompt)
    print("\n=== END PROMPT ===\n")
    print(f"Prompt saved to: {saved_file}")

if __name__ == "__main__":
    main() 