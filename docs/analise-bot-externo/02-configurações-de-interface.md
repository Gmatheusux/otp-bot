# 02 - Configurações de interface

- Vídeo: https://www.youtube.com/watch?v=Vhu78S3iwB0
- Modelo: gemini-3.7-flash

---

## Resumo
Este vídeo demonstra a etapa preliminar de configuração da interface gráfica do cliente de jogo (baseado em OTClient / Poketibia) para compatibilização com o bot externo "Pokemon Aliiance V3". O narrador ajusta parâmetros essenciais no menu de opções (ativação de Classic View, definição de 1 painel lateral esquerdo e 1 direito, desativação de shaders em corpos de shinies) e reposiciona janelas de jogo (Minimap e Battle no painel esquerdo, Pokebar e Health bar no direito). O vídeo encerra preparando o espectador para a etapa de configuração direta no software do bot.

---

## Funcionalidades

### 1. Configurações de Interface (Menu Options > Interface)
* **Nome da funcionalidade/aba/módulo:** Menu de Opções — Aba `Interface`.
* **O que ela faz e como o usuário configura:**
  * **Classic view:** Chave comutadora (toggle switch). É ativada (ligada / azul). Padroniza o viewport de jogo para o modo clássico sem distorções ou layouts dinâmicos que possam deslocar as coordenadas da tela.
  * **Left panels:** Slider numérico com valor ajustado para `1` (adiciona uma coluna lateral fixa à esquerda da viewport do jogo).
  * **Right panels:** Slider numérico mantido em `1` (mantém uma coluna lateral fixa à direita).
  * *Demais opções visíveis na tela (valores padrão/não alterados no vídeo):*
    * `Display creature names` (ativo)
    * `Display creature health bars` (ativo)
    * `Display creature health bars above texts` (desativo)
    * `Show player health bar` (ativo)
    * `Health Color`: Dropdown em `Default`
    * `Top left panel`: `0`
    * `Top right panel`: `0`
    * `Floor fading`: Slider em `750 ms`
* **Como parece funcionar por baixo:**
  * *Dito no vídeo:* O narrador apenas orienta a ativar o "Classic view", setar "Left panels" em 1 e "Right panels" em 1.
  * *Inferência técnica:* Bots externos (que operam via captura de tela/pixel ou leitura de offsets de memória fixos) dependem de dimensões estritas e imutáveis da área de renderização do mapa (`gameMapPanel`). A fixação de 1 painel lateral esquerdo e 1 direito com a "Classic View" garante que a grade de tiles de visualização do personagem fique em tamanho fixo e centrado, evitando que variações na resolução do monitor alterem as distâncias em pixels entre o personagem e os monstros/tiles.
* **Limitações, bugs ou dicas mencionadas:** Nenhuma menção a bugs; trata-se de um pré-requisito de alinhamento visual.
* **Minutagem:** 00:02 a 00:12.

---

### 2. Configurações de Jogo (Menu Options > Game)
* **Nome da funcionalidade/aba/módulo:** Menu de Opções — Aba `Game`.
* **O que ela faz e como o usuário configura:**
  * **Show a Special Shader on Shinies Corpses:** Chave comutadora (toggle switch). É explicitamente desativada (desligada / cinza) pelo usuário.
  * *Demais opções visíveis na aba:*
    * `Classic control` (ativo)
    * `Display text messages` (ativo)
    * `Display status messages` (ativo)
    * `Enable Walk with Right Click` (ativo)
    * `Shift mouse button action`: Dropdown em `Walk`
    * `Shift-right-click a backpack opens it in a new window` (ativo)
    * `Turn Pokémon when you turn Character` (ativo)
    * `Allow Tab to target NPCs` (ativo)
    * `Show guild name above players` (ativo)
    * `Show guild icon above players` (ativo)
    * `Show a Special Icon on Shinies` (ativo)
    * `Show Pokémon Spells on Floor` (ativo)
* **Como parece funcionar por baixo:**
  * *Dito no vídeo:* O narrador orienta a desativar a opção `Show a Special Shader on Shinies Corpses`.
  * *Inferência técnica:* Shaders visuais alteram ciclicamente as cores e o brilho dos pixels dos corpos caídos (criando efeitos pulsantes ou de brilho). Bots baseados em visão computacional, verificação de hashes de imagem ou leitura de pixel RGB para auto-loot / detecção de corpses não conseguem identificar o sprite se ele estiver sofrendo mutação de cor por shaders. Desativar o shader mantém a paleta de cores estática e padronizada.
* **Limitações, bugs ou dicas mencionadas:** Nenhuma reclamação expressa, apenas a diretriz de manter desmarcado.
* **Minutagem:** 00:13 a 00:20.

---

### 3. Organização e Encaixe das Janelas da Interface (Docking)
* **Nome da funcionalidade/aba/módulo:** Gerenciamento de Janelas e Painéis de Interface (HUD / Docking Panels).
* **O que ela faz e como o usuário configura:**
  * O narrador fecha o menu de opções e reorganiza os elementos na tela:
    * **Minimap:** Movido do lado direito para o topo do painel recém-criado à esquerda.
    * **Battle:** Aberto através do botão na barra superior e fixado no painel esquerdo, logo abaixo da janela do Minimap.
    * **Pokebar:** Posicionada/mantida no painel direito (área intermediária/inferior).
    * **Player Health Bar (Barra de Vida/Status):** Posicionada no topo do painel direito.
* **Como parece funcionar por baixo:**
  * *Dito no vídeo:* O narrador afirma que o usuário pode organizar conforme preferir e que "não necessariamente precisa ser onde eu tô colocando a minha aqui", deixando entender que há flexibilidade ou que as coordenadas de leitura podem ser calibradas posteriormente.
  * *Inferência técnica:* Apesar da fala do narrador indicando que o usuário pode organizar livremente, bots para Tibia/OTClient frequentemente utilizam OCR ou varredura de pixels dentro da janela *Battle* (para atacar alvos prioritários) e no *Minimap* (para detecção de posição, waypoints de mapa ou leitura de marcas). Colocá-los em painéis específicos e desobstruídos reduz a chance de sobreposição de janelas e garante que as regiões de interesse (ROIs) estejam sempre visíveis para o loop de captura de tela do bot.
* **Limitações, bugs ou dicas mencionadas:** O narrador dá a dica de que a posição exata das janelas pode variar segundo o gosto do usuário.
* **Minutagem:** 00:21 a 00:49.

---

## Detalhes de interface

* **Estrutura geral exibida:** 
  * Cliente baseado na arquitetura típica do OTClient (fork open-source amplamente utilizado em servidores de Tibia e Poketibia).
  * Painel superior com ícones de atalho (inventário, battle, canais, opções, som, etc.) e barra de atalhos rápidos/cooldowns na borda inferior do mapa.
  * Três colunas principais resultantes:
    1. **Coluna lateral esquerda (Painel 1):** Minimap (topo) e Battle list (abaixo).
    2. **Área central (Game Window):** Visualização 2D isométrica clássica do mapa com o personagem centralizado, mensagens de jogo e barra de atalhos inferior.
    3. **Coluna lateral direita (Painel 1):** Barra de vida do personagem (topo), Hunt Analyser/Pokebar (centro/abaixo), e espaço para mochilas/containers abertos.
* **Módulos do Bot / Scripts / Waypoints:**
  * Neste vídeo específico, a interface gráfica do próprio bot **não** é aberta na tela; o vídeo termina aos 00:50 com o narrador dizendo que irão para a configuração no bot propriamente dita. Portanto, menus de script, waypoints e formatos de arquivo (`.json`, `.ini`, etc.) pertencem aos vídeos subsequentes da playlist.

---

## Observações técnicas e inferências

1. **Método de Interação do Bot:**
   * A necessidade de desativar efeitos visuais (shaders) e normalizar o layout (Classic View) é uma forte assinatura de automação que depende de **Image Recognition / Pixel Scanning** ou **Screen Capture com OCR**, e não puramente de injeção de DLL ou hooks em memória (que independeriam de shaders gráficos para ler a tabela de entidades ou inventário).
2. **Separação de Painéis:**
   * A separação do Minimap e da Battle list no painel esquerdo enquanto barras de vida e inventário ficam no direito permite criar caixas delimitadoras (bounding boxes) distintas e não sobrepostas, otimizando o consumo de CPU da captura de tela do bot.
