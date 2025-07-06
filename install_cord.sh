#!/bin/bash
# Install cord command with bash completion

echo "Installing Cord System Monitor Command"
echo "====================================="

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make cord executable
chmod +x "$SCRIPT_DIR/cord"

# Check if we can install to /usr/local/bin
if [ -w /usr/local/bin ]; then
    echo "Installing cord to /usr/local/bin..."
    cp "$SCRIPT_DIR/cord" /usr/local/bin/cord
    INSTALL_PATH="/usr/local/bin"
else
    # Install to user's local bin
    mkdir -p "$HOME/.local/bin"
    echo "Installing cord to $HOME/.local/bin..."
    cp "$SCRIPT_DIR/cord" "$HOME/.local/bin/cord"
    INSTALL_PATH="$HOME/.local/bin"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
        echo "Adding $HOME/.local/bin to PATH in ~/.bashrc"
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
        echo "⚠️  Please run 'source ~/.bashrc' or restart your terminal"
    fi
fi

# Install bash completion
COMPLETION_DIR=""
if [ -d /etc/bash_completion.d ]; then
    COMPLETION_DIR="/etc/bash_completion.d"
elif [ -d /usr/share/bash-completion/completions ]; then
    COMPLETION_DIR="/usr/share/bash-completion/completions"
else
    # User completion directory
    mkdir -p "$HOME/.bash_completion.d"
    COMPLETION_DIR="$HOME/.bash_completion.d"
fi

echo "Installing bash completion to $COMPLETION_DIR..."
if [ -w "$COMPLETION_DIR" ]; then
    cp "$SCRIPT_DIR/cord_completion.bash" "$COMPLETION_DIR/cord"
    echo "✓ Bash completion installed"
else
    # Try with sudo
    if command -v sudo &> /dev/null; then
        sudo cp "$SCRIPT_DIR/cord_completion.bash" "$COMPLETION_DIR/cord"
        echo "✓ Bash completion installed (with sudo)"
    else
        # Fallback to user directory
        mkdir -p "$HOME/.bash_completion.d"
        cp "$SCRIPT_DIR/cord_completion.bash" "$HOME/.bash_completion.d/cord"
        
        # Add to bashrc if not already there
        if ! grep -q "bash_completion.d" ~/.bashrc; then
            echo "" >> ~/.bashrc
            echo "# Load custom bash completions" >> ~/.bashrc
            echo "for file in ~/.bash_completion.d/*; do" >> ~/.bashrc
            echo "    [ -r \"\$file\" ] && source \"\$file\"" >> ~/.bashrc
            echo "done" >> ~/.bashrc
        fi
        
        echo "✓ Bash completion installed to user directory"
        echo "⚠️  Please run 'source ~/.bashrc' or restart your terminal"
    fi
fi

echo ""
echo "Installation complete!"
echo ""
echo "Available commands:"
echo "  cord show        - System status overview"
echo "  cord cpu         - CPU usage"
echo "  cord memory      - Memory usage"
echo "  cord disk        - Disk usage"
echo "  cord processes   - Running processes"
echo "  cord network     - Network statistics"
echo "  cord info        - System information"
echo "  cord kill <pid>  - Kill a process"
echo "  cord help        - Show help"
echo ""
echo "Try: cord show"
echo "Tab completion: cord <TAB> or cord s<TAB>"