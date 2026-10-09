# 11 - Configuração do Catch em Shinies

- Vídeo: https://www.youtube.com/watch?v=jb5CWSavQus
- Modelo: gemini-3.8-flash

---

Aqui está o levantamento técnico detalhado do vídeo tutorial com base em tudo o que foi dito pelo narrador e exibido na interface visual.

---

## Resumo
O vídeo demonstra a configuração do sistema de captura visual (*Catch*) em criaturas raras (*Ditto* e *Shinies*) utilizando o software externo **PokeAliianceBot** no jogo OT Pokémon (Poketibia). O usuário ensina como cadastrar referências visuais de corpos derrotados via recorte de tela com o botão direito do mouse nas listas de alvos (*Catch 1* e *Catch 2*). Demonstra-se também a adição de múltiplas amostras de imagem para aumentar a precisão de detecção e a ativação final do gatilho automático de lançamento de pokébolas.

---

## Funcionalidades

### 1. Sistema de Captura por Imagem (Aba `Imagem [A]` / Recorte de Sprites)
1. **Nome da funcionalidade/aba/módulo:**
   * Aba: `Imagem [A]` (submódulo de gerenciamento de templates visuais / detecção de alvos).
2. **O que faz e como o usuário configura:**
   * **Função:** Permite registrar e remover amostras gráficas (templates de recorte de tela) dos corpos dos Pokémon derrotados para que o bot localize a posição exata na grade do jogo e execute a ação de arremesso de pokébolas.
   * **Campos, menus e opções visíveis:**
     * **Menu Suspenso (Dropdown):** Permite selecionar a ação e a categoria de alvo:
       * `Adicionar Catch1` / `Remover Catch1`
       * `Adicionar Catch2` / `Remover Catch2`
       * `Adicionar Catch3` / `Remover Catch3`
     * **Mensagem Overlay/Instrução no Topo da Tela:** Ao selecionar uma ação de adição, aparece o prompt: *"Clique e segure o BOTÃO DIREITO do mouse para capturar a Imagem."*
     * **Caixa delimitadora (Bounding Box):** O usuário clica e arrasta sobre a sprite do corpo do Pokémon para recortar uma sub-região de pixels.
     * **Área de Pré-visualização:** Exibe a imagem/trecho capturado logo abaixo da seleção.
     * **Barra de status/precisão:** Barra horizontal indicando a porcentagem de correspondência ou limiar de sensibilidade (mostra `0%` na interface durante a edição).
3. **Como funciona por baixo:**
   * *O que foi DITO no vídeo:* O usuário seleciona a opção de print, usa o clique direito para arrastar uma área pequena sem pegar o chão, e o bot salva a imagem na respectiva categoria (*Catch 1* ou *Catch 2*). Também foi dito que é possível salvar mais de uma imagem para a mesma categoria para tornar a detecção mais assertiva.
   * *INFERÊNCIA técnica:* Trata-se de **Template Matching** (varredura gráfica / busca de padrão de pixels via `BitBlt` ou captura da janela do cliente). Quando o bot localiza os pixels compatíveis dentro do viewport do jogo, ele calcula as coordenadas centrais da correspondência para despachar os eventos de clique.
4. **Limitações, dicas e observações mencionadas:**
   * **Evitar chão/cenário:** Não se deve capturar áreas do chão ou fundo do mapa, apenas a parte interna da sprite da criatura, para evitar falhas de matching devido a variações de terreno.
   * **Tamanho do recorte:** Não precisa ser uma imagem grande; um recorte pequeno e central é suficiente e mais eficiente.
   * **Sobreposição de corpos:** Quando vários Pokémon morrem no mesmo local ou lado a lado, as sprites podem se sobrepor. O narrador orienta a recortar uma parte que costuma ficar sempre visível (ex.: nas costas do Pinsir).
   * **Múltiplos templates:** Recomenda-se tirar mais de um print da mesma criatura (ângulos ou detalhes ligeiramente diferentes) para que o bot não perca o Shiny caso a primeira imagem falhe.
5. **Minutagem:**
   * `00:05` a `00:39` (Configuração da imagem para o Ditto no *Catch 2*).
   * `00:54` a `01:45` (Remoção de imagem anterior e cadastro de múltiplas imagens do Shiny Pinsir no *Catch 1*).

---

### 2. Controle e Disparo do Catch Automático (Aba `Controle [A]`)
1. **Nome da funcionalidade/aba/módulo:**
   * Aba: `Controle [A]` / Seção de automação de captura (`Pokemon [A] Controle [B]`).
2. **O que faz e como o usuário configura:**
   * **Função:** Habilita a rotina ativa em segundo plano que monitora a tela e dispara as ações do mouse/teclado para lançar pokébolas assim que um corpo correspondente a uma imagem cadastrada for encontrado.
   * **Campos e opções visíveis no módulo:**
     * Checkbox `Catch`: Ativa/desativa o loop do auto-catch.
     * Checkbox `Disconnect Alarme`: Alarme sonoro ou desconexão programada.
     * Checkbox `Stop Move`: Pausa a movimentação do personagem enquanto executa a captura.
     * Checkbox `Message Alert`: Alerta quando mensagens do jogo ocorrem.
     * Campos de Hotkeys/Slots à direita:
       * `Slot 01: [34]`
       * `Slot 02: [35]`
       * `Slot 03: [36]`
3. **Como funciona por baixo:**
   * *O que foi DITO no vídeo:* Ao marcar a caixinha `Catch`, o bot localiza o corpo previamente registrado e *"já joga a pokébola automaticamente"*. O narrador cita que diferentes categorias (*Catch 1*, *Catch 2*) são associadas a tipos diferentes de pokébolas configuradas previamente no módulo de CaveBot (ex.: Premier Ball no *Catch 2* e Ultra Ball no *Catch 1*).
   * *INFERÊNCIA técnica:* O bot opera via simulação de eventos de mouse e teclado (Win32 API: `PostMessage`, `SendMessage` ou `mouse_event`/`keybd_event`). Ao encontrar o sprite do corpo, ele simula a hotkey da pokébola associada (ou uso via crosshair) e clica com precisão nas coordenadas da tela onde a imagem foi encontrada.
4. **Limitações, dicas e observações mencionadas:**
   * O narrador reforça que o bot só executa a captura se a caixa `Catch` for ativada após salvar o template.
   * Caso o jogador use o mesmo tipo de pokébola para tudo, a separação de categorias não interfere na bola, mas permite separar prioridades de captura.
5. **Minutagem:**
   * `00:40` a `00:44` (Ativação e execução automática no Ditto).
   * `01:46` a `01:52` (Ativação e execução automática no Shiny Pinsir).

---

## Detalhes de Interface

A interface do **PokeAliianceBot** é uma janela desktop nativa padrão do Windows (estilo WinForms / C# ou C++ Win32 GUI), dividida nas seguintes áreas:

1. **Abas Principais:**
   * `Controle [A]`: Painel operacional das funções ativas (habilidades, cura, captura, alarmes).
   * `Imagem [A]`: Painel de gravação, ajuste e deleção de templates visuais.

2. **Grupos visíveis na aba `Controle [A]`:**
   * **Grupo `Habilidades`:**
     * Checkbox `Auto-Atk [F5-F10]`: Automação da rotação de ataques pelas hotkeys de função.
     * Checkbox `Potion`: Cura automática com poções.
   * **Grupo `Pokemon` / `Pokemon [A] Controle [B]`:**
     * Checkboxes: `Catch`, `Disconnect Alarme`, `Stop Move`, `Message Alert`.
     * Atribuições numéricas dos slots: `Slot 01: 34`, `Slot 02: 35`, `Slot 03: 36` (códigos virtuais de tecla ou IDs de interface).

3. **Elementos visíveis na aba `Imagem [A]`:**
   * Seletor de modo/slot via combobox (`Adicionar Catch1`, `Adicionar Catch2`, `Remover Catch...`).
   * Botão de exclusão/limpeza de imagem carregada (botão circular/X visível ao lado da pré-visualização).
   * Indicador numérico percentual (`0%`) com barra de calibragem/tolerância de matching de cor/imagem.

4. **Elementos de Feedback In-Game:**
   * Linha de status no canto superior esquerdo do jogo com instruções textuais para captura via botão direito do mouse.

---

## Observações Técnicas e Inferências

* **Arquitetura Externa Baseada em Pixel/GDI (Screen-Scraping):**
  * O bot funciona externamente ao cliente do jogo (não parece injetar DLLs na memória do Tibia/OTClient neste módulo específico, já que depende de captura visual via drag-and-drop na tela).
  * O método de captura baseia-se em recortes RGB/Bitmap estáticos, comparados periodicamente com a área renderizada da tela do jogo.
* **Sistema de CaveBot e Priorização (Mencionado verbalmente):**
  * O narrador menciona a existência prévia de configurações no módulo `CaveBot`, onde o usuário define qual ID/tipo de pokébola (Premier Ball vs. Ultra Ball) corresponde aos índices `Catch 1` e `Catch 2`.
  * Isso permite que monstros comuns recebam pokébolas normais/Ultra Balls (`Catch 1`), enquanto alvos de alto valor (como Ditto e Shinies) recebam pokébolas especiais (`Catch 2`), evitando gasto desnecessário de itens raros.
* **Tolerância a Falsos Positivos e Falsos Negativos:**
  * O uso de múltiplas capturas para a mesma categoria (`Catch 1` com 2 amostras diferentes do Pinsir) indica que o software mantém uma lista/array de templates para um mesmo identificador, iterando sobre todas as imagens cadastradas a cada ciclo de verificação.
