#!/bin/bash
# Installation script for System Monitor MCP Server

echo "System Monitor MCP Server Installation"
echo "====================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "Error: Python $PYTHON_VERSION is installed, but Python $REQUIRED_VERSION or higher is required."
    exit 1
fi

echo "✓ Python $PYTHON_VERSION detected"

# Install dependencies
echo "Installing dependencies..."
pip3 install -r "$SCRIPT_DIR/requirements.txt"

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed successfully"
else
    echo "Error: Failed to install dependencies"
    exit 1
fi

# Make server_standalone.py executable
chmod +x "$SCRIPT_DIR/server_standalone.py"

# Check if claude command exists
if command -v claude &> /dev/null; then
    echo ""
    echo "Claude CLI detected. Would you like to add the System Monitor MCP server now? (y/n)"
    read -r response
    
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "Adding System Monitor MCP server to Claude..."
        claude mcp add system-monitor python3 "$SCRIPT_DIR/server_standalone.py"
        
        if [ $? -eq 0 ]; then
            echo "✓ System Monitor MCP server added successfully!"
            echo ""
            echo "You can now use system monitoring commands in Claude CLI!"
        else
            echo "Error: Failed to add MCP server to Claude"
            echo "You can manually add it with:"
            echo "claude mcp add system-monitor python3 $SCRIPT_DIR/server_standalone.py"
        fi
    else
        echo ""
        echo "To add the server manually later, run:"
        echo "claude mcp add system-monitor python3 $SCRIPT_DIR/server_standalone.py"
    fi
else
    echo ""
    echo "Claude CLI not found. After installing Claude CLI, run:"
    echo "claude mcp add system-monitor python3 $SCRIPT_DIR/server_standalone.py"
fi

echo ""
echo "Installation complete!"