# Caminhos da conta atual; sem depender do nome do usuário ou do checkout.
typeset -U path PATH
path=("$HOME/.local/bin" "$HOME/.cargo/bin" $path)

# Gerenciadores de runtimes são opcionais e instalados separadamente.
if command -v mise >/dev/null 2>&1; then
    eval "$(mise activate zsh)"
elif [[ -d ${ASDF_DATA_DIR:-$HOME/.asdf}/shims ]]; then
    path=("${ASDF_DATA_DIR:-$HOME/.asdf}/shims" $path)
fi

export ZSH="${ZSH:-$HOME/.oh-my-zsh}"
ZSH_THEME=""  # prompt via Starship
if [[ -r $ZSH/oh-my-zsh.sh ]]; then
    plugins=(git)
    for plugin in zsh-autosuggestions zsh-syntax-highlighting; do
        if [[ -r ${ZSH_CUSTOM:-$ZSH/custom}/plugins/$plugin/$plugin.zsh ||
              -r ${ZSH_CUSTOM:-$ZSH/custom}/plugins/$plugin/$plugin.plugin.zsh ]]; then
            plugins+=($plugin)
        fi
    done
    unset plugin
    source "$ZSH/oh-my-zsh.sh"
fi

if command -v eza >/dev/null 2>&1; then
    alias ls='eza --icons --group-directories-first --git --color=always'
    alias ll='eza -lh --icons --group-directories-first --git --color=always'
    alias la='eza -lha --icons --group-directories-first --git --color=always'
    alias tree='eza --tree --icons'
fi
if command -v bat >/dev/null 2>&1; then
    alias bat='bat --style=auto --paging=always'
elif command -v batcat >/dev/null 2>&1; then
    alias bat='batcat --style=auto --paging=always'
fi
alias grep='grep --color=auto'
command -v lsblk >/dev/null 2>&1 && alias lsblk='lsblk -o NAME,SIZE,MOUNTPOINT,TYPE,FSTYPE,RM,RO,LABEL,UUID'
command -v nvim >/dev/null 2>&1 && alias lvim='nvim'
alias ..='cd ..'
alias ...='cd ../..'

# Integração pessoal opcional: exporte TRANSLATE_CLI_SCRIPT com o caminho.
if [[ -n ${TRANSLATE_CLI_SCRIPT:-} && -r $TRANSLATE_CLI_SCRIPT ]]; then
    t() { ruby "$TRANSLATE_CLI_SCRIPT" "$@"; }
fi

vdo_audio() {
    command -v pw-loopback >/dev/null 2>&1 || {
        print -u2 'Instale PipeWire para usar vdo_audio.'; return 1
    }
    print 'Criando VDO_Input e Microfone_VDO. Ctrl-C para encerrar.'
    pw-loopback -m '[FL FR]' \
        --capture-props='media.class=Audio/Sink node.name=vdo_input node.description="VDO_Input"' \
        --playback-props='media.class=Audio/Source node.name=vdo_mic node.description="Microfone_VDO"'
}

command -v zoxide >/dev/null 2>&1 && eval "$(zoxide init zsh)"
if command -v fzf >/dev/null 2>&1; then
    # fzf >= 0.48 traz a integração embutida; versões anteriores usam arquivos.
    if fzf --zsh >/dev/null 2>&1; then
        source <(fzf --zsh)
    else
        for bindings in /usr/share/fzf/key-bindings.zsh /usr/share/doc/fzf/examples/key-bindings.zsh; do
            if [[ -r $bindings ]]; then source "$bindings"; break; fi
        done
        unset bindings
    fi
    export FZF_DEFAULT_OPTS="--height 40% --layout=reverse --border=rounded --color=bg:-1,fg:-1,bg+:-1,fg+:-1,hl:4,hl+:12,pointer:5,prompt:5,border:8,header:6,info:8"
fi

# Deve ficar por último; o Zsh também funciona antes de instalar Starship.
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init zsh)"
fi
