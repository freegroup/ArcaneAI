#!/usr/bin/env bash
set -e

# Usage:
#   ./start.sh                         # macOS app (downloads the model on first run)
#   ./start.sh --dev [model.litertlm]  # dev build: uses a local model, no download
#                                      #   default: the app's model store (shared with prod)
#   ./start.sh --device <id>           # other Flutter device (see: flutter devices)
#
# The console shows, word for word, every prompt sent to the model and every
# answer (lines starting with [llm]).

MODE="prod"
DEVICE="macos"
MODEL_PATH=""
LITERT_URL="https://huggingface.co/litert-community/gemma-4-E4B-it-litert-lm/resolve/main/gemma-4-E4B-it.litertlm"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"       # app/

error() { echo -e "${RED}❌ $1${NC}"; }
success() { echo -e "${GREEN}✅ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
info() { echo -e "${CYAN}ℹ️  $1${NC}"; }

while [ $# -gt 0 ]; do
    case "$1" in
        --dev)
            MODE="dev"; shift
            if [ $# -gt 0 ] && [[ "$1" != --* ]]; then MODEL_PATH="$1"; shift; fi ;;
        --device) DEVICE="$2"; shift 2 ;;
        -h|--help) sed -n '4,11p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) error "Unknown option: $1"; exit 1 ;;
    esac
done

echo -e "${CYAN}"
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                 ArcaneAI Player                            ║"
echo "║        On-device text adventure — Flutter + LiteRT         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

for tool in flutter dart; do
    command -v "$tool" &>/dev/null || { error "$tool not found"; exit 1; }
done

# Build the game packs (definitions + sounds + manifests) into the app assets.
info "Building game packs..."
python3 "$APP_DIR/tool/build_game_pack.py"

DEFINES=()
ENTRY="lib/main.dart"
if [ "$MODE" = "dev" ]; then
    ENTRY="lib/main_development.dart"
    # The model lives in ONE place: the app's model store, where the
    # production build downloads it too — so both builds share one file and
    # nothing is downloaded or copied per build. (Outside ~/Documents etc.:
    # macOS would ask for folder access again after every re-sign.)
    BUNDLE_ID=$(sed -n 's/^PRODUCT_BUNDLE_IDENTIFIER = //p' "$APP_DIR/macos/Runner/Configs/AppInfo.xcconfig")
    MODEL_DIR="$HOME/Library/Application Support/$BUNDLE_ID/flutter_gemma"
    MODEL_PATH="${MODEL_PATH:-$MODEL_DIR/gemma-4-E4B-it.litertlm}"
    for OLD_MODEL in "$HOME/Library/Caches/arcane_player/models/gemma-4-E4B-it.litertlm" \
                     "$APP_DIR/models/gemma-4-E4B-it.litertlm"; do
        if [ ! -f "$MODEL_PATH" ] && [ -f "$OLD_MODEL" ]; then
            mkdir -p "$(dirname "$MODEL_PATH")" && mv "$OLD_MODEL" "$MODEL_PATH"
            info "Model moved to $MODEL_PATH"
        fi
    done
    if [ ! -f "$MODEL_PATH" ]; then
        warn "Model not found: $MODEL_PATH"
        read -r -p "Download Gemma 4 E4B (3.7 GB) now? [y/N] " answer
        [[ "$answer" =~ ^[yYjJ]$ ]] || exit 1
        mkdir -p "$(dirname "$MODEL_PATH")"
        curl -L -C - --fail -o "$MODEL_PATH" "$LITERT_URL"
    fi
    DEFINES+=(--dart-define=MODEL_PATH="$MODEL_PATH")
    # Google Cloud TTS as in the Python game, if config.yaml has a key for it.
    GOOGLE_TTS=$(python3 - "$APP_DIR/../config.yaml" 2>/dev/null <<'PY'
import sys, yaml
voice = (yaml.safe_load(open(sys.argv[1])) or {}).get('voice') or {}
if voice.get('enabled') and voice.get('provider') == 'google' and voice.get('api_key'):
    print(voice['api_key'])
    print(voice.get('voice_name') or '')
PY
)
    if [ -n "$GOOGLE_TTS" ]; then
        DEFINES+=(--dart-define=GOOGLE_TTS_API_KEY="$(echo "$GOOGLE_TTS" | sed -n 1p)")
        GOOGLE_VOICE=$(echo "$GOOGLE_TTS" | sed -n 2p)
        [ -n "$GOOGLE_VOICE" ] && DEFINES+=(--dart-define=GOOGLE_TTS_VOICE="$GOOGLE_VOICE")
        success "Google TTS: ${GOOGLE_VOICE:-Standardstimme}"
    fi
    success "Dev build with local model: $MODEL_PATH"
fi
cd "$APP_DIR"
flutter pub get >/dev/null

if [ "$DEVICE" != "macos" ]; then
    info "Starting on $DEVICE... r = hot reload, R = restart, q = quit"
    exec flutter run -d "$DEVICE" -t "$ENTRY" "${DEFINES[@]}"
fi

# macOS: launching via `open` makes the app its own responsible process, so
# the mic/speech permission prompt is attributed to the app (not the terminal,
# which otherwise aborts it). We build, stage the LiteRT-LM companion dylibs
# (normally a Podfile post_install phase — this SwiftPM app has no Podfile),
# re-sign, launch, then attach for logs and hot reload.
info "Building macOS app..."
flutter build macos --debug -t "$ENTRY" "${DEFINES[@]}"
APP="$APP_DIR/build/macos/Build/Products/Debug/arcane_player.app"

STAGER="$HOME/Library/Caches/flutter_gemma/native/macos_arm64/stage_macos_companions.sh"
if [ -f "$STAGER" ]; then
    sh "$STAGER" "$APP/Contents/Frameworks" >/dev/null 2>&1 || true
    codesign --force --sign - --preserve-metadata=entitlements,identifier "$APP" 2>/dev/null || true
    success "LiteRT-LM libraries staged"
fi

LOG="${TMPDIR:-/tmp}/arcane_player.log"; : > "$LOG"
pkill -f "arcane_player.app/Contents/MacOS/arcane_player" 2>/dev/null || true
open -n "$APP" --stdout "$LOG" --stderr "$LOG"

VM_URL=""
for _ in $(seq 1 40); do
    VM_URL=$(grep -o 'http://127.0.0.1:[0-9]*/[^ ]*/' "$LOG" | head -1 || true)
    [ -n "$VM_URL" ] && break
    sleep 0.5
done
if [ -z "$VM_URL" ]; then
    warn "App started, no VM service URL found (log: $LOG) — no hot reload"
    exit 0
fi
success "App started"
info "Attaching... r = hot reload, R = restart, q = quit"
exec flutter attach -d macos --debug-url "$VM_URL" -t "$ENTRY"
