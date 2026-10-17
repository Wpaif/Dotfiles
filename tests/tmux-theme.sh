#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "$0")/.." && pwd)
scratch=$(mktemp -d)
export XDG_CONFIG_HOME="$scratch/config" XDG_STATE_HOME="$scratch/state"
export XDG_RUNTIME_DIR="$scratch/runtime" TMPDIR="$scratch/tmp"
unset ALACRITTY_SOCKET ALACRITTY_WINDOW_ID
mkdir -p "$XDG_CONFIG_HOME" "$XDG_RUNTIME_DIR" "$TMPDIR"
cp -R "$root/home/.config/tmux" "$root/home/.config/alacritty" "$XDG_CONFIG_HOME/"
export TMUX_THEME_SOCKET="$scratch/tmux.sock"
cleanup() { tmux -S "$TMUX_THEME_SOCKET" kill-server 2>/dev/null || :; rm -rf "$scratch"; }
trap cleanup EXIT
cli="$root/home/.local/bin/tmux-theme"
[[ -x $cli ]] || { echo 'FAIL: seletor tmux-theme ainda não existe'; exit 1; }
tmux -S "$TMUX_THEME_SOCKET" -f /dev/null new-session -d -s test
# Sobrescritas em uma sessão já existente não podem impedir a troca de tema.
tmux -S "$TMUX_THEME_SOCKET" new-session -d -s existing
tmux -S "$TMUX_THEME_SOCKET" set -t existing status-style 'fg=red,bg=red'
tmux -S "$TMUX_THEME_SOCKET" set -w -t existing: pane-border-style 'fg=red'
tmux -S "$TMUX_THEME_SOCKET" set -p -t existing: window-style 'bg=red'
tmux -S "$TMUX_THEME_SOCKET" set -g 'status-format[0]' 'OLD GLOBAL STATUS'
"$cli" --apply catppuccin-mocha
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -gqv @theme) == catppuccin-mocha ]]
[[ $(cat "$XDG_STATE_HOME/tmux/theme") == catppuccin-mocha ]]
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -Av -t existing status-style) == *'#1e1e2e'* ]]
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -wAv -t existing: pane-border-style) == *'#45475a'* ]]
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -pAv -t existing: window-style) == *'#1e1e2e'* ]]
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -gv 'status-format[0]') != 'OLD GLOBAL STATUS' ]]
old=$(tmux -S "$TMUX_THEME_SOCKET" show -gqv status-style)
"$cli" --preview dracula
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -gqv status-style) != "$old" ]]
[[ $(cat "$XDG_STATE_HOME/tmux/theme") == catppuccin-mocha ]]
"$cli" --restore
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -gqv status-style) == "$old" ]]
if "$cli" --apply ../invalid 2>/dev/null; then echo 'FAIL: tema inválido aceito'; exit 1; fi
[[ $(cat "$XDG_STATE_HOME/tmux/theme") == catppuccin-mocha ]]
for theme in hackthebox catppuccin-mocha catppuccin-latte nord tokyo-night dracula auto; do "$cli" --preview "$theme"; done
# Cancela uma prévia real via fzf no PTY de uma janela tmux.
"$cli" --apply catppuccin-mocha
before=$(tmux -S "$TMUX_THEME_SOCKET" show -gqv status-style)
tmux -S "$TMUX_THEME_SOCKET" new-window -d -n selector "$cli"
wait_theme() {
    local expected=$1
    for ((attempt=0; attempt<100; attempt++)); do
        [[ $(tmux -S "$TMUX_THEME_SOCKET" show -gqv @theme) != "$expected" ]] || return 0
        sleep 0.05
    done
    echo "FAIL: tema esperado: $expected" >&2
    return 1
}
# Aguarda fzf pronto para receber as teclas.
for ((attempt=0; attempt<100; attempt++)); do
    if tmux -S "$TMUX_THEME_SOCKET" capture-pane -pt test:selector | rg -q 'Tema'; then break; fi
    sleep 0.05
done
tmux -S "$TMUX_THEME_SOCKET" send-keys -t test:selector Down
wait_theme auto
tmux -S "$TMUX_THEME_SOCKET" send-keys -t test:selector Escape
wait_theme catppuccin-mocha
[[ $(tmux -S "$TMUX_THEME_SOCKET" show -gqv status-style) == "$before" ]]
"$cli" --list | rg -qx hackthebox
"$cli" --list | rg -qx auto
printf 'PASS: aplicação, prévia, persistência, cancelamento e validação de temas\n'
