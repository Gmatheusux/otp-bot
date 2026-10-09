# 08 - Configurando uma hunt

- Vídeo: https://www.youtube.com/watch?v=UC9nb21wyG0
- Modelo: gemini-3.8-flash

---

## Resumo

O vídeo demonstra detalhadamente a configuração e a execução do módulo de caça automatizada (**CaveBot**) no software **PokeTibia Bot** (versão associada ao "Pokemon Aliiance V3"). O narrador ensina a criar uma rota de caça definindo pontos no minimapa do próprio jogo (zoom calibrado), associar ordens de ataque direcionadas para cada marcação, ajustar tempos de espera para agrupamento de monstros (*lure* e fechar *box*), e iniciar o bot com a ferramenta de monitoramento (**Hunt Analyzer**) ativa.

---

## Funcionalidades

### 1. Sistema de Waypoints e Calibração do Minimapa
* **O que faz e como configura:**  
  O bot utiliza as marcações nativas do minimapa do cliente OTClient/Poketibia para guiar a movimentação do personagem.  
  * **Passo a passo:** O usuário define pontos onde deseja que o personagem pare e agrupe os monstros (*lure*).
  * **Calibração de Zoom:** É exigido colocar o minimapa no zoom máximo para frente e pressionar exatamente **4 vezes o botão de diminuir zoom** ("-") para manter o padrão 4x esperado pelo bot.
  * **Marcações no cliente:** O usuário clica com o botão direito no chão/minimapa e seleciona *Create Map Mark*, definindo símbolos em ordem sequencial (por exemplo, estrelas ou 'X') para cada parada.
* **Mecanismo de funcionamento:**  
  * **Inferência técnica:** O bot realiza varredura e reconhecimento visual (correspondência de padrões de imagem/pixel matching) na área da interface reservada ao minimapa para identificar os ícones colocados pelo jogador e calcular para onde clicar e caminhar.
* **Limitações e dicas:**  
  * O espaçamento entre os pontos deve permitir que a próxima marcação esteja visível no quadrante do minimapa; se ficar fora da tela, o bot quebra/trava (como demonstrado e corrigido aos 06:08).
* **Minutagem:** 00:18 – 00:40; 06:07 – 06:25.

---

### 2. Módulo CaveBot (Configuração de Rota, Lure e Habilidades)
* **O que faz e como configura:**  
  Controla a sequência de waypoints, comandos de combate e tempos em cada parada da caça.
  * **Opções e Checkboxes no topo da janela:**
    * `Follow`: Seguir alvos/rota.
    * `Battle`: Integração com a lista de batalha.
    * `Loot`: Coleta automática de itens.
    * `Minimap`: Habilita navegação guiada por minimapa.
    * `Active`: Ativação do módulo.
    * `Dragonite Fly Mode`: Modo específico de movimentação aérea.
  * **Campos por Marcação (1ª a 8ª Marcação):**
    * Cada marcação possui um botão/status de carregamento (`Loading`), checkbox de ativação de ordem (`Order`), e o botão **"Posição"**: ao clicar em "Posição", uma moldura/mira branca aparece na tela do jogo para que o usuário clique no tile exato onde o comando do Pokémon ("Order") deve ser desferido (por exemplo, à esquerda ou à direita do personagem para direcionar o ataque em área longe de monstros distantes).
    * **Looting / Cooldown:** Tempo de espera em cada marcação. O narrador ajusta o tempo padrão para `3500` ms para dar tempo de o monstro fechar a *box* (rodear o personagem) antes de disparar o combo de dano.
* **Mecanismo de funcionamento:**  
  * **Dito no vídeo:** O botão "Posição" salva as coordenadas relativas da tela onde o comando deve ser clicado.
  * **Inferência técnica:** O bot simula cliques de mouse nas posições de tela configuradas (ou envia pacotes de ação/Order para os offsets definidos) e aguarda o temporizador configurado (cooldown) antes de avançar para a próxima marcação.
* **Limitações e dicas:**  
  * Ao definir a posição do "Order", deve-se evitar apontar na direção de *spawns* indesejados para não puxar mais monstros além do limite seguro (mencionado aos 02:01 e 03:04).
  * O narrador demonstra que caso o combo aconteça antes do agrupamento completo, deve-se elevar o tempo do cooldown na interface do CaveBot.
* **Minutagem:** 00:41 – 03:45; 05:10 – 05:30.

---

### 3. Integração com Target e Módulos de Combate
* **O que faz e como configura:**  
  Janela `Target` aberta pelo menu principal para definir o comportamento de ataque contra os alvos.
  * Exibe opções como `Target Normal`, seleção de listas de alvos, e modos de ataque (`Auto Attack`, `Lure Attack`, caixas de seleção de prioridade).
  * O narrador confirma que o Target já está pré-configurado no modo "Lure Attack" para funcionar em conjunto com as paradas de área do CaveBot.
* **Mecanismo de funcionamento:**  
  * **Inferência técnica:** Leitura da lista de batalha (*battle list*) por memória ou leitura de pixel, com envio de teclas de atalho/cliques de ataque programados conforme os monstros entram no raio de combate.
* **Limitações e dicas:**  
  * Se sobrarem apenas 1 ou 2 monstros após o combo de área, o bot finaliza individualmente ou segue para o próximo ponto de acordo com a regra de sobra estabelecida.
* **Minutagem:** 04:14 – 04:20; 06:40 – 06:50.

---

### 4. Controle Geral, Hotkeys Globais e Hunt Analyzer
* **O que faz e como configura:**  
  * **Atalho `Ctrl + F5`:** Abre/oculta a barra principal flutuante do bot (`PokeTibia Bot`), contendo botões para `CaveBot`, `Healing`, `Target`, `Level/Skill`, `Catch` e `Kill All Pokemon`. Também é usado como atalho de parada de emergência.
  * **Atalho `Ctrl + Y`:** Inicia ou pausa a execução do bot no jogo.
  * **Hunt Analyzer:** Ao iniciar via `Ctrl + Y`, uma caixa de diálogo pergunta se o usuário deseja abrir o *Hunt Analyzer*. Ao aceitar, surge no canto superior da tela um painel com métricas em tempo real:
    * Contagem de itens usados (`Revive`, `Potions`, `Medicine`).
    * Duração da sessão (`Tempo`).
    * Ganho de experiência e mortes por hora.
* **Mecanismo de funcionamento:**  
  * **Dito no vídeo:** O início é via `Ctrl + Y` e o menu principal via `Ctrl + F5`.
  * **Inferência técnica:** Hook global de teclado para detecção de atalhos; o *Hunt Analyzer* realiza OCR ou leitura direta dos contadores da interface/mensagens do chat do servidor para computar gastos e experiência.
* **Minutagem:** 04:08 – 04:36; 07:00 – 07:07.

---

## Detalhes de Interface

* **Janela Principal (PokeTibia Bot):** Barra escura e compacta com botões de acesso rápido aos módulos centrais (`CaveBot`, `Healing`, `Target`, `Level/Skill`, `Catch`, `Kill All Pokemon`, `Simplify`).
* **Janela CaveBot:**
  * Painel modular com botões superiores de alternância rápida de modos gerais.
  * Grade dividida em blocos numerados sequencialmente ("1ª Marcação", "2ª Marcação", etc.), cada qual com seu campo de status/arquivo, botão "Posição", e parâmetros de tempo/cooldown numérico.
* **Mira de Seleção de Tile ("Posição Order"):** Quadrado branco semi-transparente renderizado na tela do jogo que acompanha o cursor até a definição do clique.
* **Diálogos Modais:**
  * Caixa de confirmação com texto *"Você deseja abrir o Hunt Analyzer?"* (botões *Sim / Não*).
  * Painel de parada de emergência (*Pause / Resume / Stop*).

---

## Observações Técnicas e Inferências

1. **Abordagem Híbrida (Visão Computacional + Simulação de Entrada):**  
   O bot depende fortemente da calibragem geométrica do cliente (zoom 4x no minimapa, posições relativas na janela de jogo). Isso indica que a navegação é fortemente ancorada em leitura de tela e busca de imagens/pixels (*template matching* de ícones do minimapa), evitando injeção direta de memória ou manipulação profunda de pacotes na camada de navegação.
2. **Dependência de Campo de Visão (FOV) do Minimapa:**  
   O fato de o bot travar ou desconsiderar um waypoint se o ícone estiver fora da área visível do minimapa confirma a ausência de um sistema autônomo baseado em coordenadas absolutas do servidor (X, Y, Z); ele age estritamente como um operador automatizado que clica naquilo que o jogador humano veria na tela.
3. **Sincronia de Combate por Temporizadores:**  
   A estratégia de combate de área depende de temporizadores estáticos configurados pelo usuário (ex.: 3500 ms de *lure* antes de disparar habilidades), sem um cálculo dinâmico adaptativo de densidade de monstros ao redor, exigindo ajustes manuais na configuração da rota conforme o comportamento dos *spawns*.
