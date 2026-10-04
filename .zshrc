# =========================
# Powerlevel10k instant prompt
# =========================
# (desativado: usando starship)
# if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
#   source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
# fi

# =========================
# Oh My Zsh
# =========================
export ZSH="$HOME/.oh-my-zsh"
export PATH="${ASDF_DATA_DIR:-$HOME/.asdf}/shims:$PATH"

ZSH_THEME=""  # prompt via starship

plugins=(
  git
  zsh-autosuggestions
  zsh-syntax-highlighting
)

source $ZSH/oh-my-zsh.sh

export PATH="$HOME/.cargo/bin:$PATH"

# =========================
# Aliases
# =========================
alias ls='eza --icons --group-directories-first --git --color=always'
alias ll='eza -lh --icons --group-directories-first --git --color=always'
alias la='eza -lha --icons --group-directories-first --git --color=always'
alias tree='eza --tree --icons'

alias bat='bat --style=auto --paging=always'
alias grep='grep --color=auto'

alias lsblk='lsblk -o NAME,SIZE,MOUNTPOINT,TYPE,FSTYPE,RM,RO,LABEL,UUID'

alias lvim='nvim'

alias ..='cd ..'
alias ...='cd ../..'

alias t='ruby ~/Documents/Github/translate-cli/translater.rb'

# =========================
# Functions
# =========================
vdo_audio() {
    echo "Criando dispositivos virtuais de áudio..."
    echo "-> Captura: VDO_Input (Sink)"
    echo "-> Reprodução: Microfone_VDO (Source)"
    echo "Pressione CTRL+C para encerrar."

    pw-loopback \
        -m '[FL FR]' \
        --capture-props='media.class=Audio/Sink node.name=vdo_input node.description="VDO_Input"' \
        --playback-props='media.class=Audio/Source node.name=vdo_mic node.description="Microfone_VDO"'
}

# =========================
# Powerlevel10k config
# =========================
# [[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh

# zoxide (z projeto) e fzf (Ctrl-r histórico, Ctrl-t arquivos, Alt-c pastas)
# só ativam se estiverem instalados
command -v zoxide >/dev/null && eval "$(zoxide init zsh)"
if command -v fzf >/dev/null; then
  source <(fzf --zsh)
  export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border=rounded --color=bg+:#394260,fg+:#a3aed2,hl:#769ff0,hl+:#7aa2f7,pointer:#769ff0,prompt:#769ff0,border:#394260"
fi

# Starship (prompt) — deve ficar por último
eval "$(starship init zsh)"


# Added by Antigravity CLI installer
export PATH="/home/wilian/.local/bin:$PATH"
