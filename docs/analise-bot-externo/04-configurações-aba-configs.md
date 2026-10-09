# 04 - Configurações Aba Configs

- Vídeo: https://www.youtube.com/watch?v=VQGRU9IvWRc
- Modelo: gemini-3.8-flash

---

Abaixo está o levantamento técnico detalhado e exaustivo das configurações demonstradas no vídeo **"Configurações Aba Configs"** da playlist *Tutorial Pokemon Aliiance V3*.

---

## Resumo
O vídeo apresenta a janela de configurações globais de atalhos e parâmetros operacionais do bot externo *PokeTibia Bot* para o jogo OT Pokémon. O usuário demonstra o mapeamento das teclas do cliente do jogo diretamente no bot, associando habilidades de suporte, modos de combate, controle de movimentação e itens consumíveis (como poções e diferentes tipos de pokébolas para captura condicional). Por fim, o narrador instrui a manter os valores padrão de tolerância de imagem e o gatilho visual do modo de emergência.

---

## Funcionalidades

### Tecla Defesa
1. **Nome da funcionalidade:** Tecla Defesa
2. **O que faz e configuração:** Mapeia a tecla de atalho responsável por ativar a habilidade defensiva do Pokémon ativo (no exemplo, o movimento *Confide* do Fearow). O usuário clica no botão "Tecla Defesa", abrindo uma caixa de diálogo modal com a mensagem *"Pressione uma tecla ou botão do mouse"*, e pressiona `F9`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* O usuário afirma que salva o atalho correspondente à skill de buff/defesa configurada na barra do jogo.
   - *Inferência:* Emulação de envio de teclas virtuais (via APIs do Windows como `keybd_event`, `SendInput` ou mensagens `PostMessage`/`WM_KEYDOWN` direcionadas à janela do cliente do OT Pokémon).
4. **Limitações, dicas e observações:** O autor destaca que o atalho varia conforme o Pokémon utilizado e as habilidades disponíveis na barra de ações.
5. **Minutagem:** 00:05 – 00:23

---

### Tecla Medicine
1. **Nome da funcionalidade:** Tecla Medicine
2. **O que faz e configuração:** Define o atalho rápido para uso do item de cura de status (Medicine). Ao clicar no botão, a janela modal de captura é aberta e o usuário pressiona a tecla `End`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* Apenas a atribuição do botão para o Medicine.
   - *Inferência:* Envio de tecla virtual para disparar a *hotkey* correspondente no jogo quando o bot detecta um status negativo (ex.: poison, burn, sleep via módulo de cura/healer).
4. **Limitações, dicas e observações:** Nenhuma ressalva feita além de vincular a tecla ao atalho correto do jogo.
5. **Minutagem:** 00:24 – 00:27

---

### Tecla Revive
1. **Nome da funcionalidade:** Tecla Revive
2. **O que faz e configuração:** Configura o atalho para reviver o Pokémon desmaiado. O usuário clica no botão correspondente e aperta a tecla `R`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* O autor menciona explicitamente que é possível atribuir tanto uma tecla do teclado quanto botões do mouse.
   - *Inferência:* Interceptação do evento de entrada (hook de teclado/mouse) na interface do bot para armazenar o código da tecla/botão a ser simulado no jogo.
4. **Limitações, dicas e observações:** Flexibilidade para usar clique de mouse em vez de tecla do teclado.
5. **Minutagem:** 00:27 – 00:34

---

### Modo Ofensivo e Modo Defensivo
1. **Nome da funcionalidade:** Modo Ofensivo / Modo Defensivo
2. **O que faz e configuração:** Mapeia as teclas que alternam a postura de combate do personagem/Pokémon no cliente (equivalente aos modos de ataque balanceado/ofensivo/defensivo do Tibia). O usuário reconfigura o Modo Ofensivo para `L` e o Modo Defensivo para `K`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* Atalhos do jogo já estavam gravados, mas ele reatribui para demonstrar.
   - *Inferência:* Disparo de teclas para alterar a postura de combate conforme regras internas das rotinas de ataque e sobrevivência do bot.
4. **Limitações, dicas e observações:** Deve refletir fielmente as hotkeys de combate configuradas no client do OT Pokémon.
5. **Minutagem:** 00:34 – 00:44

---

### Poke Stop
1. **Nome da funcionalidade:** Poke Stop
2. **O que faz e configuração:** Define a tecla que interrompe comandos/ataques ou a movimentação imediata do Pokémon/personagem (função Stop/Esc). Configurada no vídeo pressionando a barra de espaço (`Space`).
3. **Como parece funcionar por baixo:** 
   - *Dito:* Mapeamento da tecla de parada no espaço.
   - *Inferência:* Emulação da tecla de parada de ação do cliente (comum para cancelar perseguição de alvos ou interromper movimentação em waypoints).
4. **Limitações, dicas e observações:** Recomenda-se utilizar uma tecla de acesso fácil como a barra de espaço.
5. **Minutagem:** 00:44 – 00:50

---

### Tecla Stun
1. **Nome da funcionalidade:** Tecla Stun
2. **O que faz e configuração:** Mapeia uma habilidade de controle de grupo/atordoamento em área ou em alvo único (ex.: habilidade de furacão do Fearow que paralisa os monstros). O usuário demonstra a skill no jogo (ativada no `F5`), abre a caixa de diálogo do bot e grava a tecla `F5`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* Habilidade usada para "parar os inimigos".
   - *Inferência:* O bot aciona essa tecla ciclicamente durante a rotina de combate/targeting para mitigar dano recebido.
4. **Limitações, dicas e observações:** O jogador deve identificar qual skill do seu Pokémon atual possui efeito de imobilização/controle de grupo.
5. **Minutagem:** 00:50 – 01:08

---

### Tecla Order
1. **Nome da funcionalidade:** Tecla Order
2. **O que faz e configuração:** Mapeia a ação "Order" (comando nativo do OT Pokémon para direcionar o Pokémon, montar, voar ou mover para uma posição). O narrador explica que utiliza no ponto (`.`) ou no botão do meio do mouse (Scroll/Mouse3). Ele clica no campo e define a tecla `.` (ponto final).
3. **Como parece funcionar por baixo:** 
   - *Dito:* Mostra que aceita ponto do teclado ou clique central do mouse.
   - *Inferência:* Disparo do comando "Order" seguido de coordenadas na tela para reposicionar o Pokémon ou interagir com obstáculos durante o percurso.
4. **Limitações, dicas e observações:** O usuário pode alternar entre botões físicos do mouse ou caracteres alfanuméricos/pontuação conforme sua ergonomia.
5. **Minutagem:** 01:09 – 01:24

---

### Tecla Potion
1. **Nome da funcionalidade:** Tecla Potion
2. **O que faz e configuração:** Configura o atalho para uso automático de poções de cura. O narrador abre as configurações de barra de ação no jogo, demonstra a configuração do objeto Potion associado à opção *Smart Use* (Use on Pokémon/Self) e define a hotkey no jogo como `F10`. Em seguida, abre a opção no bot e grava `F10`.
3. **Como parece funcionar por baixo:** 
   - *Dito:* Mostra a tela do jogo marcando "Smart Use" e salvando a barra de ação.
   - *Inferência:* O módulo *Healer* monitora a barra de vida (via pixel ou leitura de memória) e, ao cruzar o limiar de HP mínimo, envia o atalho virtual cadastrado aqui.
4. **Limitações, dicas e observações:** Exige que o jogador configure a ação dentro do jogo como *Smart Use* para que a poção seja aplicada automaticamente no alvo correto sem exigir seleção com o cursor do mouse.
5. **Minutagem:** 01:25 – 01:40

---

### Tecla PokeBall 1 e Tecla PokeBall 2
1. **Nome da funcionalidade:** Teclas de Pokébola (Catch 1 e Catch 2)
2. **O que faz e configuração:** Mapeia até dois tipos distintos de pokébolas para a rotina de captura automática (*Catch*). O narrador exemplifica o uso da *Ultra Ball* na Tecla PokeBall 1 (`F11`) e da *Premier Ball* na Tecla PokeBall 2 (`F10`). Ele explica que o módulo Catch permite definir qual bola lançar em cada criatura (por exemplo: Ultra Ball em Shinies e Premier Ball em Dittos).
3. **Como parece funcionar por baixo:** 
   - *Dito:* Explica a divisão entre "Catch 1" e "Catch 2" que será vinculada na aba de captura. Mostra a configuração do item com *Smart Use* nas barras de ação do cliente.
   - *Inferência:* As rotinas de reconhecimento visual ou eventos de combate detectam a morte do monstro (corpo no chão) e disparam a respectiva tecla de captura configurada de acordo com a lista de prioridades.
4. **Limitações, dicas e observações:** Suporta duas categorias de bolas em paralelo para economizar consumíveis caros contra alvos comuns e priorizar alvos raros.
5. **Minutagem:** 01:40 – 02:33

---

### Tolerância
1. **Nome da funcionalidade:** Tolerância
2. **O que faz e configuração:** Campo numérico (exibindo o valor padrão `25` com setas incrementais). Ajusta o índice de tolerância de variação de cor/pixel para os algoritmos de reconhecimento de imagem do bot.
3. **Como parece funcionar por baixo:** 
   - *Dito:* O narrador recomenda explicitamente não alterar e deixar no padrão.
   - *Inferência:* Parâmetro de limiar (*threshold*) em algoritmos de *Template Matching* (OpenCV ou similar) ou comparação de matrizes de pixels RGB/HSV, compensando variações de iluminação, transparências ou sombras no cliente do jogo.
4. **Limitações, dicas e observações:** O autor enfatiza que não há necessidade de alterar o valor padrão (25).
5. **Minutagem:** 02:34 – 02:37

---

### Modo Emergência
1. **Nome da funcionalidade:** Modo Emergencia
2. **O que faz e configuração:** Área que exibe uma imagem modelo/amostra (template recortado). O autor instrui a não alterar nada neste campo e manter a imagem padrão carregada.
3. **Como parece funcionar por baixo:** 
   - *Dito:* "Vocês nem mexem também. Podem deixar essa imagem aí mesmo."
   - *Inferência:* Reconhecimento de padrão gráfico (*pattern/image matching*) na interface do cliente (ex.: detecção visual de aviso crítico de vida, desconexão iminente ou ícone de perigo) que, ao ser encontrado na tela com base na tolerância, aciona a rotina de emergência (como deslogar, usar teleporte ou pausar o bot).
4. **Limitações, dicas e observações:** Deve ser deixado com a imagem padrão pré-carregada para evitar falhas de detecção.
5. **Minutagem:** 02:38 – 02:43

---

## Detalhes de Interface

- **Janela Principal ("Simply / PokeTibia Bot"):**
  - Janela flutuante compacta de cor escura contendo 8 botões de alternância organizados em grade 4x2: `Attack`, `Healer`, `Walk/Loot`, `Catch`, `Waypoint`, `Configs`, `Target`, `All Active`.
- **Janela Modal de Configurações ("Configurações"):**
  - Janela horizontal em estilo Windows Forms / Win32 clássico com borda padrão e fundo cinza-claro.
  - Grade superior com 11 botões de captura de atalhos em linha única:
    - *Tecla Defesa*
    - *Tecla Medicine*
    - *Tecla Revive*
    - *Modo Ofensivo*
    - *Modo Defensivo*
    - *Poke Stop*
    - *Tecla Stun*
    - *Tecla Order*
    - *Tecla Potion*
    - *Tecla PokeBall 1*
    - *Tecla PokeBall 2*
  - Abaixo da grade de atalhos:
    - Campo rotulado *Tolerância* com controle *numeric up/down* (definido em 25).
    - Campo rotulado *Modo Emergencia* contendo uma caixa de pré-visualização de imagem (*picture box*).
- **Caixa de Captura de Tecla ("Pressione uma tecla ou botão do mouse"):**
  - Janela modal simples contendo uma caixa de texto centralizada que aguarda o próximo pressionamento de tecla do teclado ou evento de mouse e fecha automaticamente ao salvar o código de entrada.

---

## Observações Técnicas e Inferências

- **Natureza do Software:** Trata-se de um bot externo (*pixel-based macro*). O uso de termos como "Tolerância" e o componente visual de "Modo Emergência", aliado à exigência de configuração manual de teclas idênticas às *Action Bars* do cliente do jogo, reforça que a ferramenta atua majoritariamente por **análise visual de tela** (busca de padrões/templates gráficos de barras de vida, monstros e itens) combinada com **emulação de teclado e mouse**, sem injeção direta de DLL ou manipulação de memória de processo (*hooking* interno).
- **Dependência do Cliente Oficial:** Toda a lógica de uso inteligente de itens (curar a si mesmo, usar no Pokémon) é delegada aos recursos nativos de *Action Bar / Smart Use* do próprio jogo. O bot apenas se encarrega de acionar as teclas virtuais no momento em que os eventos de gatilho são detectados.
