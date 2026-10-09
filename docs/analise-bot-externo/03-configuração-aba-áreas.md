# 03 - Configuração Aba Áreas

- Vídeo: https://www.youtube.com/watch?v=k3lvhw4VARI
- Modelo: gemini-3.8-flash

---

## Resumo
O vídeo apresenta a configuração inicial do módulo de calibração de visão de tela ("Aba Áreas") do software PokeTibia Bot (interface Simplify). O narrador demonstra, de maneira sequencial, o mapeamento manual de seis regiões essenciais da interface gráfica do cliente de jogo OT Pokémon: Minimapa, Poké-bar, Battle, Barra de vida, Área de Catch e Detecção de Mensagens. Essa etapa é o pré-requisito fundamental para que as rotinas de automação (cavebot, cura, ataque e captura) possam localizar elementos visuais na tela via captura de coordenadas e reconhecimento visual.

---

## Funcionalidades

### 1. Minimapa
1. **Nome:** Minimapa (selecionado dentro da janela "Áreas", sob o agrupador "Filtros de tela").
2. **O que faz e como configura:** Delimita a região do minimapa do jogo. O usuário clica no item "Minimapa" na lista, surge uma janela modal de instrução ("*Clique e segure o botão DIREITO do mouse para capturar a área do Minimapa*"). Ao clicar em "OK", o cursor ganha a função de seleção: o usuário clica e arrasta com o botão direito sobre o minimapa no canto superior esquerdo da tela do jogo, formando um retângulo verde de seleção que grava as coordenadas ao soltar o clique.
3. **Funcionamento subjacente:** 
   - *Dito no vídeo:* Que o usuário precisa capturar e soltar sobre o minimapa.
   - *Inferência:* O bot armazena as coordenadas cartesianas $(X_1, Y_1, X_2, Y_2)$ da área delimitada para aplicar reconhecimento visual/pixel search ou matching de pixels de rota/waypoints diretamente no minimapa sem injetar código na memória do jogo.
4. **Limitações e dicas:** Não foram relatados bugs específicos; o usuário deve abranger com precisão os limites do mapa.
5. **Minutagem:** 00:20 – 00:38.

---

### 2. Poké-bar (ou Pokebar)
1. **Nome:** Poké-bar.
2. **O que faz e como configura:** Registra as coordenadas da barra lateral onde ficam alocadas as Pokébolas dos Pokémon do jogador. O usuário seleciona a opção na lista, confirma a caixa de diálogo modal e seleciona a área arrastando com o botão direito do mouse ao redor da coluna vertical de Pokébolas no canto direito do cliente.
3. **Funcionamento subjacente:**
   - *Dito no vídeo:* O narrador apenas orienta a colocar a barra inteira dentro do retângulo verde.
   - *Inferência:* Reconhecimento de imagem/cor (pixel search/template matching) para monitorar o status do Pokémon (se está fora da pokébola, desmaiado, recarregando ou se a pokébola está ativa/inativa), viabilizando trocas rápidas e automação de revive/reviver.
4. **Limitações e dicas:** É necessário garantir que todas as posições de pokébolas (geralmente até 6) fiquem integralmente contidas na seleção.
5. **Minutagem:** 00:38 – 00:47.

---

### 3. Battle
1. **Nome:** Battle.
2. **O que faz e como configura:** Delimita a janela de "Battle" (lista de alvos/monstros próximos). Clica-se na opção "Battle", aceita-se o aviso modal e arrasta-se a seleção retangular sobre toda a extensão da lista de monstros/jogadores na lateral esquerda da tela.
3. **Funcionamento subjacente:**
   - *Dito no vídeo:* O narrador enfatiza explicitamente que a janela do Battle precisa estar aberta e expandida em tamanho grande para que o bot funcione corretamente.
   - *Inferência:* O bot usa OCR ou busca por padrões gráficos/cores de barras de vida e nomes de monstros dentro da região capturada para executar o clique de ataque ou envio de comando de target. Se a lista for muito pequena, o número de alvos visíveis é truncado, prejudicando a rotina de targeting.
4. **Limitações e dicas:** Dica destacada pelo autor: a janela do Battle do cliente deve estar esticada/grande para que o bot tenha um bom desempenho.
5. **Minutagem:** 00:48 – 01:00.

---

### 4. Barra de vida
1. **Nome:** Barra de vida.
2. **O que faz e como configura:** Mapeia a barra de HP/energia tanto do personagem quanto do Pokémon ativo. O usuário seleciona o item, confirma o alerta e arrasta a seleção do início das barras até a extremidade direita da interface.
3. **Funcionamento subjacente:**
   - *Dito no vídeo:* Mostra todas as informações de vida do personagem e do Pokémon. O autor instrui a arrastar o mouse até o limite direito da tela.
   - *Inferência:* Leitura contínua de porcentagem de pixels vermelhos/verdes (pixel reading horizontal) para calcular a fração restante de vida e disparar hotkeys/ações de cura/poções automaticamente quando a vida cai abaixo de determinado limiar.
4. **Limitações e dicas:** O narrador dá a dica prática de arrastar o mouse até encostar no limite direito da janela para não cortar os pixels finais da barra.
5. **Minutagem:** 01:01 – 01:19.

---

### 5. Área de Catch
1. **Nome:** Área de Catch.
2. **O que faz e como configura:** Seleciona a tela principal de jogo (viewport do mapa onde o personagem e os monstros andam). O usuário confirma o item na lista e traça um retângulo verde abrangendo praticamente toda a janela central de renderização do jogo.
3. **Funcionamento subjacente:**
   - *Dito no vídeo:* Abrange a área onde acontecem as animações do jogo.
   - *Inferência:* Identificação de monstros mortos (corpos/loot) e animações visuais para disparo de ações como jogar pokébolas (automatch de corpses caídos no chão após o combate) por clique simulado ou atalho.
4. **Limitações e dicas:** Deve cobrir a viewport visível do mapa sem sobrepor barras de interface fixas.
5. **Minutagem:** 01:20 – 01:31.

---

### 6. Área de Detecção de Mensagens (Área Detec/Detecção Mensag)
1. **Nome:** Área Detec/Detecção Mensag.
2. **O que faz e como configura:** Mapeia a janela de console/chat de texto (aba "Default" e logs de sistema na base da interface). O usuário seleciona o item e arrasta a área retangular sobre a caixa de texto inferior do jogo.
3. **Funcionamento subjacente:**
   - *Dito no vídeo:* Região onde chegam as mensagens de texto para o personagem.
   - *Inferência:* Utilização de OCR (Optical Character Recognition) ou hash de texto/leitura de fontes para identificar avisos do servidor (ex.: captura bem-sucedida/falha, ganho de experiência, mensagens de GM ou avisos de status).
4. **Limitações e dicas:** É fundamental cobrir toda a área útil de rolagem de texto para que linhas novas não sejam ignoradas.
5. **Minutagem:** 01:32 – 01:42.

---

## Detalhes de interface

- **Janela Principal ("Simplify - PokeTibia Bot"):**
  - Barra de título estilizada com botão de minimizar/fechar.
  - Grade de botões modulares organizados em duas linhas:
    - Linha superior: *Áreas*, *Combo*, *Healing*, *Target*.
    - Linha inferior: *Loot/Cave*, *Catch*, *Server*, *All Hotkeys*.
- **Janela Secundária ("Áreas"):**
  - Caixa de grupo/título: *Filtros de tela*.
  - Componente de lista (ListBox) contendo os 6 módulos de seleção de área.
- **Mecanismo de Captura na Tela:**
  - Janelas modais informativas com ícone de exclamação azul instruindo o usuário a usar o botão direito do mouse.
  - Sobreposição visual direta sobre o jogo: um retângulo semi-transparente verde brilhante com borda demarcada em verde vivo acompanha o arraste do cursor, permitindo precisão visual no recorte.

---

## Observações técnicas e inferências

- **Arquitetura Externa Baseada em Visão Computacional (Screen Scraping / Pixel Bot):**
  - Toda a configuração inicial apresentada no vídeo comprova que o bot opera externamente ao cliente de jogo, sem necessidade de injeção de DLL ou leitura de ponteiros em memória dinâmica (RAM).
  - Ele depende estritamente das posições e dimensões dos elementos na tela para monitorar o jogo através de captura de tela contínua (GDI, DirectX hooks ou APIs de captura de desktop).
- **Sensibilidade à Resolução e Layout:**
  - Por depender de coordenadas físicas na tela, qualquer movimentação de janelas internas do cliente, redimensionamento da janela do jogo ou alteração na escala de DPI do sistema operacional invalida o mapeamento, exigindo reconfiguração na aba "Áreas".
