# 06 - Configuração Target

- Vídeo: https://www.youtube.com/watch?v=_GZeRgii1Bg
- Modelo: gemini-3.8-flash

---

## Resumo

O vídeo apresenta a configuração do módulo **Target** do software externo "PokeTibia Bot" (voltado ao jogo PokeTibia / OT Pokémon). O tutorial ensina a configurar o reconhecimento visual de alvos normais e "shinies" por meio de prints recortados da lista de batalha (*Battle*), a definição do comportamento de ataque (*Lure*, *Auto Attack*, etc.), a gestão de revives para finalizar grupos de monstros (*boxes*), a temporização e automação de combos de habilidades, e o fluxo seguro de captura de Pokémon raros.

---

## Funcionalidades

### 1. Captura e Lista de Alvos (Target Normal e Target Shiny)
* **Nome:** Target Normal / Target Shiny (Seção de Reconhecimento de Alvos).
* **O que faz e como configura:**
  * Permite ao bot identificar quais criaturas atacar na lista de batalha do jogo.
  * O usuário clica no botão `Print Target` (para monstros comuns) ou `Print Target Shiny` (para variantes shinies).
  * O sistema exibe uma instrução na tela: *"Clique e segure o botão DIREITO do mouse para capturar o Target"*.
  * O usuário clica com o botão direito diretamente no centro do ícone/rosto do monstro dentro da janela *Battle* do jogo. A imagem capturada passa a ser exibida no quadro de visualização da interface.
  * Permite adicionar múltiplos alvos (ex.: *Print Target 1*, *Print Target 2*), selecionáveis por caixas de combinação, para hunts que contenham diferentes espécies (como Pinsir, Meganium, etc.).
  * Conta com o botão `Del Mouse` para remover capturas/alvos indesejados e uma caixa com checkbox `+ Cooldown` para tempo de espera entre seleções de alvo.
* **Como parece funcionar por baixo:**
  * **Inferência técnica:** O bot utiliza captura de tela/leitura de pixels baseada em correspondência de padrões visuais (*template matching* via OpenCV ou similar). Ao clicar com o botão direito, ele define uma região retangular de interesse (ROI) e salva os pixels recortados para fazer varredura em tempo real na janela *Battle*. O bot não lê a memória do processo para obter os IDs das criaturas, operando de forma 100% visual/externa.
* **Limitações, bugs e dicas:**
  * **Dica/Aviso do autor:** O clique deve ser feito estritamente no centro do rosto/corpo do Pokémon na lista *Battle*.
  * **Bug alertado:** Se o print pegar a borda branca de seleção ou as barras laterais que se movem, o algoritmo de reconhecimento visual falhará/irá "bugar", impedindo que o bot identifique o alvo corretamente.
* **Minutagem:** 04:44 a 06:26 (demonstração prática); introdução conceitual em 00:07 a 00:12.

---

### 2. Gestão de Revives (Revive Normal e 2º Revive)
* **Nome:** Revives / 2º Revive.
* **O que faz e como configura:**
  * Controla o uso automatizado do item Revive pelo personagem para curar o Pokémon durante o combate contra uma *box* (grupo de monstros).
  * **Campos:**
    * Checkbox e campo numérico de quantidade para o revive principal.
    * Checkbox e campo numérico para `2º Revive` (visível em 00:18).
  * O usuário ativa o `2º Revive` caso seu Pokémon não cause dano suficiente para liquidar a *box* inteira utilizando apenas uma rotação e um único revive.
* **Como parece funcionar por baixo:**
  * **Inferência técnica:** Monitoramento de tempo ou de status de vida do Pokémon via leitura de tela/pixels na barra de HP, seguido pelo envio de hotkey simulada ou clique virtual no slot do item Revive. O segundo revive é acionado após o término da primeira rotação do combo caso os alvos ainda estejam vivos.
* **Limitações, bugs e dicas:**
  * **Dica do autor:** Essencial para personagens de nível mais baixo cujos Pokémon têm atributos menores e necessitam de uma sobrevida extra para limpar o spawn.
* **Minutagem:** 00:12 a 00:31.

---

### 3. Modos de Ataque e Mecânica de Fuga (Modos de Ataque & Fugir)
* **Nome:** Modos de ataque (`Auto Attack`, `Lure Attack`, `Attack por Quantidade`) e Checkbox `Fugir`.
* **O que faz e como configura:**
  * Menu suspenso onde o usuário define a estratégia de combate do bot:
    * `Lure Attack`: O personagem junta um grupo (*lure*) antes de desferir os ataques em área. Modo mais recomendado pelo autor.
    * `Attack por Quantidade`: Ataca ao atingir um número determinado de monstros agrupados.
    * `Auto Attack`: Focado em alvos individuais ou contínuos sem necessidade de lurar.
    * `Fugir` (Checkbox): Força o personagem a recuar antes de usar o Revive.
* **Como parece funcionar por baixo:**
  * **Dito no vídeo:** O bot analisa a presença de inimigos e, com a opção `Fugir`, move o personagem para longe do alcance direto do monstro antes de invocar/curar.
  * **Inferência técnica:** Simulação de passos no teclado (setas ou teclas WASD) em direção oposta à posição do monstro na tela para quebrar o contato antes de disparar a tecla do item Revive.
* **Limitações, bugs e dicas:**
  * **Dica do autor:** Manter o `Fugir` sempre marcado para evitar mortes instantâneas (*insta-kill*), impedindo que o revive seja executado colado em monstros perigosos (ex.: Pinsir).
  * O `Auto Attack` é recomendado para contas muito fracas/iniciais (nível 1).
* **Minutagem:** 00:32 a 01:16.

---

### 4. Configurações Especiais para Alvos Shiny
* **Nome:** Seção Target Shiny (Comportamento de Ataque e Delay).
* **O que faz e como configura:**
  * Define regras específicas caso surja um Pokémon Shiny na tela:
    * `Revives`: Quantidade máxima de revives permitidos para gastar com o Shiny (exibido configurado com 10, com menção de que pode ser alterado para 20). O bot não gasta todos se o monstro morrer antes.
    * Checkbox `Atacar`:
      * **Marcado:** O bot interrompe imediatamente a rota/lure ao avistar o Shiny e foca nele de forma prioritária.
      * **Desmarcado:** O bot finaliza a *box* atual normalmente e mata o Shiny junto com os outros monstros lurados.
    * `Delay Shiny:` Campo numérico em milissegundos (exibido com `2500` ms). Determina quanto tempo o bot permanece parado após a morte do Shiny antes de tentar arremessar a Pokébola.
* **Como parece funcionar por baixo:**
  * **Dito no vídeo:** O delay dá tempo para o sistema executar o comando de captura sem que o personagem saia correndo ou tente continuar a rota.
  * **Inferência técnica:** Temporizador que bloqueia o loop de movimentação do cavebot, seguido do disparo da hotkey de captura/arremesso de pokébola.
* **Limitações, bugs e dicas:**
  * **Dica do autor:** Deixar o checkbox `Atacar` desmarcado é considerado mais seguro pelo narrador para evitar desorganização no posicionamento durante o lure.
  * Se o `Delay Shiny` for deixado em 0 ou muito baixo, o bot pode se mover antes de registrar o clique da pokébola, falhando a captura. O autor recomenda entre `1500 ms` e `2500 ms`.
* **Minutagem:** 01:17 a 02:42.

---

### 5. Configuração de Auto Combo
* **Nome:** Auto Combo (Temporizador e Rotação de Skills).
* **O que faz e como configura:**
  * **Botão do Combo:** O usuário clica no primeiro campo e pressiona a tecla que ativa o combo nativo do cliente de jogo (o autor utiliza a tecla `E`).
  * **Campos de Teclas Sequenciais:** 6 campos adicionais onde podem ser atribuídas teclas avulsas (ex.: `F8`, `F6`, `F5`) para jogadores em clientes que não possuem auto-combo nativo.
  * **Tempo do Combo:** Campo numérico (ms) para definir a duração total da rotação de magias (ex.: `2500` ms).
  * **Delay entre Skills:** Tempo de espera em milissegundos entre o envio de cada tecla da sequência (padrão exibido: `300` ms).
* **Como parece funcionar por baixo:**
  * **Dito no vídeo:** O bot pressiona uma tecla, aguarda o delay configurado (ex.: 300 ms), pressiona a próxima, e repete a cadeia.
  * **Inferência técnica:** Emulação de eventos de teclado a nível de sistema operacional (`keybd_event` ou `SendInput` no Windows) direcionados à janela ativa do cliente.
* **Limitações, bugs e dicas:**
  * **Ajuste fino:** Se o tempo do combo for muito longo, o personagem ficará parado sem fazer nada após as magias acabarem; se for muito curto, o bot cortará a animação das habilidades para soltar o revive antes da hora.
  * Cada Pokémon possui velocidades de animação e conjuração diferentes, exigindo calibração individual entre 2.0s e 2.5s.
* **Minutagem:** 02:43 a 04:42.

---

## Detalhes de Interface

1. **Janela Principal ("Simplify" / "PokeTibia Bot"):**
   * Janela flutuante compacta de cor escura (estilo moderno/flat).
   * Contém seis botões principais de navegação:
     * `Cavebot`
     * `Healing`
     * `Target`
     * `Loot/Drop`
     * `Catch`
     * `Darkness`
2. **Janela Modal "Target":**
   * **Cabeçalho:** Título "Target" centralizado com botão de fechar.
   * **Bloco Esquerdo:** Coluna dedicada ao `Target Normal`, com seletor de perfil/imagem, botão de captura visual, botão de deleção e campo de cooldown.
   * **Bloco Direito:** Coluna dedicada ao `Target Shiny`, espelhando a estrutura do bloco normal.
   * **Bloco Central/Inferior:**
     * Subpainel de Revives e Modos de Ataque com caixas de marcação e seletores de quantidade.
     * Subpainel de Auto Combo com entrada para tecla mestre, 6 botões de atalho sequencial e caixas de texto com rótulos `Tempo do Combo (ms)` e `Delay entre Skills (ms)`.
     * Pré-visualizações gráficas em tempo real das imagens salvas após os recortes.

---

## Observações Técnicas e Inferências

* **Arquitetura Baseada em Visão Computacional Externa:**
  * O software opera de forma totalmente desacoplada da memória do executável do jogo (não injeta DLLs nem faz leitura de ponteiros/RAM para identificar alvos). Ele baseia seu funcionamento na leitura gráfica da tela e no envio de comandos de periféricos simulados (mouse/teclado).
* **Dependência da Estabilidade da UI do Jogo:**
  * Por depender de correspondência visual na lista de batalha, qualquer alteração gráfica externa (zoom, redimensionamento de janela, temas de interface do cliente, sobreposição de janelas ou mudanças na barra de vida) interfere diretamente na precisão do algoritmo.
* **Sincronismo via Delays Rígidos:**
  * A automação não recebe feedback direto do estado do jogo (como flags de "ataque finalizado" ou "monstro capturado"). O fluxo é governado inteiramente por timers em milissegundos configurados manualmente pelo usuário (`Delay Shiny`, `Tempo do Combo`, `Delay entre Skills`).
