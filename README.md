# Dotfiles

Dotfiles com temas integrados para Alacritty, tmux e Starship. Novas instalações
usam Ayu Minimal, com fundo quase preto; HackTheBox continua disponível.
O LazyVim recebe o visual Ayu Dark, e o Helix mantém sua configuração existente.

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
| `home/.config/nvim/` | Overlay visual sobre um LazyVim já instalado |
| `home/.local/bin/` | `~/.local/bin/` (temas, opacidade, moldura, vidro fosco e helpers do tmux) |

## Instalação em um Linux novo

Depois de clonar ou copiar este repositório, entre na pasta `Dotfiles` e execute:

```sh
./install.sh --dry-run
./install.sh --bootstrap --theme ayu-minimal
```

Para reproduzir também o vidro preto fosco no GNOME, execute na sessão gráfica
da própria conta, sem sudo:

```sh
./install.sh --dry-run --bootstrap --theme ayu-minimal --frosted-glass
./install.sh --bootstrap --theme ayu-minimal --frosted-glass
```

`--frosted-glass` executa o preset depois de instalar os arquivos. Requer
Python >= 3.11 e as ferramentas do GNOME já disponíveis; pode baixar a extensão
Blur My Shell do catálogo oficial, habilitá-la e aplicar 92% de opacidade às
instâncias do Alacritty. Esse passo exige acesso à sessão GNOME e à rede quando
a extensão ainda não está instalada. Não faz parte de `--bootstrap` sozinho.
Não pode ser usado com `--target` na instalação real; a simulação apenas mostra
o plano. Se o preset falhar, os dotfiles já copiados continuam instalados e o
erro é informado; execute `terminal-frosted-glass` novamente na sessão normal.

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
configurados, junto com **Ctrl+Shift+O** para opacidade e **Ctrl+Shift+D** para
a preferência da barra de título. Ayu Minimal é o padrão de uma conta nova; uma escolha salva
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
./install.sh --frosted-glass # desfoque no GNOME da sessão atual
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
disponíveis.

## Comportamento e visual separados

O instalador separa o que muda **como** você trabalha (zsh, tmux, helix,
starship, scripts `tmux-*`) do que muda **a aparência** (Alacritty, Ayu no
Neovim, scripts `terminal-*`).

```sh
./install.sh --no-visual   # só comportamento
./install.sh --visual      # comportamento + visual
```

Sem nenhuma das opções, o visual é instalado, exceto no **Omarchy**
(detectado por `omarchy-theme-set` ou `~/.config/omarchy`): lá o sistema de
temas dele controla as cores do terminal, do Neovim e do desktop, e os
dotfiles não as sobrescrevem. `--frosted-glass` exige o visual.

### Escolher componentes

Cada parte pode ser omitida com `--no-COMPONENTE`: `bash`, `zsh`, `tmux`,
`helix`, `starship` e `visual`. Exemplo para o Omarchy, mantendo só zsh e helix:

```sh
./install.sh --no-bash --no-tmux --no-starship --no-visual
```

Para escolher num menu, sem lembrar as opções:

```sh
./install.sh -i
```

O menu (Bash puro, sem dependências) lista os componentes e os extras
(pacotes, Oh My Zsh, fonte, vidro fosco) já marcados com o padrão detectado.
Digite os números para alternar (`a` marca tudo, `n` desmarca, Enter segue,
`q` sai), escolha o tema inicial e confirme o resumo. Ele só monta as mesmas
opções acima e lê a entrada padrão; com a entrada encerrada, nada é instalado.

`--no-tmux` pula toda a configuração do tmux (`.tmux.conf`, cheatsheet,
atalhos `tmux-*` e a barra). Com o visual ligado, continuam instalados o
`tmux-theme` e os temas, que o Alacritty usa para trocar de tema (`Ctrl+Shift+T`).

## Aplicativos

`install-packages.sh` instala os aplicativos de uso diário em Arch, Manjaro e
Omarchy: Firefox, Helix, Bitwarden, qpwgraph, qBittorrent, Celluloid, Discord,
Steam e Telegram (repositórios oficiais), mais Spotify e spotatui (AUR, via
`yay`). Só instala o que falta.

```sh
./install-packages.sh --dry-run   # mostra o plano
./install-packages.sh             # instala
./install-packages.sh --no-aur    # sem Spotify e spotatui
```

O Steam exige `[multilib]` habilitado em `/etc/pacman.conf`; se estiver
desabilitado, ele é ignorado com um aviso. A lista fica no topo do script.

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
painel: fundo sólido, bordas finas, sessão e janelas à esquerda; hostname,
CPU, modo do tmux, bateria e relógio à direita, com ícones Nerd Font.
Os campos são agrupados em blocos com o fundo de superfície da paleta;
a sessão usa a cor de destaque e modos ativos usam a cor de aviso.
O modo indica NORMAL, PREFIX, COPY e ZOOM (estados simultâneos aparecem juntos).
A CPU usa amostras de `/proc/stat`, atualizadas no intervalo de 5 segundos;
a primeira amostra mostra `--`. A bateria vem de `/sys/class/power_supply`,
indica carregamento e fica oculta em máquinas sem bateria. Com várias baterias,
exibe a média dos percentuais. Não é necessário instalar plugins dos temas.

| Tema no seletor | Referência |
|---|---|
| `hackthebox` | Paleta original deste repositório |
| `ayu-dark` | [Ayu Dark](https://github.com/alacritty/alacritty-theme/blob/master/themes/ayu_dark.toml) — fundo quase preto `#07090d`, destaques âmbar |
| `ayu-minimal` | Mesma paleta Ayu personalizada do LazyVim, com barra discreta, divisórias cinza e popups de borda simples |
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
O campo opcional `layout=minimal` ativa o layout discreto usado pelo
`ayu-minimal`; sem ele, o tema usa os blocos padrão da barra.

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

## Visual do LazyVim

O colorscheme local **`ayu-dark`** acompanha a paleta personalizada do terminal:
fundo `#07090d`, superfícies `#10141c`, âmbar `#ffb454`, verde `#9ccc42` e
vermelho `#ff4d5a`. A interface usa divisórias finas, janelas flutuantes com
borda simples, abas discretas e uma barra de status sem separadores grandes.
A proposta minimalista toma o [Lackluster](https://github.com/slugbyte/lackluster.nvim)
como referência; não é uma cópia da imagem do Reddit, que não pôde ser acessada.

A camada usa os plugins que o LazyVim já tem. Não modifica atalhos, LSP,
formatação, conclusão ou fontes de dados das barras; as alterações nos plugins
se limitam à apresentação. Não adiciona uma dependência de tema externa.

O instalador copia apenas `colors/ayu-dark.lua`, `lua/dotfiles/ayu.lua` e
`lua/plugins/visual.lua`, com backup dos arquivos existentes. Os demais
arquivos de `~/.config/nvim` são preservados. É necessário ter LazyVim instalado;
o overlay não instala nem substitui sua configuração base. Reinicie o Neovim
para carregar todo o visual. `:colorscheme ayu-dark` aplica apenas o tema em
uma instância já aberta. O tema do editor é fixo em Ayu; o seletor do terminal
continua independente.

## Barra de título do Alacritty

O padrão de novas instalações é `window.decorations = "none"`, sem barra de
título nem botões. **Ctrl+Shift+D** executa `terminal-decorations toggle`:
alterna a preferência entre `none` e `full`, sem abrir nem fechar janelas.
A alteração vale na próxima abertura do Alacritty. No Alacritty 0.17, a criação da janela
aplica as decorações; alterar a configuração por IPC não redesenha essa moldura.

```sh
terminal-decorations hide --new-window  # abrir sem barra de título
terminal-decorations show --new-window  # abrir com barra de título
terminal-decorations toggle             # mudar somente a preferência
terminal-decorations status
```

O script preserva as demais configurações e salva a versão anterior em
`${XDG_STATE_HOME:-~/.local/state}/alacritty-decorations/previous.toml`.

### Mover a janela sem barra no GNOME

Para mover a janela segurando **Ctrl + botão esquerdo do mouse** e arrastando,
execute no terminal da sua sessão GNOME, sem sudo:

```sh
gsettings set org.gnome.desktop.wm.preferences mouse-button-modifier '<Control>'
```

A preferência é persistente e vale para todas as janelas do GNOME, inclusive
o Alacritty sem decorações. Pode interferir em Ctrl+clique nos aplicativos.
O instalador dos dotfiles não altera essa preferência automaticamente.

Para consultar a configuração:

```sh
gsettings get org.gnome.desktop.wm.preferences mouse-button-modifier
```

Para voltar ao valor anterior desta sessão (**Super/Windows + arraste**):

```sh
gsettings set org.gnome.desktop.wm.preferences mouse-button-modifier '<Super>'
```

### Cantos arredondados no GNOME

Execute na sessão GNOME, sem sudo:

```sh
terminal-rounded-corners
```

Antes de instalar os dotfiles, também é possível executar diretamente:

```sh
~/Documentos/Github/Dotfiles/home/.local/bin/terminal-rounded-corners
```

O comando baixa a versão compatível da extensão
[Rounded Window Corners Reborn](https://extensions.gnome.org/extension/7048/rounded-window-corners-reborn/)
do catálogo oficial do GNOME e configura um raio de **12 px**, limitado ao
Alacritty. Janelas maximizadas ou em tela cheia permanecem com cantos retos.
Mantém as configurações de decorações e transparência do Alacritty.
Se a extensão recém-instalada não for reconhecida, saia e entre na sessão
GNOME e execute novamente o comando. O instalador comum dos dotfiles apenas
copia o comando; não instala nem ativa a extensão automaticamente.

As preferências anteriores da extensão ficam em
`~/.local/state/dotfiles/backups/*-rounded-corners-*/rounded-corners.dconf`,
respeitando `XDG_STATE_HOME`. Para desativar o efeito:

```sh
gnome-extensions disable rounded-window-corners@fxgn
```

Para restaurar as preferências, primeiro desative a extensão e então use o
arquivo de backup informado pelo comando:

```sh
dconf reset -f /org/gnome/shell/extensions/rounded-window-corners-reborn/
dconf load /org/gnome/shell/extensions/rounded-window-corners-reborn/ < /caminho/do/backup/rounded-corners.dconf
```

## Opacidade por janela

Para o aspecto de **vidro preto fosco**, use Ayu Minimal e execute, no terminal
normal da sua sessão GNOME, sem sudo:

```sh
terminal-frosted-glass
```

O comando requer Python >= 3.11, GLib e as ferramentas do GNOME. Se necessário,
baixa o Blur My Shell do catálogo oficial `extensions.gnome.org`, conferindo a
compatibilidade com a versão do GNOME antes de instalar. Configura desfoque
dinâmico moderado (sigma 24), limitado ao Alacritty, e mantém a opacidade do
ator da extensão em 255 para preservar o texto. Em instalações novas da
extensão, desativa seus efeitos no painel, dock e demais componentes.
Salva a opacidade do Alacritty em 92% e habilita a transparência dos fundos
coloridos; também tenta enviar esses ajustes por IPC às instâncias abertas.
As cores do tema não são alteradas pelo comando.

Se o GNOME não reconhecer a extensão recém-instalada, será necessário sair e
entrar na sessão e executar novamente o comando. As configurações anteriores
ficam em `~/.local/state/dotfiles/backups/`, respeitando `XDG_STATE_HOME`.
`terminal-frosted-glass --alacritty-only` configura somente a transparência,
sem baixar extensões ou ativar desfoque. O efeito fosco só estará ativo após
a extensão estar instalada, carregada e habilitada na sessão GNOME.

No Alacritty, **Ctrl+Shift+O** abre `terminal-opacity` em uma janela de controle.
**←** reduz a opacidade e **→** aumenta, em passos de 1%, de 10% a 100%.
A prévia modifica somente a janela que acionou o atalho, inclusive com tmux
aberto. Quando o atalho não fornece o identificador da janela, o controle
descobre as janelas pelos processos do usuário: escolhe automaticamente se
houver uma só, ou pede a seleção pelo fzf se houver várias. Na lista, ↑/↓ escolhe o destino e ←/→ inicia a prévia sem precisar de Enter.
A própria janela do controle é excluída. **Enter** mantém o ajuste nessa janela; **Esc**, Ctrl-C ou fechar o
controle restaura o valor anterior. Não altera a configuração global nem
a paleta; novas janelas continuam com a opacidade configurada no Alacritty.
Cada seta aplica a prévia por IPC imediatamente, incluindo os fundos coloridos
do tmux. Enter apenas mantém o ajuste. No Alacritty 0.17+, o controle consulta
a opacidade efetiva da janela; em versões anteriores usa o último ajuste
registrado ou a configuração. Esc também restaura a opção de transparência
dos fundos coloridos. O controle lembra os valores aplicados por ele
enquanto a janela estiver em uso.

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
