# 09 - Configurações Aba Catch (Cavebot)

- Vídeo: https://www.youtube.com/watch?v=EzDTMEyMfDw
- Modelo: gemini-3.8-flash

---

## Resumo
O vídeo apresenta a configuração do módulo **Catch** do utilitário externo "PokeTibia Bot" (voltado ao jogo PokeTibia / OT Pokémon). O recurso é projetado para automatizar o arremesso de Pokébolas em Pokémons normais caídos no chão através de correspondência de padrões visuais (Image Matching/Template Matching). O autor demonstra o fluxo de recortar o sprite do monstro, configurar tempos de espera (*delay*) e calibrar o limiar de sensibilidade visual (*tolerância*).

---

## Funcionalidades

### Módulo Catch (Captura de Pokémons Normais)
1. **Nome da funcionalidade/aba/módulo:**
   * **Catch** (janela/sub-aba acessada através do menu principal do bot).

2. **O que faz e como o usuário configura:**
   * **Finalidade:** Detectar o corpo do Pokémon derrotado na tela e realizar a ação automatizada de arremessar a Pokébola.
   * **Botão "Print":** Ao ser clicado, ativa o modo de recorte de imagem. O usuário deve selecionar e recortar uma porção representativa do sprite do Pokémon (de preferência o centro ou uma parte visualmente estável/visível).
   * **Área de Pré-visualização (Preview):** Exibe a porção gráfica capturada que servirá de modelo/âncora para a busca na tela.
   * **Campo de Delay (ms):** Define o tempo de intervalo em milissegundos entre o lançamento de uma Pokébola e outra (visível configurado em torno de 1500–2000 ms), evitando comandos repetitivos em velocidade não permitida pelo jogo.
   * **Checkbox / Chave de Ativação:** Caixa de seleção para habilitar ou desabilitar o módulo de captura automática.
   * **Controle de Tolerância:** Campo numérico (padrão em 50) que define o rigor de correspondência visual:
     * *Aumentar tolerância (>50):* Torna a detecção mais permissiva caso o bot não esteja reconhecendo o Pokémon no chão.
     * *Diminuir tolerância (ex: 20–30):* Torna a comparação mais rigorosa para prevenir falsos positivos (como clicar em partes do chão ou outros objetos que lembrem as cores do sprite).

3. **Como funciona por baixo:**
   * **Processamento de Imagem / Template Matching (*Inferência baseada no comportamento e na fala*):** O bot utiliza visão computacional baseada em comparação de templates (busca de subimagem em buffer de tela/pixel matching). O parâmetro de "tolerância" corresponde matematicamente ao limiar de confiança/distância de cor na matriz de pixels.
   * **Simulação de Entrada (*Dito e Inferido*):** O vídeo cita que, em caso de erro, o bot "joga o mouse em coisa nada a ver". Isso confirma que a ação de captura é realizada via emulação de cursor do mouse (movimentação e cliques de mouse na coordenada onde a imagem coincidiu), e não por injeção direta de pacotes de rede.
   * **Captura de Tela da Ferramenta (*Dito e Visual*):** Ao apertar "Print", o bot intercepta as coordenadas de tela via instrução *"Clique e segure o BOTÃO DIREITO do mouse para capturar a imagem"*, gerando um arquivo de imagem local associado à regra de captura.

4. **Limitações, bugs e dicas mencionadas:**
   * **Falsos Positivos:** Se a tolerância estiver alta demais, o cursor pode mirar em elementos visuais incorretos do cenário. A recomendação explícita do narrador é reduzir a tolerância para 30 ou 20 caso isso ocorra.
   * **Falsos Negativos:** Se o bot não estiver identificando o Pokémon para jogar as Pokébolas, deve-se elevar a tolerância.
   * **Seleção do Trecho de Imagem:** Recomenda-se recortar o centro ou partes da criatura que fiquem sempre visíveis e não sofram oclusão fácil.
   * **Valor ideal padrão:** O narrador destaca que o valor de tolerância em **50** costuma funcionar na maioria dos casos.
   * **Uso pessoal:** O autor cita que quase não usa essa função para Pokémons comuns, reservando o tempo/recurso apenas para criaturas do tipo *Shiny*.

5. **Minutagem:**
   * **00:00 – 00:10:** Introdução à aba Catch e distinção entre captura comum e shinies.
   * **00:11 – 00:20:** Utilização da ferramenta de recorte (Print) e seleção do sprite.
   * **00:21 – 00:30:** Explicação do delay entre tentativas de arremesso.
   * **00:30 – 00:39:** Ativação/desativação da funcionalidade.
   * **00:40 – 01:06:** Explicação e calibração fina do parâmetro de tolerância (sensibilidade e falsos positivos).

---

## Detalhes de Interface

* **Menu Superior / Painel Flutuante Principal:**
  * Apresenta uma janela compacta com tema escuro (Dark Mode) e bordas finas contendo os botões principais de navegação:
    * `Drive`
    * `Combat`
    * `Healing`
    * `Target`
    * `Loot/Door`
    * `Catch`
    * `Server`
    * `All Markings`
* **Janela Modal "Catch":**
  * Janela filha de tamanho fixo contendo:
    * Botão `Print` estilizado no canto superior esquerdo.
    * Quadro de visualização (ImageViewer) com fundo preto ao lado do botão, exibindo o fragmento capturado.
    * Caixa de texto para preenchimento de Delay.
    * Caixa de seleção (Checkbox) para ligar/desligar a execução do Catch.
    * Caixa de número/slider de Tolerância.
* **Overlay de Recorte:**
  * Ao acionar o botão "Print", surge na parte superior central do cliente do jogo uma legenda branca explicativa: *"Clique e segure o BOTÃO DIREITO do mouse para capturar a imagem."* com efeito de cursor em cruz/alvo para seleção da área retangular.

---

## Observações Técnicas e Inferências

* **Arquitetura Baseada em Pixels (Pixel-Bot / Image Search):**
  * Diferente de bots tradicionais de Tibia que leem estruturas de memória direta (Memory/Packet injection via DLL injection), esta ferramenta opera primariamente em nível de superfície gráfica (Screen Scraping / Pixel Matching), reduzindo a probabilidade de detecção por checagens de integridade de memória do cliente.
* **Armazenamento de Imagens:**
  * O narrador indica que *"a imagem já vai ficar salva"*, o que infere a existência de uma pasta local do bot onde arquivos de imagem (como PNG ou BMP) são persistidos e vinculados ao perfil ativo de configuração.
* **Coordenação com Hotkeys:**
  * Como o bot atira Pokébolas através da emulação do mouse, ele depende da sincronização entre o clique de mira na coordenada detectada e a hotkey da Pokébola configurada no cliente do jogo, razão pela qual o ajuste de *delay* precisa mimetizar o tempo de *cooldown* global de ações.
