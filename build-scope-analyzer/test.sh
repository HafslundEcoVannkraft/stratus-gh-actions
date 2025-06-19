#!/bin/bash

set -e

# Check for --skip-setup flag
SKIP_SETUP=false
for arg in "$@"; do
    if [ "$arg" == "--skip-setup" ]; then
        SKIP_SETUP=true
    fi
done

if [ "$SKIP_SETUP" == true ]; then
    echo "Skipping setup and using existing virtual environment..."

    # Check if venv exists
    if [ ! -d "venv" ]; then
        echo "Error: Virtual environment 'venv' not found."
        echo "Please run without --skip-setup flag first to create the virtual environment."
        exit 1
    fi

    # Just activate the virtual environment
    echo "Activating existing virtual environment..."
    source venv/bin/activate
else
    # Remove any existing virtual environment
    echo "Removing old virtual environment (if any)..."
    rm -rf venv

    # Create a new virtual environment
    echo "Creating new virtual environment..."
    python3 -m venv venv

    # Activate the virtual environment
    echo "Activating virtual environment and installing dependencies..."
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Setup complete! Running tests..."

# Extract test arguments (everything after -- if it exists)
TEST_ARGS=""
FOUND_SEPARATOR=false
for arg in "$@"; do
    if [ "$arg" == "--" ]; then
        FOUND_SEPARATOR=true
        continue
    fi

    if [ "$FOUND_SEPARATOR" == true ]; then
        TEST_ARGS="$TEST_ARGS $arg"
    fi
done

# Run the tests with any provided arguments
echo "Running: python test_build_scope_analyzer.py$TEST_ARGS"
python test_build_scope_analyzer.py $TEST_ARGS

echo "Tests completed!"
echo ""
echo "Note: The virtual environment is still active."
echo ""
echo "Usage:"
echo "  ./test.sh                       # Full setup and run tests"
echo "  ./test.sh --skip-setup          # Skip setup, just run tests"
echo "  ./test.sh -- -v                 # Run tests with verbose flag"
echo "  ./test.sh --skip-setup -- -v    # Skip setup, run tests with verbose flag"
echo ""
echo "To run the tests again manually:"
echo "source venv/bin/activate"
echo "python test_build_scope_analyzer.py"
echo "To deactivate the virtual environment when done:"
echo "  - Type 'deactivate' in your terminal"
echo "  - Or close your terminal session"
echo "To remove the virtual environment completely:"
echo "  - First deactivate it"
echo "  - Then run: rm -rf venv"