from setuptools import setup, find_packages

setup(
    name="llm_kit",
    version="0.1.0",
    packages=find_packages(include=['tools*', 'tests*', 'providers*', 'memory*', 'prompts*']),
    install_requires=[
        "python-dotenv>=1.0.0",
        "pytest>=8.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-sugar",
        "psutil>=5.9.0",
        "anthropic>=0.45.0",
        "requests>=2.32.3",
        "beautifulsoup4>=4.12.3",
        "pyautogui>=0.9.54",
        "openai>=1.0.0",
        "responses>=0.24.0",
        "transformers>=4.37.2",
        "sentencepiece>=0.1.99",
        "torch>=2.0.0",
        "watchdog==3.0.0",
        "protobuf>=4.25.1",
        "ollama",
        "typing-extensions>=4.5.0",
        "black>=23.0.0",
        "isort>=5.12.0",
        "mypy>=1.5.0",
    ],
    python_requires=">=3.8",
    author="Justin Lietz",
    description="A toolkit for LLM interactions",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
) 