# Dotfiles

Tema comum: HackTheBox (verde `#9fef00`, fundo `#141d2b`) no Alacritty, tmux, starship e Helix.

## Organização

A pasta `home/` espelha o diretório pessoal: arquivos ocultos ficam na raiz,
configurações de aplicativos em `.config/` e scripts em `.local/bin/`.
Use `ls -la home` para visualizar os arquivos ocultos.

| Arquivo no repositório | Destino |
|---|---|
| `home/.bashrc` | `~/.bashrc` |
| `home/.zshrc` | `~/.zshrc` |
| `home/.tmux.conf` | `~/.tmux.conf` |
| `home/.tmux-cheatsheet.txt` | `~/.tmux-cheatsheet.txt` |
| `home/.config/starship.toml` | `~/.config/starship.toml` |
| `home/.config/alacritty/` | `~/.config/alacritty/` |
| `home/.config/tmux/themes/` | `~/.config/tmux/themes/` |
| `home/.config/helix/` | `~/.config/helix/` |
| `home/.local/bin/` | `~/.local/bin/` (scripts do tmux) |

## Instalação em um Linux novo

Depois de clonar ou copiar este repositório, entre na pasta `Dotfiles` e execute:

```sh
./install.sh --dry-run
./install.sh --bootstrap --theme gruvbox
```

`--bootstrap` instala os pacotes disponíveis no gerenciador do sistema,
Oh My Zsh, zsh-autosuggestions, zsh-syntax-highlighting e JetBrainsMono Nerd
Font Mono. Os downloads usam os repositórios oficiais dos projetos. A fonte
usa a versão 3.5.1 e é conferida pelo SHA-256 publicado nessa release.
Não é necessário executar o instalador com `sudo`: somente o gerenciador
de pacotes pede elevação quando necessário.

Para instalar somente os arquivos, sem rede ou pacotes:

```sh
./install.sh
```

O instalador funciona a partir de qualquer diretório. Ele copia Bash, Zsh,
tmux, Alacritty, Starship, Helix e os scripts auxiliares, sem depender de
manter o checkout no mesmo lugar. Os temas e **Ctrl+Shift+T** já ficam
configurados. HackTheBox é o padrão de uma conta nova; uma escolha salva
é mantida nas reinstalações. Use `--theme NOME` para escolher outro tema.
Os ícones das linguagens continuam com as cores originais.

Arquivos diferentes e links simbólicos nos componentes instalados vão para
`${XDG_STATE_HOME:-~/.local/state}/dotfiles/backups/<data>-<pid>/`.
`manifest.tsv` registra cada destino e seu backup. Arquivos idênticos são
ignorados: executar novamente não cria backups desnecessários. As pastas
gerenciadas `alacritty/`, `helix/` e `tmux/themes/` são substituídas como
unidades, com backup completo; outras configurações da conta são preservadas.

`XDG_CONFIG_HOME`, `XDG_STATE_HOME` e `XDG_DATA_HOME` são respeitados. Para
instalar em uma home de teste, sem usar os diretórios XDG da conta atual:

```sh
./install.sh --target /tmp/dotfiles-teste --theme hackthebox
```

Não use `--bootstrap` nesse teste se não quiser instalar pacotes no sistema.
Pais que sejam links simbólicos são recusados antes da instalação: nesses
casos, indique o diretório real com XDG_* ou `--target`.

As opções também podem ser usadas separadamente:

```sh
./install.sh --packages      # pacman / apt-get / dnf
./install.sh --shell-tools   # Oh My Zsh e plugins
./install.sh --font          # Nerd Font na conta do usuário
./install.sh --help
```

Em Arch, Manjaro e Omarchy, os pacotes são instalados pelo pacman, com
atualização completa do sistema para evitar upgrades parciais. Em Debian,
Ubuntu e Fedora, pacotes indisponíveis nos repositórios configurados são
informados e ignorados. Confira a lista de dependências pendentes ao final;
versões antigas da distribuição podem precisar de fontes de pacotes mais
recentes para Alacritty, tmux, fzf ou ferramentas como Starship e Yazi.
O instalador não adiciona PPAs, COPRs ou repositórios de terceiros.

Validado no Manjaro stable: os 24 pacotes do bootstrap estão disponíveis nos
repositórios configurados, incluindo `ttf-jetbrains-mono-nerd`. O Alacritty usa
a família `JetBrainsMono Nerd Font Mono`. Para instalar:

```sh
./install.sh --dry-run --bootstrap --theme gruvbox
./install.sh --bootstrap --theme gruvbox
```

Os testes instalam os arquivos em diretórios temporários e simulam o pacman
e os downloads do bootstrap; também verificam que uma falha do pacman preserva
as configurações existentes. Essa validação não executa uma atualização real
do sistema. Para repetir os testes específicos:

```sh
python3 -B -m unittest discover -s tests -p test_install.py -k manjaro -v
```

Ele não muda seu shell de login, não instala runtimes de linguagens e não
recarrega sessões tmux abertas. Abra um novo terminal após instalar. Mise,
asdf, Neovim e PipeWire são opcionais; integrações só são ativadas quando
disponíveis. Para o atalho pessoal `t`, defina `TRANSLATE_CLI_SCRIPT` com o
caminho do projeto translate-cli.

## Dependências

Requer Linux com Bash, Alacritty >= 0.14, tmux >= 3.3 e fzf >= 0.48.
Os demais recursos usam Starship, zoxide, eza, bat e uma Nerd Font.
Clipboard: wl-clipboard no Wayland, xclip/xsel no X11 ou OSC 52 pelo tmux.

O Zsh usa Oh My Zsh com os plugins `git`, `zsh-autosuggestions` e
`zsh-syntax-highlighting`. Os popups do tmux usam Helix (`helix` ou `hx`), lazygit, yazi e less.
O Helix está configurado para usar `clangd` e `clang-format` em projetos C.

## Temas do tmux

Instale também `home/.config/tmux/themes/` em `~/.config/tmux/themes/` e
`home/.local/bin/tmux-theme` em `~/.local/bin/tmux-theme` (executável).
O script requer Bash, fzf e `flock` (util-linux). A pasta `~/.local/bin`
deve estar no `PATH` para executar o comando diretamente.

Abra o seletor com **Ctrl+Shift+T** no Alacritty (mesmo sem tmux),
com `tmux-theme` no terminal ou com **Ctrl-a T** dentro do tmux:

- **↑/↓, clique ou roda do mouse:** prévia imediata no Alacritty e nas sessões tmux existentes.
- **Enter:** confirma e salva em `${XDG_STATE_HOME:-~/.local/state}/tmux/theme`.
- **Esc / Ctrl-C:** restaura o visual anterior sem salvar.

As paletas usam as cores dos projetos originais, adaptadas ao layout deste
painel: fundo sólido, bordas finas, sessão e janelas à esquerda, Git e hora
à direita. Não é necessário instalar os plugins completos dos temas.

| Tema no seletor | Referência |
|---|---|
| `hackthebox` | Paleta original deste repositório |
| `catppuccin-mocha` | [Catppuccin Mocha](https://github.com/catppuccin/tmux) — escuro, tons pastel |
| `catppuccin-latte` | [Catppuccin Latte](https://github.com/catppuccin/tmux) — claro |
| `dracula` | [Dracula](https://github.com/dracula/tmux) — cinza escuro e roxo |
| `gruvbox` | [Gruvbox Dark](https://github.com/alacritty/alacritty-theme/blob/master/themes/gruvbox_dark.toml) — contraste médio, tons quentes |
| `nord` | [Nord](https://github.com/nordtheme/tmux) — tons frios, azul e ciano |
| `tokyo-night` | [Tokyo Night](https://github.com/janoamaral/tokyo-night-tmux) — azul noturno |

As fontes exatas das cores estão registradas nos arquivos `.theme`.
`auto` lê as cores do tema atual do Omarchy (caminho atual ou legado);
no GNOME acompanha a preferência claro/escuro com Catppuccin Mocha/Latte.
A sincronização de Auto é consultada no intervalo da barra (5 segundos).
Fora desses ambientes, Auto usa Catppuccin Mocha.

```sh
tmux-theme --list             # listar os temas disponíveis
tmux-theme --apply dracula      # aplicar e salvar sem abrir a lista
tmux-theme --restore          # reaplicar a escolha salva
```

Para adicionar uma paleta, crie `~/.config/tmux/themes/nome.theme` usando
um dos arquivos existentes como modelo. Nomes aceitam letras minúsculas,
números, hífen e sublinhado; as cores usam `#RRGGBB`. Os arquivos são
lidos como dados, nunca executados. `auto` é um nome reservado.

A escolha vale para todas as sessões do servidor tmux; só é permitido um
seletor aberto por usuário, pois o arquivo de cores do Alacritty é compartilhado. O seletor sincroniza as cores do tmux e do Alacritty. Fonte e opacidade
continuam configuradas no emulador de terminal.

### Verificação

`python3 -B -m unittest discover -s tests -v` também verifica o instalador
em homes temporárias: backup, reinstalação, links, XDG e simulação.
Nenhum pacote é instalado durante esses testes.

Execute `bash tests/tmux-theme.sh` para validar as paletas e a persistência
em um servidor tmux temporário, sem interferir nas sessões em uso.

Para testar o seletor com o fzf real em um terminal virtual, sem criar
sockets, execute `python3 -B -m unittest discover -s tests -v`. Essa suíte
simula somente o transporte de comandos do tmux; não substitui o teste
de integração com um servidor real.

A aplicação de um tema força as sessões, janelas e painéis já existentes
a herdarem suas cores: remove sobrescritas locais de aparência, restaura
o layout padrão da barra e redesenha todos os clientes conectados ao
mesmo servidor. Atalhos, processos e barras ocultas (`status off`) são
preservados. Cancelar o seletor restaura também as opções visuais locais
e os layouts de barra anteriores.

## Atalho do Alacritty

**Ctrl+Shift+T** executa `~/.local/bin/terminal-theme`, que abre uma janela
independente com o seletor. O programa em primeiro plano não recebe
comandos nem é interrompido. O atalho funciona sem sessões tmux abertas.

O arquivo principal do Alacritty importa `theme.toml` na mesma pasta. O
seletor atualiza esse fragmento com fundo, texto, cursor, seleção e as
16 cores ANSI do tema. Todas as janelas que usam essa configuração e
recarregamento automático acompanham a prévia; Enter mantém a escolha
para as próximas aberturas e Esc restaura o arquivo anterior.

Instale `home/.local/bin/terminal-theme` junto com `tmux-theme` e copie
os dois arquivos em `home/.config/alacritty/`. As paletas `.theme` incluem
os campos `color0` a `color15` para manter a identidade de cada tema no
terminal. `--restore` reaplica a escolha salva mesmo sem servidor tmux;
novas sessões recebem a escolha ao carregar a configuração do tmux.

Sem tmux aberto, Auto consulta o tema do ambiente ao abrir o seletor ou
reaplicar a escolha. A atualização periódica continua disponível enquanto
há tmux com a barra de status ativa.

## Cores do prompt e das buscas

O Starship usa cores ANSI para o diretório, Git e símbolo do prompt,
que acompanham a paleta selecionada na interface. Os ícones de linguagens
preservam suas cores originais; o texto de versão acompanha o tema. O layout e os símbolos do prompt são preservados.
As buscas do fzf e o próprio seletor também usam as cores básicas do terminal.

Em shells já abertos, execute `source ~/.zshrc` uma vez para atualizar as
opções do fzf. A configuração do Starship é lida ao desenhar o próximo
prompt; depois disso, trocar o tema recolore os elementos que usam ANSI.

A troca também envia as cores diretamente às instâncias abertas do Alacritty
via `alacritty msg config --window-id -1`, cobrindo todas as janelas de cada
processo encontrado nos sockets do usuário. Essa atualização modifica somente
`colors.*`; fonte e outras preferências em runtime são preservadas. Cancelar
a prévia reenvia a paleta anterior. Se o fragmento de cores estiver ausente,
ele é recriado com o tema atual antes de abrir a lista.

Falhas ao enviar as cores para uma instância são registradas em
`~/.local/state/tmux/alacritty-errors.log`, sem perder a escolha salva. O
HackTheBox usa o verde vivo `#9fef00` tanto na cor normal quanto na brilhante.
