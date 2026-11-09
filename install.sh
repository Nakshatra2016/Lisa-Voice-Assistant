#!/bin/bash
# Installs Lisa as a macOS LaunchAgent so it starts automatically at login
# and restarts itself if it crashes.
#
# Run this from inside the lisa project folder:
#   chmod +x install.sh
#   ./install.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Prefer the project's virtual environment so the LaunchAgent uses the same
# packages installed for Lisa, rather than Homebrew's externally-managed
# system Python.
if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_PATH="$SCRIPT_DIR/.venv/bin/python"
else
    PYTHON_PATH="$(command -v python3)"
fi
PLIST_NAME="com.lisa.assistant.plist"
DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

if [ -z "$PYTHON_PATH" ]; then
    echo "python3 not found on PATH. Install Python 3 first."
    exit 1
fi

if [ -z "$NEWS_API_KEY" ]; then
    echo "Warning: NEWS_API_KEY is not set in your current shell — the news"
    echo "commands won't work until you set it. See README.md."
fi
if [ -z "$CRYPTO_NEWS_API_KEY" ]; then
    echo "Note: CRYPTO_NEWS_API_KEY is not set — crypto news will use NEWS_API_KEY."
fi
if [ -z "$FOREX_NEWS_API_KEY" ]; then
    echo "Note: FOREX_NEWS_API_KEY is not set — forex news will use NEWS_API_KEY."
fi
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Warning: ANTHROPIC_API_KEY is not set in your current shell — the"
    echo "general Q&A fallback won't work until you set it. See README.md."
fi

mkdir -p "$HOME/Library/LaunchAgents"

sed \
    -e "s#__PYTHON_PATH__#${PYTHON_PATH}#g" \
    -e "s#__SCRIPT_PATH__#${SCRIPT_DIR}/main.py#g" \
    -e "s#__SCRIPT_DIR__#${SCRIPT_DIR}#g" \
    -e "s#__NEWS_API_KEY__#${NEWS_API_KEY}#g" \
    -e "s#__CRYPTO_NEWS_API_KEY__#${CRYPTO_NEWS_API_KEY}#g" \
    -e "s#__FOREX_NEWS_API_KEY__#${FOREX_NEWS_API_KEY}#g" \
    -e "s#__ANTHROPIC_API_KEY__#${ANTHROPIC_API_KEY}#g" \
    "$SCRIPT_DIR/$PLIST_NAME" > "$DEST"

# unload any previous version, then load the new one
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo ""
echo "Lisa is installed and will now start automatically when you log in."
echo ""
echo "Useful commands:"
echo "  Stop Lisa:     launchctl unload $DEST"
echo "  Start Lisa:    launchctl load $DEST"
echo "  Uninstall:     launchctl unload $DEST && rm $DEST"
echo "  Logs:          tail -f $SCRIPT_DIR/lisa.log"
echo "  Error logs:    tail -f $SCRIPT_DIR/lisa.error.log"
echo ""
echo "First time running: macOS will prompt you for Microphone access, and"
echo "for Accessibility/Automation permission the first time Lisa tries to"
echo "control apps via osascript (call/open/close). Grant these in"
echo "System Settings > Privacy & Security."
