#!/usr/bin/env bash
# Instala os aplicativos de uso diário em Arch, Manjaro e Omarchy.
set -euo pipefail

# Repositórios oficiais (steam exige o repositório multilib habilitado).
official=(firefox helix bitwarden qpwgraph qbittorrent celluloid discord steam telegram-desktop)
# AUR, via yay.
aur=(spotify spotatui-bin)

dry_run=0
use_aur=1
fail() { printf 'install-packages.sh: %s\n' "$*" >&2; exit 1; }
usage() {
    cat <<'HELP'
Uso: ./install-packages.sh [opções]

Instala apenas o que ainda falta; pacotes já instalados são ignorados.

  --dry-run   Mostra o que seria instalado sem alterar o sistema
  --no-aur    Não instala os pacotes do AUR (spotify, spotatui-bin)
  -h, --help  Mostra esta ajuda
HELP
}
while (($#)); do
    case $1 in
        --dry-run) dry_run=1 ;;
        --no-aur) use_aur=0 ;;
        -h|--help) usage; exit 0 ;;
        *) fail "Opção desconhecida: $1" ;;
    esac
    shift
done
command -v pacman >/dev/null || fail 'Requer pacman (Arch, Manjaro ou Omarchy).'
(( EUID != 0 )) || fail 'Execute como usuário comum; o sudo é chamado quando necessário.'

missing() {
    local package
    for package in "$@"; do
        pacman -Qq -- "$package" >/dev/null 2>&1 || printf '%s\n' "$package"
    done
}
run() {
    if (( dry_run )); then printf '  [simulação] %s\n' "$*"; else "$@"; fi
}

mapfile -t need_official < <(missing "${official[@]}")
if [[ ${#need_official[@]} -gt 0 && " ${need_official[*]} " == *' steam '* ]] &&
   ! grep -q '^\[multilib\]' /etc/pacman.conf; then
    printf 'Aviso: [multilib] está desabilitado em /etc/pacman.conf; steam será ignorado.\n' >&2
    mapfile -t need_official < <(printf '%s\n' "${need_official[@]}" | grep -vx steam || :)
fi
if ((${#need_official[@]})); then
    printf 'Oficiais: %s\n' "${need_official[*]}"
    run sudo pacman -S --needed "${need_official[@]}"
else
    printf 'Oficiais: tudo já instalado.\n'
fi

if (( use_aur )); then
    mapfile -t need_aur < <(missing "${aur[@]}")
    if ((${#need_aur[@]})); then
        printf 'AUR: %s\n' "${need_aur[*]}"
        if command -v yay >/dev/null; then
            run yay -S --needed "${need_aur[@]}"
        else
            printf 'Aviso: yay não encontrado; instale-o ou use --no-aur. Pulando: %s\n' "${need_aur[*]}" >&2
        fi
    else
        printf 'AUR: tudo já instalado.\n'
    fi
fi
