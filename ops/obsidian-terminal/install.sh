#!/bin/sh
set -eu
cd "$(dirname "$0")"
command -v gh >/dev/null
systemctl --user show-environment >/dev/null
gh api repos/Dirtyhandgernades/Dudebot/actions/workflows/obsidian-free-quant-feed.yml --silent
install -Dm644 terminal.py "$HOME/.local/share/obsidian-terminal/terminal.py"
for unit in obsidian-research.service obsidian-research.timer; do
    install -Dm644 "$unit" "$HOME/.config/systemd/user/$unit"
done
systemctl --user daemon-reload
systemctl --user enable --now obsidian-research.timer
systemctl --user list-timers obsidian-research.timer
