---
name: Poketibia CV Bot
description: Bot autônomo baseado em Visão Computacional Híbrida e Utility AI.
stack:
  - python
  - opencv
  - pytesseract
  - pydirectinput
  - ultralytics
  - fastapi
  - react
architecture_style: hybrid_cv_utility_ai
---

# <span style="color: #CC5500;">**Diretrizes Arquiteturais: Bot Poketibia**</span>

## <span style="color: #CC5500;">**A Regra de Ouro**</span>
- <span style="color: #CC5500;">**Movimentação e Cliques 100% Humanizados:**</span> Todo e qualquer input de mouse DEVE ser gerado utilizando <span style="color: #CC5500;">**Curvas de Bezier**</span> para emular a imperfeição da trajetória humana.
- <span style="color: #CC5500;">**Delays Randômicos:**</span> É estritamente proibido o uso de delays estáticos (ex: `sleep(1)`). Todos os intervalos devem utilizar funções de randomização com ruído para evitar detecção por análise de frequência.
- <span style="color: #CC5500;">**Limites Humanos (`core/humanizer.py`):**</span> Toda tecla e todo clique passam pelo `Humanizer`: teto de APM (padrão 180), intervalo mínimo entre entradas (80 ms), tempo de reação a cada mudança de fase (mínimo 160 ms), tecla segurada por tempo gaussiano, recargas sempre **acima** da configurada e mira com desvio de pixels. Proibido zerar ou furar cooldowns (o antigo `force_reset_all_timers` foi removido).
- <span style="color: #CC5500;">**Sem Injeção:**</span> O bot só lê pixels da tela e envia entradas pelo sistema operacional (SendInput). Nunca lê memória, injeta DLL, intercepta pacotes ou altera o cliente.

## <span style="color: #CC5500;">**Arquitetura Híbrida de Visão**</span>
- <span style="color: #CC5500;">**Base (Color Masking e OCR):**</span> Leitura de interface, vida e mana deve priorizar cálculo direto de pixels e Template Matching. `PyTesseract` será limitado para leitura de Chat ou textos complexos.
- <span style="color: #CC5500;">**YOLO na GPU (decidido):**</span> Template Matching falha com sprites sobrepostos em lures cheios; selvagens, shiny e corpos são detectados por YOLO (CUDA + FP16) treinado com prints do Poke Alliance. Template Matching fica para itens e ícones da interface.

## <span style="color: #CC5500;">**Lógica de Decisão e Percepção**</span>
- <span style="color: #CC5500;">**Thread Dupla:**</span> Separação estrita entre a thread de <span style="color: #CC5500;">**Percepção**</span> (captura de tela contínua a 20-30 FPS) e a thread de <span style="color: #CC5500;">**Decisão**</span> (leitura de estado e execução de filas com cooldown).
- <span style="color: #CC5500;">**Utility AI / Behavior Trees:**</span> Transição de uma State Machine rígida para Utility AI, permitindo que a ação com maior "nota" de urgência interrompa e assuma o controle (ex: vida cai, cura cancela o andar).
- <span style="color: #CC5500;">**Estresse em Lures (a definir):**</span> O protótipo `scikit-fuzzy` foi removido por não estar ligado ao bot. A regra de defesa atual é "N selvagens no raio do summon"; uma pontuação de estresse (HP, mobs, tempo) volta depois das respostas da anamnese (`docs/ANAMNESE.md`).

## <span style="color: #CC5500;">**Modo Companion e Aprendizado**</span>
- <span style="color: #CC5500;">**Controle Compartilhado:**</span> O bot deve detectar inputs do jogador (modo Companion) e ceder o controle, assumindo tarefas delegadas de forma transparente.
- <span style="color: #CC5500;">**Eventos Estruturados:**</span> O aprendizado do bot não usará Imitation Learning via pixels brutos. Ele gravará logs de eventos (ex: "6 bichos, vida em 72%, jogador apertou m4") para gerar regras editáveis via Decision Trees.

## <span style="color: #CC5500;">**Segurança e Evasão (Kill Event)**</span>
- <span style="color: #CC5500;">**Anti-Ban Assíncrono:**</span> Leitura de chat para identificação de Game Masters opera com Zero-Bloat. Ferramentas pesadas como Tesseract operam estritamente após filtros de diferença de pixel (MSE), economizando CPU para o Core de Combate.

## <span style="color: #CC5500;">**Interface Gráfica Integrada (Dashboard React + API FastAPI)**</span>
- <span style="color: #CC5500;">**Bot com GUI Própria:**</span> O bot não é mais apenas um script headless: possui uma Interface Gráfica Integrada (`frontend/`, React + Vite + Tailwind) que roda localmente e se comunica com o `core/api_server.py` (FastAPI) via HTTP/WebSocket, sem depender de processos externos de terceiros.
- <span style="color: #CC5500;">**Fonte Única de Verdade:**</span> O `config.json` em disco é a fonte de verdade. A UI lê via `GET /api/config` e grava via `POST /api/config` (agrupando edições seguidas), com o backend sobrescrevendo o arquivo inteiro. A `decision_thread` relê o config a cada frame, então as mudanças valem sem reiniciar (exceto o arquivo do modelo).
- <span style="color: #CC5500;">**Console por Schema:**</span> Abas, seções e campos vêm de `frontend/src/schema/features.js`, cada campo apontando para um caminho do `config.json`. Seções têm `status: ativo | planejado` para a UI nunca prometer o que o bot ainda não faz.
- <span style="color: #CC5500;">**Console Exclusivo:**</span> API presa em `127.0.0.1`, sem CORS, com token aleatório por execução (`X-OTP-Token`). Janela própria via `pywebview`.
- <span style="color: #CC5500;">**Telemetria em Tempo Real:**</span> `/ws/logs` transmite o log do bot; `/api/status` entrega estado, telemetria e as leituras da tela (HP, EXP, postura, time).

## <span style="color: #CC5500;">**Hardware Alvo e Monitores**</span>
- <span style="color: #CC5500;">**PC de Referência:**</span> RTX 5060 Ti **8 GB**, Ryzen 7 5800X3D, 32 GB de RAM. Orçamento de VRAM: modelo de visão + inferência abaixo de ~3 GB para sobrar para o jogo; treino com o jogo fechado.
- <span style="color: #CC5500;">**Dois Monitores:**</span> O jogo fica no monitor **principal** (único que o `pydirectinput` alcança); o console e o resto ficam no outro. `engine.monitor = 0` escolhe o principal sozinho (o `mss` nem sempre o lista como 1).

## <span style="color: #CC5500;">**Calibração da Interface**</span>
- <span style="color: #CC5500;">**Perfis por Resolução:**</span> A interface do cliente não escala com o monitor. As regiões ficam em pixels reais por resolução (`calibration.profiles["LxA"]`) e o perfil é escolhido pelo tamanho do frame.
- <span style="color: #CC5500;">**Leitura por Cor:**</span> Barras lidas por máscara HSV e última coluna colorida; postura pela mediana do brilho do fundo da mão ativa. Leitura incerta retorna `None` e o bot não age sobre ela.
