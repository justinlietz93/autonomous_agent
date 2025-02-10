#!/bin/bash

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install the package in development mode
pip install -e .

# Create a requirements.txt snapshot
pip freeze > requirements.txt

echo "Environment setup complete!"
echo "To activate: source venv/bin/activate" 