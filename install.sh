#!/usr/bin/env bash
# Instala dotfiles por cópia; não depende da localização futura do checkout.
set -euo pipefail
repo_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
target_home=${HOME:?HOME não definido}
target_explicit=0
dry_run=0
packages=0
shell_tools=0
font=0
frosted_glass=0
selected_theme=
stage=
backup_dir=
fail() { printf 'install.sh: %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'HELP'
Uso: ./install.sh [opções]

Sem opções: copia os dotfiles, faz backup das diferenças e verifica dependências.
Não instala pacotes, não acessa a rede e não troca o shell de login.

  --dry-run          Mostra o plano sem escrever arquivos nem acessar a rede
  --bootstrap        Instala pacotes disponíveis, Oh My Zsh/plugins e Nerd Font
  --packages         Instala pacotes via pacman, apt-get ou dnf (pede sudo)
  --shell-tools      Clona Oh My Zsh e seus dois plugins oficiais
  --font             Instala JetBrainsMono Nerd Font Mono (v3.5.1, SHA-256)
  --frosted-glass    Instala/configura desfoque no GNOME da sessão atual
  --theme NOME       Tema inicial; mantém a escolha existente quando omitido
  --target CAMINHO   Home de destino (isolado dos XDG_* da conta atual)
  -h, --help         Mostra esta ajuda

Exemplos:
  ./install.sh --dry-run
  ./install.sh --bootstrap --theme ayu-minimal
  ./install.sh --bootstrap --theme ayu-minimal --frosted-glass
  ./install.sh --target /tmp/nova-home --theme hackthebox
HELP
}
while (($#)); do
    case $1 in
        --dry-run) dry_run=1 ;;
        --bootstrap) packages=1; shell_tools=1; font=1 ;;
        --packages) packages=1 ;;
        --shell-tools) shell_tools=1 ;;
        --font) font=1 ;;
        --frosted-glass) frosted_glass=1 ;;
        --theme|--target)
            (($# >= 2)) || fail "Falta valor para $1"
            if [[ $1 == --theme ]]; then selected_theme=$2
            else target_home=$2; target_explicit=1; fi
            shift ;;
        -h|--help) usage; exit 0 ;;
        *) fail "Opção desconhecida: $1" ;;
    esac
    shift
done
[[ $(uname -s) == Linux ]] || fail 'Este instalador é destinado ao Linux.'
[[ $target_home == /* && $target_home != / ]] || fail 'Use um destino absoluto diferente de /.'
[[ $target_home != *$'\n'* && $target_home != *$'\t'* ]] || fail 'Destino não pode conter tabulação ou quebra de linha.'
target_home=$(realpath -ms -- "$target_home")
[[ $target_home != / ]] || fail 'O destino não pode ser a raiz do sistema.'
[[ $target_home != "$repo_dir" && $target_home != "$repo_dir/"* ]] || fail 'O destino não pode ficar dentro do próprio repositório.'
if (( target_explicit )); then
    config_dir=$target_home/.config
    state_dir=$target_home/.local/state
    data_dir=$target_home/.local/share
else
    config_dir=${XDG_CONFIG_HOME:-$target_home/.config}
    state_dir=${XDG_STATE_HOME:-$target_home/.local/state}
    data_dir=${XDG_DATA_HOME:-$target_home/.local/share}
fi
bin_dir=$target_home/.local/bin
for directory in "$config_dir" "$state_dir" "$data_dir"; do
    [[ $directory == /* ]] || fail 'XDG_CONFIG_HOME, XDG_STATE_HOME e XDG_DATA_HOME devem ser absolutos.'
done
if (( frosted_glass && ! dry_run )); then
    (( ! target_explicit )) || fail '--frosted-glass não pode ser usado com --target; execute na conta da sessão GNOME atual.'
    desktop=${XDG_CURRENT_DESKTOP:-}
    [[ ${desktop^^} == *GNOME* ]] || fail '--frosted-glass requer uma sessão GNOME ativa.'
    for tool in python3 gnome-shell gnome-extensions gsettings gdbus glib-compile-schemas; do
        command -v "$tool" >/dev/null || fail "Instale $tool antes de usar --frosted-glass."
    done
    python3 -c 'import sys; raise SystemExit(sys.version_info < (3, 11))' || fail '--frosted-glass requer Python >= 3.11.'
fi
if [[ -z $selected_theme && -r $state_dir/tmux/theme ]]; then
    IFS= read -r selected_theme < "$state_dir/tmux/theme" || :
    if [[ ! $selected_theme =~ ^[a-z0-9][a-z0-9_-]*$ ]] ||
       [[ $selected_theme != auto && ! -f $repo_dir/home/.config/tmux/themes/$selected_theme.theme ]]; then
        selected_theme=
    fi
fi
selected_theme=${selected_theme:-ayu-minimal}
[[ $selected_theme =~ ^[a-z0-9][a-z0-9_-]*$ ]] || fail "Tema inválido: $selected_theme"
[[ $selected_theme == auto || -f $repo_dir/home/.config/tmux/themes/$selected_theme.theme ]] || fail "Tema desconhecido: $selected_theme"
# Nunca instalar através de um link de diretório pai sem fazer backup dele.
# Links nos próprios componentes serão movidos para o backup e substituídos.
check_parents() {
    local parent
    parent=$(dirname -- "$1")
    while [[ $parent != / && $parent != . ]]; do
        [[ ! -L $parent ]] || fail "Diretório pai é link simbólico: $parent. Use o caminho real via XDG_* ou --target."
        [[ ! -e $parent || -d $parent ]] || fail "Diretório pai não é uma pasta: $parent"
        parent=$(dirname -- "$parent")
    done
}
declare -a sources=() destinations=() labels=()
add() { sources+=("$1"); destinations+=("$2"); labels+=("$3"); }
for name in .bashrc .zshrc .tmux.conf .tmux-cheatsheet.txt; do
    add "home/$name" "$target_home/$name" "home/$name"
done
for name in alacritty helix tmux/themes starship.toml; do
    add "home/.config/$name" "$config_dir/$name" "config/$name"
done
# Overlay visual do LazyVim: nunca substituir a configuração nvim inteira.
for name in colors/ayu-dark.lua lua/dotfiles/ayu.lua lua/plugins/visual.lua; do
    add "home/.config/nvim/$name" "$config_dir/nvim/$name" "config/nvim/$name"
done
for source in "$repo_dir/home/.local/bin/"*; do
    [[ -f $source ]] || continue
    name=${source##*/}
    add "home/.local/bin/$name" "$bin_dir/$name" "home/.local/bin/$name"
done
add theme-choice "$state_dir/tmux/theme" state/tmux/theme
for destination in "${destinations[@]}"; do check_parents "$destination"; done
backup_dir=$state_dir/dotfiles/backups/$(date +%Y%m%d-%H%M%S)-$$
check_parents "$backup_dir/manifest.tsv"
if (( dry_run )); then
    printf 'SIMULAÇÃO — nenhuma alteração será realizada.\nDestino: %s\nTema: %s\n' "$target_home" "$selected_theme"
    for destination in "${destinations[@]}"; do printf '  instalar com backup se necessário: %s\n' "$destination"; done
    (( ! packages )) || printf '  pacotes: detectar pacman/apt-get/dnf; instalar os disponíveis via sudo\n'
    (( ! shell_tools )) || printf '  git clone: Oh My Zsh, zsh-autosuggestions, zsh-syntax-highlighting\n'
    (( ! font )) || printf '  fonte: JetBrainsMono Nerd Font v3.5.1, validar SHA-256 e atualizar fontconfig\n'
    (( ! frosted_glass )) || printf '  vidro fosco: executar terminal-frosted-glass na sessão GNOME atual; pode baixar e habilitar Blur My Shell\n'
    exit 0
fi
stage=$(mktemp -d)
cleanup() { [[ -z $stage ]] || rm -rf -- "$stage"; }
trap cleanup EXIT
trap 'printf "Falha durante a instalação. Backups, se criados: %s\n" "$backup_dir" >&2' ERR
cp -a -- "$repo_dir/home" "$stage/home"
# Gera cores sem criar servidor tmux, enviar IPC ou alterar janelas abertas.
env XDG_CONFIG_HOME="$repo_dir/home/.config" \
    "$repo_dir/home/.local/bin/tmux-theme" --export-alacritty "$selected_theme" \
    > "$stage/home/.config/alacritty/theme.toml"
printf '%s\n' "$selected_theme" > "$stage/theme-choice"
as_root() {
    if (( EUID == 0 )); then "$@"
    else command -v sudo >/dev/null || fail 'sudo não está instalado.'; sudo "$@"; fi
}
install_packages() {
    local manager package
    local -a candidates available=()
    if command -v pacman >/dev/null; then
        # Atualização completa evita upgrades parciais em sistemas Arch.
        as_root pacman -Syu --needed git bash zsh alacritty tmux fzf starship zoxide \
            eza bat helix lazygit yazi wl-clipboard xclip less ripgrep fd \
            curl unzip fontconfig util-linux clang ttf-jetbrains-mono-nerd
        return
    elif command -v apt-get >/dev/null; then
        manager=apt
        as_root apt-get update
        candidates=(git bash zsh alacritty tmux fzf starship zoxide eza bat helix lazygit yazi
            wl-clipboard xclip less ripgrep fd-find curl unzip fontconfig util-linux clang clang-format)
    elif command -v dnf >/dev/null; then
        manager=dnf
        candidates=(git bash zsh alacritty tmux fzf starship zoxide eza bat helix lazygit yazi
            wl-clipboard xclip less ripgrep fd-find curl unzip fontconfig util-linux clang clang-tools-extra)
    else
        fail 'Gerenciador não suportado. Instale as dependências manualmente e execute sem --packages.'
    fi
    for package in "${candidates[@]}"; do
        if { [[ $manager == apt ]] && apt-cache show "$package" >/dev/null 2>&1; } ||
           { [[ $manager == dnf ]] && dnf -q info "$package" >/dev/null 2>&1; }; then
            available+=("$package")
        else
            printf 'Pacote ausente nos repositórios configurados: %s (será listado na verificação final).\n' "$package" >&2
        fi
    done
    ((${#available[@]})) || fail 'Nenhum pacote encontrado nos repositórios.'
    if [[ $manager == apt ]]; then as_root apt-get install "${available[@]}"
    else as_root dnf install "${available[@]}"; fi
}
clone_if_missing() {
    local url=$1 destination=$2 pending
    if [[ -e $destination || -L $destination ]]; then
        printf 'Mantendo instalação existente: %s\n' "$destination"
        return
    fi
    check_parents "$destination"
    mkdir -p -- "$(dirname -- "$destination")"
    pending=$(mktemp -d "${destination}.XXXXXX")
    if ! git clone --depth 1 "$url" "$pending"; then
        rm -rf -- "$pending"
        fail "Falha ao baixar $url"
    fi
    mv -- "$pending" "$destination"
}
install_shell_tools() {
    command -v git >/dev/null || fail 'Instale git antes de usar --shell-tools.'
    clone_if_missing https://github.com/ohmyzsh/ohmyzsh.git "$target_home/.oh-my-zsh"
    clone_if_missing https://github.com/zsh-users/zsh-autosuggestions.git "$target_home/.oh-my-zsh/custom/plugins/zsh-autosuggestions"
    clone_if_missing https://github.com/zsh-users/zsh-syntax-highlighting.git "$target_home/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting"
}
install_font() {
    local family= version=v3.5.1 archive=JetBrainsMono.zip digest font_file destination
    command -v fc-list >/dev/null && family=$(fc-list : family) || :
    if [[ $family == *'JetBrainsMono Nerd Font Mono'* ]]; then
        printf 'JetBrainsMono Nerd Font Mono já está instalada.\n'; return
    fi
    for tool in curl unzip sha256sum awk; do command -v "$tool" >/dev/null || fail "Instale $tool para baixar a fonte."; done
    curl --fail --location --retry 2 --proto '=https' --tlsv1.2 \
        "https://github.com/ryanoasis/nerd-fonts/releases/download/$version/$archive" -o "$stage/$archive"
    curl --fail --location --retry 2 --proto '=https' --tlsv1.2 \
        "https://github.com/ryanoasis/nerd-fonts/releases/download/$version/SHA-256.txt" -o "$stage/SHA-256.txt"
    digest=$(awk '/(^|[ /(*])JetBrainsMono\.zip([ )]|$)/ {for(i=1;i<=NF;i++) if(length($i)==64 && $i ~ /^[0-9a-fA-F]+$/) {print $i; exit}}' "$stage/SHA-256.txt")
    [[ $digest =~ ^[[:xdigit:]]{64}$ ]] || fail 'Checksum da fonte não encontrado na lista oficial.'
    printf '%s  %s\n' "$digest" "$stage/$archive" | sha256sum --check --status || fail 'Checksum da fonte não corresponde ao oficial.'
    unzip -q "$stage/$archive" -d "$stage/fonts"
    destination=$data_dir/fonts/JetBrainsMonoNerdFont
    check_parents "$destination/font.ttf"
    mkdir -p -- "$destination"
    while IFS= read -r -d '' font_file; do cp -a -- "$font_file" "$destination/"; done \
        < <(find "$stage/fonts" -type f \( -name '*.ttf' -o -name 'OFL.txt' -o -iname '*license*' \) -print0)
    command -v fc-cache >/dev/null && fc-cache -f "$destination" || :
}
(( ! packages )) || install_packages
(( ! shell_tools )) || install_shell_tools
(( ! font )) || install_font
installed=0
unchanged=0
for i in "${!sources[@]}"; do
    source=$stage/${sources[i]}
    destination=${destinations[i]}
    if [[ ! -L $destination ]] && diff -qr -- "$source" "$destination" >/dev/null 2>&1; then
        # diff não compara permissões; mantém executáveis os helpers instalados.
        if [[ ! -f $source || ! -x $source || -x $destination ]]; then
            unchanged=$((unchanged + 1)); continue
        fi
    fi
    if [[ -e $destination || -L $destination ]]; then
        backup=$backup_dir/${labels[i]}
        mkdir -p -- "$(dirname -- "$backup")"
        mv -- "$destination" "$backup"
        printf '%s\t%s\n' "$destination" "$backup" >> "$backup_dir/manifest.tsv"
    fi
    mkdir -p -- "$(dirname -- "$destination")"
    cp -a -- "$source" "$destination"
    installed=$((installed + 1))
done
printf '\nDotfiles: %s componentes instalados, %s já estavam atualizados.\nTema: %s\n' "$installed" "$unchanged" "$selected_theme"
[[ ! -d $backup_dir ]] || printf 'Backup: %s\n' "$backup_dir"
if (( frosted_glass )); then
    printf '\nConfigurando vidro fosco na sessão GNOME atual...\n'
    env XDG_CONFIG_HOME="$config_dir" XDG_STATE_HOME="$state_dir" XDG_DATA_HOME="$data_dir" \
        "$bin_dir/terminal-frosted-glass"
fi
missing=()
for tool in zsh tmux alacritty fzf starship zoxide eza flock less; do
    command -v "$tool" >/dev/null || missing+=("$tool")
done
command -v bat >/dev/null || command -v batcat >/dev/null || missing+=(bat)
command -v helix >/dev/null || command -v hx >/dev/null || missing+=(helix)
for tool in lazygit yazi clangd clang-format; do command -v "$tool" >/dev/null || missing+=("$tool"); done
if ((${#missing[@]})); then printf 'Dependências ainda ausentes: %s\n' "${missing[*]}"; fi
for tool in alacritty tmux fzf; do
    minimum=0.14; flag=--version
    [[ $tool != tmux ]] || { minimum=3.3; flag=-V; }
    [[ $tool != fzf ]] || minimum=0.48
    if command -v "$tool" >/dev/null; then
        version=$("$tool" "$flag" 2>/dev/null || :)
        if [[ $version =~ ([0-9]+\.[0-9]+(\.[0-9]+)?) ]]; then
            version=${BASH_REMATCH[1]}
            if ! printf '%s\n%s\n' "$minimum" "$version" | sort -VC; then
                printf 'Atualize %s: versão %s encontrada; requer >= %s.\n' "$tool" "$version" "$minimum" >&2
            fi
        fi
    fi
done
printf 'Abra um novo terminal. Atalho dos temas: Ctrl+Shift+T no Alacritty.\n'
printf 'Opacidade: Ctrl+Shift+O. Preferência da barra de título: Ctrl+Shift+D (vale na próxima abertura).\n'
printf 'Para usar Zsh como shell de login, altere-o nas preferências da sua conta.\n'
