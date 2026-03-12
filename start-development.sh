#!/usr/bin/env bash
set -e

TITLE="Dungeon Development Environment"

# Required tools
REQUIRED_TOOLS=("npm" "node" "python3")

# Services - each array: (name, command, directory, info)
declare -a svc_editor_server=("editor-server" "source venv/bin/activate && python src/main.py" "editor/server" "Editor API: http://localhost:8000")
declare -a svc_developer=("developer-server" "source ../venv/bin/activate && python developer.py" "game/src" "Developer API: http://localhost:9000")
declare -a svc_editor_ui=("editor-ui" "npm run serve" "editor/ui" "Editor UI: http://localhost:8080")
declare -a SERVICES=("svc_editor_server" "svc_developer" "svc_editor_ui")

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Process tracking
declare -a PIDS=() SERVICE_NAMES=() SERVICE_INFOS=()

# Utility functions
error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

# Cleanup
cleanup() {
    echo -e "\n${YELLOW}Stopping all services...${NC}"
    
    for i in "${!PIDS[@]}"; do
        local pid=${PIDS[$i]} name=${SERVICE_NAMES[$i]}
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${BLUE}   Stopping $name (PID: $pid)${NC}"
            kill -TERM -"$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
        fi
    done
    
    sleep 2
    for i in "${!PIDS[@]}"; do
        local pid=${PIDS[$i]} name=${SERVICE_NAMES[$i]}
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${RED}   Force kill $name (PID: $pid)${NC}"
            kill -KILL -"$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
        fi
    done
    
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Header
echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║            $TITLE                 ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Editor Server (API)     → http://localhost:8000           ║"
echo "║  Developer Server (Game) → http://localhost:9000           ║"
echo "║  Editor UI (Vue.js)      → http://localhost:8080           ║"
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

# Check for Python virtual environments
if [ ! -d "$SCRIPT_DIR/editor/server/venv" ]; then
    warn "Python venv not found in editor/server/"
    info "Create it with: cd editor/server && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

if [ ! -d "$SCRIPT_DIR/game/venv" ]; then
    warn "Python venv not found in game/"
    info "Create it with: cd game && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Check for node_modules
if [ ! -d "$SCRIPT_DIR/editor/ui/node_modules" ]; then
    warn "node_modules not found in editor/ui/"
    info "Install with: cd editor/ui && npm install"
fi

echo ""

# Start services
for svc_name in "${SERVICES[@]}"; do
    eval "svc_array=(\"\${${svc_name}[@]}\")"
    name="${svc_array[0]}"
    command="${svc_array[1]}"
    directory="${svc_array[2]}"
    svc_info="${svc_array[3]}"
    
    full_dir="$SCRIPT_DIR/$directory"
    
    if [ -d "$full_dir" ]; then
        info "Starting $name..."
        (cd "$full_dir" && bash -c "$command") &
        PIDS+=($!); SERVICE_NAMES+=("$name"); SERVICE_INFOS+=("$svc_info")
        sleep 1
    else
        error "Directory not found: $full_dir"
    fi
done

# Show results
echo ""
echo -e "${GREEN}Services started:${NC}"
for svc_info in "${SERVICE_INFOS[@]}"; do
    success "   $svc_info"
done

echo ""
warn "Press Ctrl+C to stop all services"
echo ""

# Wait and monitor
while true; do
    sleep 5
    running=0
    for pid in "${PIDS[@]}"; do
        kill -0 "$pid" 2>/dev/null && ((running++))
    done
    [ $running -eq 0 ] && { error "All services stopped unexpectedly"; break; }
done