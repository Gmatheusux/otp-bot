# 10 - Funções do Sinapty2

- Vídeo: https://www.youtube.com/watch?v=GiITAqjwccI
- Modelo: gemini-3.8-flash

---

Com base no trecho em vídeo e no áudio apresentado, segue o levantamento técnico detalhado das funcionalidades expostas do módulo **SinaptyBot** (especificamente a interface "Painel de Controle 02").

---

## Resumo
O vídeo apresenta a segunda parte das configurações do **SinaptyBot** para um cliente de *PokéTibia* (Open-Tibia derivado de Pokémon). O foco do trecho é a tela denominada **Painel de Controle 02**, responsável por automações de suporte e contingência, incluindo uso automático de poções de cura, ressuscitação imediata de Pokémon, captura seletiva (focada em Shinies e raros), alarmes de desconexão e de mensagens, além de um sistema de ativação periódica de consumíveis em slots configuráveis.

---

## Funcionalidades

### 1. Instant Revive
* **1. Nome da funcionalidade:** `Instant Revive` (Checkbox na coluna *Healing*).
* **2. O que faz e como configura:** Revive o Pokémon instantaneamente assim que ele morre durante a caçada (*hunt*). A configuração exibida no trecho consiste apenas na ativação/desativação via caixa de seleção (*checkbox*).
* **3. Funcionamento interno:**
  * *Dito no vídeo:* O narrador apenas menciona que, se o Pokémon morrer na hunt, ele "vai reviver instantaneamente".
  * *Inferência técnica:* Não há menção explícita de injeção de DLL ou memória; tipicamente, em bots externos para clientes baseados em Tibia (OTClient/Old Tibia), esse tipo de ação é disparado via monitoramento de imagem/pixel na barra de status do Pokémon ou leitura de memória da barra de vida (quando atinge 0), seguido do envio automatizado de hotkey pré-definida ou clique com botão direito sobre o *Revive* e uso no Pokémon.
* **4. Limitações, bugs ou dicas:** Explicado apenas de forma superficial pelo narrador no trecho, sem detalhamento de cooldowns ou comportamento caso o jogador fique sem *revives* na bolsa.
* **5. Minutagem:** 00:07 a 00:13.

---

### 2. Potion
* **1. Nome da funcionalidade:** `Potion` (Checkbox na coluna *Healing*).
* **2. O que faz e como configura:** Realiza a cura automática do Pokémon. O narrador afirma que, ao marcar a opção, se a vida do Pokémon cair para 50%, o bot passa a aplicar poções automaticamente conforme configurado na barra inferior do cliente.
* **3. Funcionamento interno:**
  * *Dito no vídeo:* "Se ele tiver com 50% de vida ele começa a utilizar potion, de acordo com o que você configurou aqui embaixo".
  * *Inferência técnica:* Monitora a barra de vida do Pokémon (provavelmente leitura percentual por amostragem de cor/pixel na barra de vida ou leitura da estrutura de memória do *battle/pokemon bar*). O uso é acionado simulando tecla de atalho configurada para o item na barra de ação (*action bar*).
* **4. Limitações, bugs ou dicas:** O narrador indica que o gatilho fixo mencionado no momento é a faixa de 50% de HP.
* **5. Minutagem:** 00:14 a 00:21.

---

### 3. Catch (Captura de Raros/Shiny)
* **1. Nome da funcionalidade:** `Catch` (Checkbox na coluna central).
* **2. O que faz e como configura:** Automação de captura voltada especificamente para Pokémon especiais (*Shiny*, *Ditto* e outros raros). A ativação é feita marcando o checkbox. O narrador deixa claro que essa função não é destinada a monstros comuns.
* **3. Funcionamento interno:**
  * *Dito no vídeo:* Exclusivo para capturar Shinies e Dittos; os monstros comuns devem ser configurados no bot principal/cavebot.
  * *Inferência técnica:* Reconhecimento de nome do monstro derrotado via leitura de texto no log/servidor (chat), análise de texto flutuante ou identificação do sprite/cor específica do cadáver no chão antes de disparar a sequência de uso de pokébolas.
* **4. Limitações, bugs ou dicas:** O usuário é alertado de que para monstro comum deve-se usar a configuração padrão do Cavebot tradicional, reservando esta opção para criaturas raras.
* **5. Minutagem:** 00:21 a 00:31 e retorno em 01:04.

---

### 4. Disconnect Alarm
* **1. Nome da funcionalidade:** `Disconnect Alarm` (Checkbox na coluna central).
* **2. O que faz e como configura:** Alarme sonoro/notificação caso o personagem seja desconectado do servidor ou morra. Ativado via checkbox.
* **3. Funcionamento interno:**
  * *Dito no vídeo:* Dispara avisos sonoros/alertas quando o personagem sai do jogo ou acaba morrendo.
  * *Inferência técnica:* Monitoramento de estado do cliente (perda de conexão com o socket, tela de login reaparecendo ou perda de foco da janela ativa/tela de morte).
* **4. Limitações, bugs ou dicas:** Nenhum bug citado; serve como recurso anti-inatividade/alerta para evitar perdas enquanto estiver AFK.
* **5. Minutagem:** 00:32 a 00:41.

---

### 5. Respostas e Message Alert
* **1. Nome da funcionalidade:** `Respostas` e `Message Alert` (Checkboxes na coluna de mensagens/segurança).
* **2. O que faz e como configura:** 
  * `Message Alert`: Detecta se algum jogador ou moderador/GM enviou mensagem no chat.
  * `Respostas`: Automatiza o envio de resposta caso alguém fale com o personagem.
* **3. Funcionamento interno:**
  * *Dito no vídeo:* Detecta se alguém mandou mensagem e executa a resposta configurada.
  * *Inferência técnica:* Leitura de mensagens que chegam no canal padrão (*Default*) ou canais privados (*Private Chat/Whisper*), possivelmente via scraping de texto do componente de chat do OTClient ou hooks de socket/memória. A resposta emula a digitação no canal ativo.
* **4. Limitações, bugs ou dicas:** O vídeo não detalha neste trecho se as respostas são predefinidas estaticamente em listas ou randômicas.
* **5. Minutagem:** 00:42 a 00:50.

---

### 6. Automação de Slots de Consumíveis (Buffs / Charms / XP)
* **1. Nome da funcionalidade:** `Slots (Slot 1, Slot 2, Slot 3)` (Campos numéricos).
* **2. O que faz e como configura:** Executa o uso contínuo de itens consumíveis (exemplificados como boost de XP, Shiny Charm e Charm de Evento). 
  * Campos visíveis:
    * `Slot 1` com valor padrão visível `[50]`
    * `Slot 2` com valor padrão visível `[50]`
    * `Slot 3` com valor padrão visível `[50]`
* **3. Funcionamento interno:**
  * *Dito no vídeo:* Consome itens colocados na barra inferior (Action Bar) do jogo conforme a numeração e tempo programados.
  * *Inferência técnica:* Os valores "50" representam o intervalo de repetição ou duração (provavelmente minutos ou segundos) para disparar novamente o atalho correspondente ao slot da *Action Bar* (como as *Action Buttons* visíveis no canto inferior direito do OTClient).
* **4. Limitações, bugs ou dicas:** Depende de o usuário posicionar os consumíveis exatamente nos slots vinculados na barra de ações.
* **5. Minutagem:** 00:51 a 01:03.

---

## Detalhes de interface
* **Janela principal do utilitário:** Denominada `SinaptyBot`.
* **Subjanelas/Abas:**
  * No topo esquerdo há botões/abas de navegação: `Controle 01`, `Target/Cave 01`, `Extra 01`.
  * A tela aberta em exibição é intitulada internamente como **Painel de Controle 02**.
* **Layout dos controles:**
  * **Bloco Esquerdo (Healing):**
    * Checkbox: `Instant Revive`
    * Checkbox: `Potion`
  * **Bloco Central:**
    * Checkbox: `Catch`
    * Checkbox: `Disconnect Alarm`
  * **Bloco Intermediário Direito:**
    * Checkbox: `Respostas`
    * Checkbox: `Message Alert`
  * **Bloco Direito (Slots):**
    * Três linhas de entrada de texto/número:
      * Rótulo `Slot 1` seguido de caixa de texto `50`.
      * Rótulo `Slot 2` seguido de caixa de texto `50`.
      * Rótulo `Slot 3` seguido de caixa de texto `50`.
* **Ambiente de jogo integrado:** O cliente é baseado no **OTClient** modificado para *PokeTibia*, exibindo módulos nativos como *Hunt Analyzer*, lista de Pokémons ativos na direita, *Battle List*, mini-mapa customizado e *Action Bar* horizontal inferior.

---

## Observações técnicas e inferências
1. **Natureza da aplicação (Externo vs. Interno):** A janela do *SinaptyBot* roda como um processo separado sobreposto (overlay/janela GUI padrão Win32/Python/C#), com visual estilo formulário clássico, sem estar incorporada como módulo Lua nativo dentro da interface do OTClient.
2. **Método de atuação:** Pela forma como o narrador orienta a colocar poções e consumíveis na *Action Bar* do próprio jogo, o bot depende de simulação de entradas de teclado (Virtual Key Codes / SendInput) direcionadas aos atalhos da interface, agindo de maneira complementar às funções do próprio cliente.
3. **Divisão de papéis:** Há uma separação nítida entre o motor básico de caça (mencionado como algo que fica em outra seção/bot tradicional) e este painel, que funciona como um gestor de exceções (alertas, detecção de eventos raros como Shinies e manutenção de buffs de longa duração).
