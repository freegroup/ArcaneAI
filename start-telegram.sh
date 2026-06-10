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
echo "║                 Dungeon Telegram Bot                       ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Players interact via Telegram chat                        ║"
echo "║  Set TELEGRAM_BOT_TOKEN or telegram.bot_token in           ║"
echo "║  config.yaml before starting                               ║"
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

# Check for bot token
source "$SCRIPT_DIR/game/venv/bin/activate"
TOKEN_IN_CONFIG=$(python3 -c "
import yaml, sys
try:
    with open('$SCRIPT_DIR/config.yaml') as f:
        cfg = yaml.safe_load(f)
    tok = cfg.get('telegram', {}).get('bot_token', '')
    print('yes' if tok else 'no')
except Exception:
    print('no')
" 2>/dev/null)

if [ "$TOKEN_IN_CONFIG" = "no" ] && [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    error "Kein Telegram Bot Token gefunden."
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${YELLOW}Du hast noch keinen Bot? → Neuen Bot anlegen:${NC}"
    echo "  1. Telegram öffnen und @BotFather suchen"
    echo "  2. /newbot senden"
    echo "  3. Name eingeben (z.B. 'ArcaneAI')"
    echo "  4. Username eingeben — muss auf 'bot' enden (z.B. 'arcaneai_bot')"
    echo "  5. BotFather schickt dir einen Token: 1234567890:AAH..."
    echo ""
    echo -e "${YELLOW}Du hast schon einen Bot, aber kein Token mehr? → Token wiederherstellen:${NC}"
    echo "  1. @BotFather öffnen"
    echo "  2. /mybots senden → deinen Bot auswählen"
    echo "  3. 'API Token' klicken → Token wird angezeigt"
    echo ""
    echo -e "${CYAN}Token einrichten (eine der beiden Varianten):${NC}"
    echo ""
    echo "  Variante A — config.yaml (empfohlen):"
    echo "    telegram:"
    echo "      bot_token: \"1234567890:AAH...\""
    echo ""
    echo "  Variante B — Umgebungsvariable:"
    echo "    export TELEGRAM_BOT_TOKEN=\"1234567890:AAH...\""
    echo "    ./start-telegram.sh"
    echo ""
    echo -e "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    exit 1
fi

echo ""
info "Starting Telegram bot..."
echo ""

cd "$SCRIPT_DIR/game/src"
source ../venv/bin/activate
exec python main.py telegram
