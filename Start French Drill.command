#!/bin/zsh
# Double-click me to start the French drill.
# A Terminal window will open and stay running (that's the app's server),
# and the drill will open in your browser at http://localhost:8642.
cd "$(dirname "$0")"
exec python3 server.py
