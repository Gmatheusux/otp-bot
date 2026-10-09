# 07 - Funcionamento da aba cavebot

- Vídeo: https://www.youtube.com/watch?v=mL7CHH-5fQo
- Modelo: gemini-3.8-flash

---

## Resumo

Este vídeo apresenta detalhadamente as opções de configuração da aba **Cavebot** do software de automação externa **PokeTibia Bot** (versão focada no servidor *Pokemon Aliiance*). O autor demonstra o funcionamento dos controles globais da caçada (combate, controle do pokémon via Order, parada, uso de revive e coleta de loot) e o sistema de rota por waypoints/marcações. São explicados os comportamentos de tempo de espera (tempo padrão vs. cooldown individual), definição de coordenadas do Order na tela, ativação de combate por ponto e suporte a escadas e grama alta.

---

## Funcionalidades

### 1. Battle (Módulo de Reconhecimento de Combate / Lista de Batalha)
* **O que faz e como configura:** Checkbox localizado no topo esquerdo da janela do Cavebot. Deve ser mantido ativado para que o bot reconheça os monstros na battle list e execute as ações ofensivas durante a rota.
* **Como funciona por baixo:** 
  * *Inferência:* Provavelmente realiza monitoramento visual (leitura de pixels/OCR) ou leitura de memória da battle list do cliente Tibia/Poketibia para identificar alvos ativos e gerenciar estados de combate.
* **Limitações/Dicas:** O autor instrui a manter a opção sempre ativada durante a hunt.
* **Minutagem:** 00:03 - 00:11

---

### 2. Order (Posicionamento Estratégico do Pokémon)
* **O que faz e como configura:** Checkbox "Order" no painel superior. Controla o envio do pokémon para um local específico com o comando *Order* do jogo. É configurado em conjunto com a "Posição Order" presente no popup de cada marcação.
* **Como funciona por baixo:**
  * *Dito:* O bot direciona o pokémon para a posição gravada para travar e fechar o *box* de monstros ao redor dele.
  * *Inferência:* Emite cliques do mouse ou aciona a hotkey/ação de *Order* associada a coordenadas pré-capturadas na tela (X, Y) relativas à janela do jogo.
* **Limitações/Dicas:** É fortemente recomendado deixar ativado para garantir que o "box" de monstros fique fechado e centralizado, otimizando as magias em área.
* **Minutagem:** 00:12 - 00:24

---

### 3. Poke Stop
* **O que faz e como configura:** Checkbox no painel superior. Quando ativado, durante o lure de monstros, o pokémon é mantido parado enquanto o personagem puxa os monstros; após isso, o pokémon se desloca até o ponto.
* **Como funciona por baixo:**
  * *Dito:* Mantém o pokémon parado durante a atração das criaturas (lure) e faz com que ele se desloque apenas posteriormente.
  * *Inferência:* Interrompe comandos de movimento do pet ou usa comandos de parar/voltar para a Pokébola temporariamente.
* **Limitações/Dicas:** O autor afirma que quase não utiliza essa função por não se adequar ao seu estilo de jogo.
* **Minutagem:** 00:25 - 00:42

---

### 4. Revive (Auto-Revive)
* **O que faz e como configura:** Checkbox "Revive" no topo da janela. Ativa o uso automatizado do item Revive no pokémon caso ele seja derrotado durante o trajeto.
* **Como funciona por baixo:**
  * *Dito:* Necessário para o bot utilizar automaticamente o item de revive.
  * *Inferência:* Monitora o status/ícone de vida do pokémon ou a barra lateral do slot do pet; ao detectar desmaio, simula uso do item via hotkey configurada ou clique no inventário/slot.
* **Limitações/Dicas:** Recomendado deixar sempre ativo por segurança do personagem.
* **Minutagem:** 00:43 - 00:50

---

### 5. Loot (Coleta Automatizada de Drop)
* **O que faz e como configura:** Checkbox e campos auxiliares de loot (exibe campos para configurar a tecla de loot ao lado). Permite definir uma tecla (no vídeo é mostrado o teste com a barra de "Espaço" ou botão "Win").
* **Como funciona por baixo:**
  * *Dito:* O personagem anda até o centro do box e aperta repetidamente a tecla configurada para catar itens ao redor (ex.: espaço ou hotkey personalizada).
  * *Inferência:* Simulação de pressão de tecla de teclado (Key strokes) direcionada ao cliente.
* **Limitações/Dicas:** O autor pontua que no servidor *Pokemon Aliiance* o recurso não é tão necessário devido à presença do sistema nativo de *Auto Loot*, mas é útil em outros servidores como o PXG.
* **Minutagem:** 00:51 - 01:21

---

### 6. Tempo Padrão (Delay Global de Espera de Box)
* **O que faz e como configura:** Checkbox acompanhado de caixa de entrada numérica (valor exibido: `3200` ms / 3,2 segundos). Quando habilitado, o bot aplica esse tempo fixo em todas as marcações de combate antes de soltar os combos.
* **Como funciona por baixo:**
  * *Dito:* O bot chega no waypoint, aguarda os 3,2 segundos configurados para que os pokémons colados formem o box completo e só então dispara o auto combo de magias.
  * *Inferência:* Temporizador (*sleep/delay*) executado antes da rotina de ataque do módulo Combo.
* **Limitações/Dicas:** Simplifica e agiliza a configuração da rota, pois evita ter que ajustar manualmente o cooldown de cada waypoint individual.
* **Minutagem:** 01:22 - 01:58, 02:18 - 02:22

---

### 7. Cooldown Individual de Marcação
* **O que faz e como configura:** Campo numérico de "Cooldown" exibido dentro do submenu `Config` de cada marcação (1ª Marcação, 2ª Marcação, etc.).
* **Como funciona por baixo:**
  * *Dito:* Funciona apenas se a opção "Tempo Padrão" estiver desmarcada. O bot aguardará o tempo específico definido individualmente para cada waypoint antes de agir.
  * *Inferência:* Sobrescreve o delay global com uma variável local indexada por ponto de rota.
* **Limitações/Dicas:** Mais trabalhoso de configurar, recomendado apenas para hunts com dinâmicas de tempo muito assimétricas entre salas.
* **Minutagem:** 01:59 - 02:17

---

### 8. Gerenciador de Marcações / Waypoints (Mini-map Waypoints)
* **O que faz e como configura:** Grid com slots expansíveis de "1ª Marcação" a "20ª Marcação", ativáveis através de checkboxes e listas de seleção.
* **Como funciona por baixo:**
  * *Dito:* Permite habilitar de 1 até 20 pontos de rota conforme a extensão da hunt. O autor costuma usar de 10 a 12 pontos.
  * *Inferência:* Cada marcação armazena um par de coordenadas do mapa/minimapa para onde o bot simula o clique de navegação (map click / pathfinding).
* **Limitações/Dicas:** Para hunts curtas, deixar apenas os pontos necessários ativos reduz o consumo e simplifica a rota.
* **Minutagem:** 02:23 - 02:49

---

### 9. Configurações Globais / Avançadas (Popup Config)
* **O que faz e como configura:** Janela modal acionada pelo botão "Config" no cabeçalho. Contém parâmetros de tolerância de pixels (ex.: tolerância 20), tempos de reação e suporte para "Grama Alta".
* **Como funciona por baixo:**
  * *Dito:* O autor recomenda manter os valores padrão de tempo e tolerância. A opção de Grama Alta serve para eventos onde há grama alta bloqueando ou exigindo caminhada diferenciada.
  * *Inferência:* A tolerância refere-se à margem de erro na detecção de cores de pixels na tela para reconhecimento de caminhos ou obstáculos.
* **Limitações/Dicas:** Não alterar os parâmetros padrão a menos que seja estritamente necessário ou instruído para hunts de eventos específicos.
* **Minutagem:** 02:50 - 03:18

---

### 10. Posição Order (Gravação de Coordenadas de Mira)
* **O que faz e como configura:** Botão "Posição Order" dentro do menu de cada marcação. Ao ser clicado, fecha ou minimiza temporariamente o menu, permitindo ao usuário posicionar o cursor no chão do jogo e clicar com o **botão direito** para salvar a posição.
* **Como funciona por baixo:**
  * *Dito:* O usuário clica na opção, mira na tela onde quer fixar o pokémon e aperta o botão direito do mouse para gravar.
  * *Inferência:* O bot captura as coordenadas relativas da tela `(X, Y)` onde o cursor estava no momento do clique e associa à marcação corrente.
* **Minutagem:** 03:19 - 03:43

---

### 11. Flag de Ataque (Ícone de Espada / Checkbox Combate)
* **O que faz e como configura:** Checkbox com ícone de espada ao lado de cada waypoint.
* **Como funciona por baixo:**
  * *Dito:* Se ativado, o bot chega no ponto, espera e executa o combate para derrotar os monstros atraídos (lure). Se desativado, o ponto atua apenas como passagem/caminho (o bot apenas transita pelo ponto sem parar para bater).
  * *Inferência:* Flag booleana que aciona ou ignora o gatilho de execução da rotina de combos ao atingir aquele waypoint específico.
* **Minutagem:** 03:50 - 04:06

---

### 12. Flag de Escada (Navegação de Andares)
* **O que faz e como configura:** Checkbox "Escada" no painel de configuração individual da marcação.
* **Como funciona por baixo:**
  * *Dito:* Indica que o waypoint em questão é uma escada ou rampa de mudança de andar.
  * *Inferência:* Altera o comportamento de clique/movimento para acionar subida/descida de andar e ajustar a referência de coordenadas de andar do mapa.
* **Limitações/Dicas:** Não é utilizado na hunt demonstrada no servidor atual, mas útil para servidores com dungeons multinível convencionais de Tibia.
* **Minutagem:** 04:07 - 04:30

---

## Detalhes de Interface

1. **Janela Principal (PokeTibia Bot):**
   * Interface compacta com botões temáticos em grade:
     * *Direct*, *Order/Revive*, *Target*, *Lure/Cast*, *Cavebot*, *Trainer*, *All Markings*.
2. **Janela do Cavebot:**
   * **Cabeçalho:** Checkboxes globais (*Battle*, *Order*, *Poke Stop*, *Revive*, *Loot*, *Tempo Padrão* com input numérico) e botão de configurações globais (*Config*).
   * **Corpo:** Grade com cartões para cada waypoint ("1ª Marcação", "2ª Marcação", até "20ª Marcação").
   * **Cartão de Marcação Individual:**
     * Checkbox de habilitação.
     * Botão `Config` que abre um submenu suspenso contendo:
       * Botão `Posição Order`
       * Campo de entrada `Cooldown`
       * Checkbox com ícone de espada (combate/lure)
       * Checkbox `Escada`
3. **Estilo Visual:** Interface desktop em tema escuro (Dark Mode), botões com visual flat e caixas modais integradas.

---

## Observações Técnicas e Inferências

* **Mecanismo de Interação:** O bot opera como uma ferramenta externa (pixel/macro-based), baseando-se intensamente em envio de comandos do mouse (gravação de coordenadas absolutas/relativas via botão direito) e de teclado (simulação de tecla espaço/atalhos para loot e combo).
* **Ausência de Injeção de Pacotes:** Não há menção a envio de pacotes brutos na rede; a captura de ações por clique de mouse e posicionamento visual evidencia funcionamento focado em simulação de periféricos (Virtual Key/Mouse events) e captura visual da área de jogo.
* **Estrutura de Waypoints:** O sistema de marcações opera de forma sequencial cíclica, onde cada ponto armazena:
  1. Destino de navegação (coordenadas do minimapa).
  2. Coordenada opcional de comando (*Posição Order*).
  3. Tempo de retenção (*Cooldown* ou *Tempo Padrão*).
  4. Estado de engajamento de combate (Flag de espada).
  5. Tratamento de transição de mapa (Flag de escada).
