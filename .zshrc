export TERMINAL="alacritty"
export COLORTERM=truecolor
export CARGO_PATH=/mnt/Kingston256G/.cargo/
export HELIX_RUNTIME=$HOME/.config/helix
export JAVA_HOME=/home/wilian/.jdk/jdk-20.0.1

# PATH
export PATH=$HOME/.local/bin:$HOME/.cargo/bin:$CARGO_PATH/bin:$JAVA_HOME/bin:$PATH

export PATH=$PATH:/home/wilian/.spicetif

# Use powerline
USE_POWERLINE="true"

# Source manjaro-zsh-configuration
#if [[ -e /usr/share/zsh/manjaro-zsh-config ]]; then
#  source /usr/share/zsh/manjaro-zsh-config
#fi
# Use manjaro zsh prompt
#if [[ -e /usr/share/zsh/manjaro-zsh-prompt ]]; then
#  source /usr/share/zsh/manjaro-zsh-prompt
#fi

# Uncomment the following line to use case-sensitive completion.
CASE_SENSITIVE="false"

eval "$(starship init zsh)"

# Load ZSH plugins
source /home/wilian/.zs h/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
source ~/.zsh/zsh-autosuggestions/zsh-autosuggestions.zsh

# Aliases
alias ls="exa --icons --group-directories-first"
alias bat="bat --style=auto"
alias lsblk="lsblk -o NAME,SIZE,MOUNTPOINT,TYPE,FSTYPE,RM,RO,LABEL"
alias replays="cd /home/wilian/Games/league-of-legends/drive_c/users/wilian/Documents/League\ of\ Legends/Replays/"
alias books="cd /home/wilian/Documents/Estudos/Books/"
alias t="ruby /home/wilian/Documents/Github/translate-cli/translater.rb"


# ASDF config
. $HOME/.asdf/asdf.sh

# Save autosuggestions historic
autoload -Uz compinit && compinit
HISTFILE=~/.zsh_history
HISTSIZE=10000
SAVEHIST=20000
setopt inc_append_history
setopt hist_ignore_all_dups
setopt hist_ignore_space
setopt hist_ignore_dups
setopt hist_lex_words
setopt EXTENDED_HISTORY


