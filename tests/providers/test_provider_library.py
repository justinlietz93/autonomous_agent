import unittest
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from providers.provider_library import ProviderLibrary
from tools.tool_base import Tool

class TestProviderLibrary(unittest.TestCase):
    def setUp(self):
        """Initialize a fresh ProviderLibrary for each test"""
        print("\nSetting up ProviderLibrary...")
        self.provider_lib = ProviderLibrary()

    def test_provider_loading(self):
        """Test that providers are loaded correctly"""
        print("\nTesting provider loading...")
        
        # List all provider files found
        providers_dir = Path(__file__).parent.parent.parent / "providers"
        provider_files = list(providers_dir.glob("*_provider.py"))
        print(f"\nFound provider files: {[f.name for f in provider_files]}")
        
        # Show loaded providers
        providers = self.provider_lib.list_providers()
        print(f"Loaded providers: {providers}")
        
        # Show provider details
        for name, provider_class in self.provider_lib.providers.items():
            print(f"\nProvider: {name}")
            print(f"  Class: {provider_class}")
            print(f"  Module: {provider_class.__module__}")
            
        # Run assertions
        self.assertGreater(len(providers), 0, "No providers were loaded")
        
        expected_providers = {"deepseek_ollama", "phi4_ollama", "deepseek-14b_ollama"}
        found_providers = set(providers)
        self.assertTrue(
            expected_providers.issubset(found_providers),
            f"Missing expected providers. Found: {found_providers}"
        )

    def test_get_provider(self):
        """Test getting specific providers"""
        print("\nTesting provider instantiation...")
        
        # Test getting existing provider
        print("\nTrying to get deepseek_ollama provider...")
        provider = self.provider_lib.get_provider("deepseek_ollama")
        if provider:
            print(f"Got provider: {provider}")
            print(f"Provider class: {provider.__class__}")
            print(f"Base classes: {provider.__class__.__bases__}")
        else:
            print("Failed to get provider!")
            
        self.assertIsNotNone(provider, "Failed to get deepseek_ollama provider")
        self.assertTrue(isinstance(provider, Tool), "Provider should inherit from Tool")
        
        # Test getting non-existent provider
        print("\nTrying to get non-existent provider...")
        provider = self.provider_lib.get_provider("nonexistent_provider")
        self.assertIsNone(provider, "Should return None for non-existent provider")

    def test_provider_interface(self):
        """Test that providers implement the required interface"""
        print("\nTesting provider interface...")
        provider = self.provider_lib.get_provider("deepseek_ollama")
        
        print(f"\nChecking provider attributes:")
        for attr in ["name", "description", "input_schema", "run"]:
            has_attr = hasattr(provider, attr)
            print(f"  {attr}: {'✓' if has_attr else '✗'}")
            if has_attr:
                print(f"    Value: {getattr(provider, attr)}")
        
        # Run assertions
        self.assertTrue(hasattr(provider, "name"), "Provider missing name attribute")
        self.assertTrue(hasattr(provider, "description"), "Provider missing description attribute")
        self.assertTrue(hasattr(provider, "input_schema"), "Provider missing input_schema attribute")
        self.assertTrue(hasattr(provider, "run"), "Provider missing run method")

if __name__ == "__main__":
    unittest.main(verbosity=2) 