# <span style="color: #CC5500;">**Contexto Ativo: Bot Poketibia (Diretiva Zero-Claude)**</span>

## <span style="color: #CC5500;">**Escopo Global e Progresso**</span>
- <span style="color: #CC5500;">**Fase 1 (Concluída):**</span> Logger de tela e motor base de Visão (`vision.py`) para leitura via OpenCV/PyTesseract homologados.
- <span style="color: #CC5500;">**Fase 2 (Concluída):**</span> Módulo de Visão de Alta Performance (`modules/vision_engine.py`) focado em YOLOv8 + TensorRT.
- <span style="color: #CC5500;">**Fase 3 (Concluída - Evoluída):**</span> Cérebro Lógico e Orquestrador de Ações (`core/action_orchestrator.py`) com timers não-bloqueantes.
- <span style="color: #CC5500;">**Fase 4 (Concluída):**</span> Atuador Cinemático (`core/mouse_controller.py`).
- <span style="color: #CC5500;">**Fase 5 (Concluída):**</span> Integração Core (`main.py`) com injeção de dependências e concorrência via `asyncio`.
- <span style="color: #CC5500;">**Fase 5.1 (Concluída):**</span> Perfil de Pokémon Ativo dinâmico para luring (inserção de `pokemon_profile` com `auto_combo_key`, `revive_key` e `defensive_buff_key` no `config_manager.py`).
- <span style="color: #CC5500;">**Fase 6 (Concluída):**</span> Hotkeys dinâmicas (`keyboard` + `asyncio.Event`) e Configuração Global via `config.json`.
- <span style="color: #CC5500;">**Fase 7 (Em Andamento):**</span> Backend da API (FastAPI + WebSocket) construído para comunicação em tempo real com o Dashboard.

## <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas**</span>
- <span style="color: #CC5500;">**Pivot Tático (Override Claude):**</span> Devido a interrupções causadas pelos guardrails do Claude CLI nas fases anteriores, a delegação autônoma foi revogada para o backend. O Gravy assumiu o controle braçal da engenharia via `write_to_file`.
- <span style="color: #CC5500;">**A Morte da FSM:**</span> A arquitetura rígida de Máquina de Estados Finita solicitada foi rejeitada em favor de um modelo superior: um <span style="color: #CC5500;">**Orquestrador Híbrido**</span> acoplado ao Utility AI.
- <span style="color: #CC5500;">**Timers Assíncronos:**</span> Para evitar o spam e ao mesmo tempo não travar a thread de decisão, todos os cooldowns agora utilizam medição `time.time()` puramente matemática combinada com `asyncio.Lock()`.
- <span style="color: #CC5500;">**Performance Extrema (GPU):**</span> Mantemos o uso de Pinned Memory via PyCUDA na visão.
- <span style="color: #CC5500;">**Zero Hardcode (Fases 5.1 e 6):**</span> Injeção de `config.json` para cooldowns externos, controle do motor de FPS e atalhos dinâmicos do perfil do Pokémon. O método de buff permite atualização sem restart.
- <span style="color: #CC5500;">**Hotkeys Thread-Safe (Fase 6):**</span> Uso da biblioteca `keyboard` mapeando atalhos para interações blindadas no loop do asyncio usando `asyncio.Event()` e `loop.call_soon_threadsafe()`. 

## <span style="color: #CC5500;">**Handoff: Fase 5.2 (Spatial Analyzer & Lógica Desacoplada)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Decisão Arquitetural Adicional:**</span> Recusa da injeção de lógica de negócio no `vision_engine.py` (mantendo-o Zero-Context). A regra espacial (identificar Summon, distância dos mobs e estado `is_boxed`) foi isolada para garantir o <span style="color: #CC5500;">**Single Responsibility Principle (SRP)**</span>.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span> 
  1. Criação do arquivo `modules/spatial_analyzer.py`.
  2. Implementação do método `calculate_spatial_state` usando matemática euclidiana para determinar `mobs_on_screen` e ativação da booleana `is_boxed` (gatilho de 8+ mobs no raio).

## <span style="color: #CC5500;">**Handoff: Fase 8 (Rastreamento Avançado e Template Matching de UI)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span> 
  1. <span style="color: #CC5500;">**Bloqueio Arquitetural (SRP):**</span> Proposta inicial de injetar cálculo de distância da box no motor visual e hardcode de interface foi rejeitada.
  2. <span style="color: #CC5500;">**Expansão Matemática:**</span> O `spatial_analyzer.py` passou a retornar o array `mob_distances` contendo as distâncias euclidianas absolutas para cada monstro identificado, mantendo a responsabilidade no módulo correto.
  3. <span style="color: #CC5500;">**Motor Agnóstico:**</span> Inclusão da função pura `match_template` no `vision_engine.py` sem contexto de interface do jogo.
  4. <span style="color: #CC5500;">**Isolamento Visual de Negócio:**</span> Criação do arquivo `modules/ui_analyzer.py` responsável por conhecer coordenadas, gerenciar a `health_area_roi` e invocar a validação de ícones (Debuffs).
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Atualização do método `calculate_spatial_state` (`spatial_analyzer.py`).
  - Criação do método `match_template` (`vision_engine.py`).
  - Criação do `UIAnalyzer` (`modules/ui_analyzer.py`).
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Integrar os novos retornos de distância e a verificação de debuff do UI Analyzer dentro do Cérebro Lógico / Orquestrador.

## <span style="color: #CC5500;">**Handoff: Fase 9 (Navegação Cavebot - Record & Playback)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span> 
  1. <span style="color: #CC5500;">**Polling Assíncrono (Zero Bloat):**</span> Para capturar os cliques do usuário globalmente sem dependências pesadas ou hooks bloqueantes, a gravação de rota (`Record`) usa `win32api.GetKeyState` iterando em uma thread leve isolada.
  2. <span style="color: #CC5500;">**Cavebot Assíncrono:**</span> A rotina de `Playback` foi construída nativamente como uma Task para o `asyncio`, capaz de injetar esperas nulas (non-blocking) e despachar a movimentação física para a threadpool via `asyncio.to_thread`.
  3. <span style="color: #CC5500;">**Cap de Segurança:**</span> Implementado bloqueio de segurança na leitura do tempo (delay máximo de 20s reduzido para 3s) a fim de impedir que pausas longas e acidentais durante a gravação engasguem o bot durante a repetição.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Criação do arquivo `core/navigator.py`.
  - Implementação do motor de Gravação (`start_recording`, escuta de cliques).
  - Implementação do motor de Repetição (`play_route`, com loop no arquivo `route.json`).
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Integrar os atalhos de Record e Playback dinamicamente no `main.py` utilizando o módulo `keyboard`.

## <span style="color: #CC5500;">**Handoff: Fase 10 (Cérebro Try-Hard Assíncrono - Foco no Summon)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span> 
  1. <span style="color: #CC5500;">**Refatoração do Motor de Decisão:**</span> O antigo arquivo síncrono `core/decision_thread.py` foi reescrito totalmente para `asyncio` e plugado na threadpool principal do `main.py`, substituindo o *stub* genérico anterior.
  2. <span style="color: #CC5500;">**Foco Tático no Summon:**</span> O gatilho de ataque e proteção (`is_boxed`) reage estritamente à proximidade dos monstros em relação ao Summon, garantindo a sobrevivência em lures massivos.
  3. <span style="color: #CC5500;">**Sobrescrita de Cooldown (Emergency Reset):**</span> Criação da função `force_reset_all_timers()` no Orquestrador. Em cenários de desespero (Dense Lure), o bot não respeita delays padronizados, executando uma rajada instantânea de Defesa + Combo + Revive.
  4. <span style="color: #CC5500;">**Atalhos do Cavebot:**</span> Os atalhos F10 (Record) e F11 (Play) solicitados na Fase 9 foram oficializados globalmente no `main.py`.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Modificação em `core/action_orchestrator.py` (`force_reset_all_timers()`).
  - Reescrita completa de `core/decision_thread.py` (Lógica Try-Hard).
  - Atualização do `main.py` (Importações, injeção de dependências do `Navigator` e unificação do loop).
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Validar in-game o disparo de habilidades com os cooldowns resetados dinamicamente e retomar a UI (Fase 7) para exibir a telemetria do orquestrador.

## <span style="color: #CC5500;">**Handoff: Fase 11 (Rotinas de Finalização - Auto Catch e Kill Event via OCR)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span> 
  1. <span style="color: #CC5500;">**Isolamento Assíncrono do OCR:**</span> O OCR de chat não foi misturado ao loop de visão do YOLO para evitar queda severa de FPS. Foi criado um módulo separado chat_analyzer.py rodando em sua própria Task de asyncio.
  2. <span style="color: #CC5500;">**Performance Extrema (Zero Bloat no OCR):**</span> O PyTesseract só é engatilhado se o cálculo matemático de Mean Squared Error (MSE) acusar uma variação visual na ROI (mudança na linha de chat).
  3. <span style="color: #CC5500;">**Auto Catch Geométrico:**</span> O SpatialAnalyzer foi expandido para rastrear as coordenadas normalizadas da classe 2 (cadáveres). O cérebro try-hard injeta o clique utilizando as curvas bezier do MouseController multiplicadas pela resolução absoluta da tela do usuário.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Criação de modules/chat_analyzer.py (Monitoramento de GM).
  - Atualização do modules/spatial_analyzer.py (Retorno de \dead_pokemons\).
  - Atualização de core/decision_thread.py (Integração do MouseController e Auto Catch).
  - Atualização de main.py e config.json (Injeção de dependências do ChatAnalyzer e hotkey do Catch).
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Entrar na Fase de Testes in-game para validar a precisão do clique no cadáver e se o PyTesseract consegue ler corretamente as fontes pequenas do log.

## <span style="color: #CC5500;">**Handoff: Fase 7 (Descongelamento - API Backend FastAPI)**</span>
- <span style="color: #CC5500;">**Status:**</span> Em Andamento.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span> 
  1. <span style="color: #CC5500;">**Servidor Assíncrono (FastAPI):**</span> A base do frontend será alimentada por uma API leve rodando nativamente no loop do Python, permitindo rotas POST para salvar edições diretamente no `config.json`.
  2. <span style="color: #CC5500;">**Streaming de Telemetria (WebSocket):**</span> Implementação de um `ConnectionManager` interno para expor a função `broadcast_log`, permitindo que os alertas da `decision_thread` cheguem na UI sem gargalo de HTTP Polling.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Modificação do `core/config_manager.py` (criação do método `update_full_config`).
  - Criação do `core/api_server.py`.
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Integrar a inicialização do `uvicorn` dentro do script principal (`main.py`) e testar o envio de mensagens WebSocket diretamente da `decision_thread`.

## <span style="color: #CC5500;">**Handoff: Fase 7.1 (Interface Gráfica Integrada — Ligação React ↔ FastAPI)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída.
- <span style="color: #CC5500;">**Consolidação:**</span> O bot passa a possuir uma <span style="color: #CC5500;">**Interface Gráfica Integrada**</span> (Dashboard React + Vite servido localmente, consumindo o `core/api_server.py` via HTTP). A UI lê e grava o estado real do `config.json` em vez de depender de valores estáticos.
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span>
  1. <span style="color: #CC5500;">**Hook de Config (`useBotConfig`):**</span> Criado `frontend/src/hooks/useBotConfig.js`, responsável por `GET http://localhost:8000/api/config` via `useEffect` no mount e por expor `updateConfig`, que faz merge local profundo e dispara `POST /api/config` com o objeto completo (o backend sobrescreve o arquivo inteiro a cada chamada).
  2. <span style="color: #CC5500;">**Fluxo de Dados Top-Down:**</span> `Dashboard.jsx` é o único consumidor do hook; `config`, `loading` e `updateConfig` são passados como props para `AdvancedSettings.jsx`, evitando múltiplas chamadas fetch concorrentes.
  3. <span style="color: #CC5500;">**Novos Campos de Config:**</span> Adicionados `cooldowns.revive` (Delay do Revive, slider 1–15s) e `engine.offensive_mode` (toggle de Ofensividade) tanto em `config.json` quanto nos defaults do `ConfigManager`, substituindo o fallback hardcoded de 5.0s do `revive` em `main.py`.
  4. <span style="color: #CC5500;">**Persistência Imediata:**</span> Qualquer alteração nesses dois controles dispara POST imediato ao backend (sem botão "Salvar"), mantendo o `config.json` em disco sempre sincronizado com a UI.
- <span style="color: #CC5500;">**Componentes Finalizados:**</span>
  - Criação de `frontend/src/hooks/useBotConfig.js`.
  - Atualização de `frontend/src/components/Dashboard.jsx` (integração do hook) e `frontend/src/components/AdvancedSettings.jsx` (campos Delay do Revive e Ofensividade).
  - Atualização de `core/config_manager.py` e `config.json` (campos `cooldowns.revive` e `engine.offensive_mode`).
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Conectar o `useBotConfig` ao stream `/ws/logs` para refletir telemetria em tempo real no `FuzzyLogPanel` (atualmente ainda usa logs estáticos de exemplo).

## <span style="color: #CC5500;">**Handoff: Fase 7.2 (Console Próprio + Bot Rodando de Ponta a Ponta)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída (2026-10-08).
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span>
  1. <span style="color: #CC5500;">**Console Exclusivo:**</span> API presa em `127.0.0.1`, CORS removido e token aleatório por sessão (`X-OTP-Token` / `?token=` no WS). O `main.py` abre o console numa janela `pywebview` (`--no-window` imprime o link).
  2. <span style="color: #CC5500;">**Runtime Compartilhado:**</span> `core/runtime.py` (`BotRuntime`) concentra pause/kill/cavebot/telemetria; hotkeys e API usam os mesmos métodos.
  3. <span style="color: #CC5500;">**Bot abre PAUSADO:**</span> só age após Play no console ou F8.
  4. <span style="color: #CC5500;">**Combate independente do Cavebot:**</span> `decision_thread` reagia apenas com rota tocando; agora combate sempre e só interrompe a rota se ela estiver ativa.
  5. <span style="color: #CC5500;">**Visão na GPU:**</span> `VisionEngine` usa `cuda:0` + FP16 quando disponível; modelo via `engine.model_path` (padrão `models/otp_yolo.pt`), fallback mock se ausente.
- <span style="color: #CC5500;">**Bloqueios:**</span> PyTorch instalado é `+cpu` (GPU não usada); faltam `websockets` e `pywebview`; não há modelo treinado nem Tesseract.
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Instalar PyTorch CUDA (cu130) e iniciar o dataset/treino do YOLO com prints do Poke Alliance.

## <span style="color: #CC5500;">**Handoff: Fase 7.3 (Console por Abas + Config ao Vivo)**</span>
- <span style="color: #CC5500;">**Status:**</span> Concluída (2026-10-08).
- <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas:**</span>
  1. <span style="color: #CC5500;">**UI orientada a Schema:**</span> `frontend/src/schema/features.js` descreve abas → seções → campos (caminho no `config.json`). Cada seção tem `status: ativo | planejado`; as planejadas salvam a config mas mostram "Em breve".
  2. <span style="color: #CC5500;">**Config ao vivo:**</span> `decision_thread` recebe `get_config` e relê a cada frame (toggles, limiar/raio de "cercado", teclas, cooldowns via `orchestrator.sync_cooldowns`). FPS/confiança da visão, ROI do chat e hotkeys também valem sem reiniciar; só `engine.model_path` exige restart.
  3. <span style="color: #CC5500;">**Defaults por merge:**</span> `ConfigManager` mescla `DEFAULT_CONFIG` com o arquivo, garantindo as chaves novas (`features.*`).
  4. <span style="color: #CC5500;">**Captura de tecla:**</span> campos de tecla capturam o pressionamento e convertem para nomes da lib `keyboard`; o backend avisa no log teclas inválidas.
- <span style="color: #CC5500;">**Ambiente:**</span> PyTorch `2.14.1+cu130` validado na RTX 5060 Ti (sm_120); `pywebview` e `websockets` instalados.
- <span style="color: #CC5500;">**Próxima Etapa Pendente:**</span> Dataset + treino do YOLO (classes: summon, selvagem, corpo) e leitura de HP/coordenadas via ROI (minimapa exibe `x, y, z`).
