#!/bin/bash
# Rename Agent Installer
# Usage: curl -fsSL https://raw.githubusercontent.com/omarshahine/claude-rename-agent/main/install.sh | bash

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m' # No Color

echo ""
echo -e "${GREEN}  ██████╗ ███████╗███╗   ██╗ █████╗ ███╗   ███╗███████╗${NC}"
echo -e "${GREEN}  ██╔══██╗██╔════╝████╗  ██║██╔══██╗████╗ ████║██╔════╝${NC}"
echo -e "${GREEN}  ██████╔╝█████╗  ██╔██╗ ██║███████║██╔████╔██║█████╗${NC}"
echo -e "${GREEN}  ██╔══██╗██╔══╝  ██║╚██╗██║██╔══██║██║╚██╔╝██║██╔══╝${NC}"
echo -e "${GREEN}  ██║  ██║███████╗██║ ╚████║██║  ██║██║ ╚═╝ ██║███████╗${NC}"
echo -e "${GREEN}  ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝     ╚═╝╚══════╝${NC}"
echo -e "${GREEN}                       AGENT${NC}"
echo ""
echo -e "${DIM}  Installing Rename Agent...${NC}"
echo ""

# Check for Python 3.10+
check_python() {
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
    elif command -v python3.10 &> /dev/null; then
        PYTHON_CMD="python3.10"
    elif command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
        MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
            PYTHON_CMD="python3"
        else
            echo -e "${RED}Error: Python 3.10+ is required (found $PYTHON_VERSION)${NC}"
            echo ""
            echo "Install Python 3.11 with:"
            echo "  macOS:  brew install python@3.11"
            echo "  Ubuntu: sudo apt install python3.11"
            exit 1
        fi
    else
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        exit 1
    fi
    echo -e "  ${DIM}Found Python: $PYTHON_CMD${NC}"
}

# Check for Claude Code
check_claude_code() {
    if ! command -v claude &> /dev/null; then
        echo -e "${RED}Error: Claude Code is not installed${NC}"
        echo ""
        echo "Install Claude Code first:"
        echo "  curl -fsSL https://claude.ai/install.sh | bash"
        exit 1
    fi
    echo -e "  ${DIM}Found Claude Code${NC}"
}

# Install the package
install_package() {
    echo -e "  ${DIM}Installing claude-rename-agent...${NC}"
    $PYTHON_CMD -m pip install --quiet --upgrade claude-rename-agent
}

# Main installation
main() {
    check_python
    check_claude_code
    install_package

    echo ""
    echo -e "${GREEN}  ✓ Rename Agent installed successfully!${NC}"
    echo ""
    echo "  Get started:"
    echo -e "    ${GREEN}rename-agent${NC}          Start interactive mode"
    echo -e "    ${GREEN}rename-agent --help${NC}   Show all options"
    echo ""
}

main
