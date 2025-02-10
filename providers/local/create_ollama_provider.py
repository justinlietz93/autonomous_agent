# Script to automatically create new Ollama providers from template

import os
import sys
import argparse
import re
from pathlib import Path

def sanitize_class_name(model_name: str) -> str:
    """Convert model name to valid Python class name."""
    # Replace any non-alphanumeric chars with underscore
    class_name = re.sub(r'[^a-zA-Z0-9]', '_', model_name)
    # Ensure starts with letter
    if not class_name[0].isalpha():
        class_name = 'Model_' + class_name
    # Convert to PascalCase
    class_name = ''.join(x.capitalize() for x in class_name.split('_'))
    return f"{class_name}Provider"

def sanitize_model_name(model_name: str) -> str:
    """Convert model name to format suitable for provider name."""
    # Replace dots and special chars with hyphens
    safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', model_name)
    # Remove consecutive hyphens
    safe_name = re.sub(r'-+', '-', safe_name)
    # Remove leading/trailing hyphens
    safe_name = safe_name.strip('-')
    return safe_name

def create_provider(model_name: str) -> None:
    """Create a new Ollama provider file from template."""
    
    # Convert model name to proper formats
    safe_model_name = sanitize_model_name(model_name)
    class_name = sanitize_class_name(model_name)
    
    # Create provider file path 
    provider_dir = Path(__file__).parent
    provider_file = provider_dir / f"{safe_model_name}_ollama_provider.py"
    template_file = provider_dir / "ollama_provider_template.py"
    
    # Check if provider already exists
    if provider_file.exists():
        print(f"Provider for {model_name} already exists at {provider_file}")
        return
        
    # Check if template exists
    if not template_file.exists():
        print(f"Error: Template file not found at {template_file}")
        return
        
    try:
        # Read template content
        with open(template_file, 'r') as f:
            template_content = f.read()
            
        # Replace template placeholders
        provider_content = (template_content
            .replace('MODEL_NAMEProvider', class_name)
            .replace('MODEL_NAME', model_name))
        
        # Create provider file
        with open(provider_file, 'w') as f:
            f.write(provider_content)
            
        print(f"Created new Ollama provider at {provider_file}")
        print(f"Provider class: {class_name}")
        print(f"Provider name: {safe_model_name}_ollama")
        print("\nTo use this provider:")
        print(f"1. Install model: ollama pull {model_name}")
        print("2. Start Ollama: ollama serve")
        print(f"3. Run with: python main_autonomous.py --provider {safe_model_name}_ollama")
        
    except Exception as e:
        print(f"Error creating provider: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Create new Ollama provider")
    parser.add_argument('--new-provider', type=str, help="Name of the Ollama model (e.g. qwen2.5-coder)")
    
    args = parser.parse_args()
    
    if args.new_provider:
        create_provider(args.new_provider)
    else:
        print("Please provide a model name with --new-provider")

if __name__ == "__main__":
    main() 