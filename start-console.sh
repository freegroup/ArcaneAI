#!/usr/bin/env bash
set -e

# Required tools
REQUIRED_TOOLS=("python3")

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Utility functions
error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Header
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Dungeon Console Game                      ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Interactive text adventure in your terminal               ║"
echo "║  Type 'quit' to exit, 'help' for commands                  ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check tools
for tool in "${REQUIRED_TOOLS[@]}"; do
    if ! command -v "$tool" &>/dev/null; then
        error "$tool not found. Please install it first."
        exit 1
    fi
done
success "All required tools found"

# Check for Python virtual environment
if [ ! -d "$SCRIPT_DIR/game/venv" ]; then
    warn "Python venv not found in game/"
    info "Create it with: cd game && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo ""
info "Starting console game..."
echo ""

# Run the console game (foreground, interactive)
cd "$SCRIPT_DIR/game/src"
source ../venv/bin/activate
exec python main.py