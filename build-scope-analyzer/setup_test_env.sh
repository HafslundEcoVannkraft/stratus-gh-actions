#!/bin/bash

set -e

# Remove any existing virtual environment
echo "Removing old virtual environment (if any)..."
rm -rf venv

# Create a new virtual environment
echo "Creating new virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete!"
echo "To activate the virtual environment, run: source venv/bin/activate"
echo "To run the tests, use: python test_build_scope_analyzer.py"
echo "To deactivate the virtual environment when done:"
echo "  - Type 'deactivate' in your terminal"
echo "  - Or close your terminal session"
echo "To remove the virtual environment completely:"
echo "  - First deactivate it"
echo "  - Then run: rm -rf venv" 