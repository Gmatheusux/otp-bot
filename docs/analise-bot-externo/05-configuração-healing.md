# 05 - Configuração Healing

- Vídeo: https://www.youtube.com/watch?v=f81OMjAQd8w
- Modelo: gemini-3.5-flash

---

## Resumo

O vídeo apresenta o tutorial de configuração do módulo de **Healing (Cura)** do software **Simply PokeTibia Bot (V3)**, um bot externo projetado para o jogo *OT Pokémon* (baseado em Tibia). O foco do tutorial é ensinar o usuário a configurar o sistema de cura automatizada dupla, onde o bot detecta a vida do Pokémon de ataque, rotaciona para um Pokémon de suporte (cura), conjura a habilidade de cura e retorna ao Pokémon principal, além de detalhar a alternativa de cura por comida (food).

---

## Funcionalidades

### Módulo de Healing (Cura)

Este módulo é responsável por monitorar a saúde do Pokémon ativo e executar ações de cura automatizadas, seja alternando de Pokémon para usar habilidades de suporte ou consumindo itens de comida.

*   **Como o usuário configura:**
    *   **Healing com pokemon (Checkbox):** Ativa ou desativa a rotina de cura utilizando um Pokémon de suporte.
    *   **Print poke cura (Botão/Campo de Imagem):** O usuário clica neste botão, vai até a tela do jogo e, com o botão direito do mouse, seleciona uma pequena área retangular no centro do ícone do Pokémon curador (no caso do vídeo, um *Togepi*) localizado na barra lateral de Pokémon (*Pokémon Bar*). O bot salva um recorte dessa imagem para fins de reconhecimento visual.
    *   **Print pokemon utilizado (Botão/Campo de Imagem):** Semelhante ao anterior, o usuário clica no botão e seleciona a área central do ícone do Pokémon de ataque/caça principal (no caso, um *Arcanine*) na barra lateral de Pokémon.
    *   **Skill de cura (Campo de Texto):** O usuário digita a tecla de atalho (*hotkey*) correspondente à habilidade de cura do Pokémon de suporte dentro do jogo. No vídeo, a habilidade *Heal Area* do Togepi está configurada na tecla `F4`.
    *   **Comida (Campo de Texto/Tecla):** Define a tecla de atalho para consumir comida (no vídeo, o item *Pizza* está associado à tecla de aspas simples/crase `'`).
    *   **Controle de porcentagem de vida (Slider/Barra de progresso):** Embora não detalhado verbalmente, há barras de ajuste de porcentagem de vida logo abaixo dos prints dos Pokémon, que definem o limiar de HP para ativar a cura.

*   **Como funciona por baixo (Funcionamento Técnico):**
    *   **Reconhecimento de Imagem (Template Matching):** *(Inferência)* O bot realiza capturas de tela (*screengrabs*) contínuas da região da barra de Pokémon do cliente do jogo. Ele compara os recortes salvos ("Print poke cura" e "Print pokemon utilizado") para identificar qual Pokémon está atualmente ativo e monitorar o status de sua barra de vida (provavelmente por leitura de pixels coloridos/RGB na barra de HP ao lado do ícone).
    *   **Simulação de Teclado e Mouse (Virtual Keypress/Click):** *(Inferência)* Ao detectar que a vida do Pokémon principal caiu abaixo do limite configurado, o bot simula um clique do mouse ou comando de atalho para invocar o Pokémon de cura (*Togepi*). Em seguida, envia o comando de teclado correspondente à hotkey da skill de cura (ex: `F4`). Após a execução, ele simula o comando para trazer de volta o Pokémon de ataque (*Arcanine*).
    *   **Simulação de Hotkey de Comida:** *(Dito e Inferido)* Se a opção de curar com Pokémon estiver desativada, o bot envia repetidamente a tecla configurada no campo de comida (ex: `'`) para alimentar o personagem/Pokémon diretamente.

*   **Limitações, dicas ou reclamações mencionadas:**
    *   **Dica de captura:** O narrador destaca que o recorte de imagem ("print") do Pokémon na barra lateral não precisa ser grande; selecionar apenas a região central do ícone do Pokémon é suficiente para o funcionamento correto do algoritmo de busca visual.
    *   **Dica de atalhos:** É mencionado que cada Pokémon de cura pode ter sua habilidade em uma tecla diferente (como `F5`, `F6`), devendo o usuário ajustar o campo "Skill de cura" de acordo com o Pokémon ativo.
    *   **Omissão de uso:** O narrador afirma que o botão de comida pode ser deixado em branco pela maioria dos usuários, pois o método de cura por Pokémon é o mais utilizado.

*   **Minutagem:** 00:00 a 01:32.

---

## Detalhes de Interface

A interface do **Simply PokeTibia Bot** é compacta, flutuante e cinza-escura, projetada para sobrepor-se ao cliente do jogo sem ocupar muito espaço.

*   **Janela Principal ("Simply | PokeTibia Bot"):**
    *   Apresenta uma grade de botões de acesso rápido para os diferentes módulos do sistema:
        *   `Healer` (módulo configurado no vídeo)
        *   `Combo`
        *   `Buffs`
        *   `Target`
        *   `CaveBot`
        *   `Loot`
        *   `Extras`
        *   `All Hotkeys`
*   **Janela de Healing:**
    *   Uma subjanela que se abre ao clicar em `Healer`.
    *   Contém duas caixas de visualização de imagem (preparadas para mostrar o preview dos ícones capturados do Togepi e do Arcanine).
    *   Campos de entrada de texto cinza para digitação de teclas de atalho (`F4`, `'`).
    *   Checkboxes padrão do Windows para ativação de recursos.
    *   Sliders horizontais para ajuste fino de sensibilidade/porcentagem de HP.

---

## Observações Técnicas e Inferências

1.  **Dependência de Resolução e Layout:** Como o bot utiliza coordenadas de tela e capturas de imagem específicas da barra de Pokémon, qualquer alteração na resolução do jogo, redimensionamento da janela do cliente ou mudança no posicionamento dos elementos de interface (UI) do *OT Pokémon* invalidará os "prints" tirados, exigindo que o usuário refaça as configurações de imagem.
2.  **Injeção de Código vs. Simulação Externa:** O comportamento de clicar na tela para registrar a imagem e a necessidade de mapear teclas físicas sugerem fortemente que o **Simply** é um bot de pixel/imagem puramente externo (que simula interações humanas de teclado e mouse via APIs do Windows, como `SendInput` ou `keybd_event`), em vez de um bot que injeta DLLs ou lê diretamente a memória RAM do processo do jogo (*Memory-hard bot*). Isso o torna teoricamente menos detectável por sistemas antitrapaça básicos que buscam por manipulação de memória, mas o torna vulnerável a bloqueios de simulação de input de teclado/mouse.
