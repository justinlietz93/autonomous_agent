from typing import Dict, Type, Optional
import importlib
import os
from pathlib import Path

class ProviderLibrary:
    """A library that manages and provides access to different LLM providers."""
    
    def __init__(self):
        self.providers: Dict[str, Type] = {}
        self.provider_folders = {
            "LOCAL": {},  # Ollama providers
            "API": {},    # API providers
        }
        self._load_providers()
        
    def _load_providers(self) -> None:
        """Dynamically load all provider modules recursively from providers directory."""
        providers_dir = Path(__file__).parent
        
        # Get all Python files recursively that end with _provider.py
        provider_files = [
            f for f in providers_dir.rglob("*_provider.py")
            if f.is_file() and f.name != "__init__.py"
        ]
        
        for provider_file in provider_files:
            try:
                # Build import path
                rel_path = provider_file.relative_to(providers_dir)
                module_path = f"providers.{str(rel_path.with_suffix('')).replace(os.sep, '.')}"
                
                # Import the module
                module = importlib.import_module(module_path)
                
                # Extract provider name from filename
                provider_name = provider_file.stem.replace("_provider", "")
                
                # Look for a class that ends with 'Provider'
                for attr_name in dir(module):
                    if attr_name.endswith('Provider'):
                        provider_class = getattr(module, attr_name)
                        
                        # Store in flat dictionary for backward compatibility
                        self.providers[provider_name] = provider_class
                        
                        # Determine folder based on provider type
                        if "api" in provider_name or "API" in provider_name:
                            folder = "API"
                        else:
                            folder = "LOCAL"
                            
                        # Store in folder structure
                        self.provider_folders[folder][provider_name] = provider_class
                        break
                        
            except Exception as e:
                print(f"Failed to load provider from {provider_file}: {e}")
                
    def get_provider(self, name: str, **kwargs) -> Optional[object]:
        """
        Get a provider instance by name.
        
        Args:
            name: Name of the provider (e.g., "deepseek_ollama" or "deepseek_api")
            **kwargs: Additional arguments to pass to the provider constructor
        """
        # First try exact match in flat dictionary
        provider_class = self.providers.get(name)
        if provider_class:
            try:
                return provider_class(**kwargs)
            except Exception as e:
                print(f"Failed to initialize provider {name}: {e}")
                return None

        # If not found, search through all folders
        for folder_providers in self.provider_folders.values():
            if name in folder_providers:
                try:
                    return folder_providers[name](**kwargs)
                except Exception as e:
                    print(f"Failed to initialize provider {name}: {e}")
                    return None
        
        return None
        
    def list_providers(self) -> list[str]:
        """Get a list of available provider names."""
        return sorted(self.providers.keys())
        
    def list_providers_by_folder(self) -> list[str]:
        """Return a list of lines describing available providers by folder."""
        lines = []
        
        for folder_name in sorted(self.provider_folders.keys()):
            if folder_name and self.provider_folders[folder_name]:  # Only show non-empty folders
                lines.append(folder_name)
                lines.append("-" * 40)
                providers = sorted(self.provider_folders[folder_name].keys())
                for provider in providers:
                    lines.append(f"  - {provider}")
                lines.append("")  # blank line after each folder
            
        return lines
        
    def get_default_provider(self, **kwargs) -> Optional[object]:
        """Get the default provider."""
        return self.get_provider("deepseek_ollama", **kwargs)

    def create_provider(self, model_name: str) -> None:
        """Create a new Ollama provider."""
        providers_dir = Path(__file__).parent
        template_path = providers_dir / "local" / "ollama_provider_template.py"
        new_provider_path = providers_dir / "local" / f"{model_name}_ollama_provider.py"
        
        if not template_path.exists():
            raise ValueError(f"Template file not found at {template_path}")
            
        # Create local directory if it doesn't exist
        new_provider_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Read template and replace MODEL_NAME
        with open(template_path, 'r') as f:
            template = f.read()
        new_content = template.replace('MODEL_NAME', model_name)
        
        # Write new provider
        with open(new_provider_path, 'w') as f:
            f.write(new_content)
            
        # Reload providers to include the new one
        self._load_providers()

