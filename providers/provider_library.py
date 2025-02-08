from typing import Dict, Type, Optional
import importlib
import os
from pathlib import Path

class ProviderLibrary:
    """A library that manages and provides access to different LLM providers."""
    
    def __init__(self):
        self.providers: Dict[str, Type] = {}
        self._load_providers()
        
    def _load_providers(self) -> None:
        """Dynamically load all provider modules from the providers directory."""
        providers_dir = Path(__file__).parent
        
        # Get all Python files in the providers directory
        provider_files = [
            f for f in providers_dir.glob("*_provider.py")
            if f.is_file() and f.name != "__init__.py"
        ]
        
        for provider_file in provider_files:
            try:
                # Convert path to module name (e.g., deepseek_ollama_provider.py -> deepseek_ollama_provider)
                module_name = provider_file.stem
                
                # Import the module
                module = importlib.import_module(f"providers.{module_name}")
                
                # Extract provider name from filename (e.g., deepseek_ollama_provider -> deepseek_ollama)
                provider_name = module_name.replace("_provider", "")
                
                # Look for a class that ends with 'Provider'
                for attr_name in dir(module):
                    if attr_name.endswith('Provider'):
                        provider_class = getattr(module, attr_name)
                        self.providers[provider_name] = provider_class
                        break
                        
            except Exception as e:
                print(f"Failed to load provider from {provider_file}: {e}")
                
    def get_provider(self, name: str, **kwargs) -> Optional[object]:
        """
        Get a provider instance by name.
        
        Args:
            name: Name of the provider (e.g., "deepseek_ollama")
            **kwargs: Additional arguments to pass to the provider constructor
            
        Returns:
            Provider instance or None if provider not found
        """
        provider_class = self.providers.get(name)
        if provider_class:
            try:
                return provider_class(**kwargs)
            except Exception as e:
                print(f"Failed to initialize provider {name}: {e}")
                return None
        return None
        
    def list_providers(self) -> list[str]:
        """Get a list of available provider names."""
        return list(self.providers.keys())
        
    def get_default_provider(self, **kwargs) -> Optional[object]:
        """Get the default provider."""
        return self.get_provider("deepseek_ollama", **kwargs)

