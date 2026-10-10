---
name: Poketibia CV Bot
description: Bot autônomo baseado em Visão Computacional Híbrida e Utility AI.
stack:
  - python
  - opencv
  - pytesseract
  - pydirectinput
  - scikit-fuzzy
  - bezier
  - fastapi
  - react
architecture_style: hybrid_cv_utility_ai
---

# <span style="color: #CC5500;">**Diretrizes Arquiteturais: Bot Poketibia**</span>

## <span style="color: #CC5500;">**A Regra de Ouro**</span>
- <span style="color: #CC5500;">**Movimentação e Cliques 100% Humanizados:**</span> Todo e qualquer input de mouse DEVE ser gerado utilizando <span style="color: #CC5500;">**Curvas de Bezier**</span> para emular a imperfeição da trajetória humana.
- <span style="color: #CC5500;">**Delays Randômicos:**</span> É estritamente proibido o uso de delays estáticos (ex: `sleep(1)`). Todos os intervalos devem utilizar funções de randomização com ruído para evitar detecção por análise de frequência.

## <span style="color: #CC5500;">**Arquitetura Híbrida de Visão**</span>
- <span style="color: #CC5500;">**Base (Color Masking e OCR):**</span> Leitura de interface, vida e mana deve priorizar cálculo direto de pixels e Template Matching. `PyTesseract` será limitado para leitura de Chat ou textos complexos.
- <span style="color: #CC5500;">**Evolução (YOLO):**</span> O YOLO só será integrado caso o Template Matching falhe na localização de corpos e Pokémons durante lures caóticos (over-layering de sprites).

## <span style="color: #CC5500;">**Lógica de Decisão e Percepção**</span>
- <span style="color: #CC5500;">**Thread Dupla:**</span> Separação estrita entre a thread de <span style="color: #CC5500;">**Percepção**</span> (captura de tela contínua a 20-30 FPS) e a thread de <span style="color: #CC5500;">**Decisão**</span> (leitura de estado e execução de filas com cooldown).
- <span style="color: #CC5500;">**Utility AI / Behavior Trees:**</span> Transição de uma State Machine rígida para Utility AI, permitindo que a ação com maior "nota" de urgência interrompa e assuma o controle (ex: vida cai, cura cancela o andar).
- <span style="color: #CC5500;">**Lógica Fuzzy para Estresse:**</span> Cálculo de "estresse" em lures utilizando `scikit-fuzzy` para definir o uso de skills de defesa com base em múltiplas variáveis difusas (HP, Qtd Monstros, Tempo).

## <span style="color: #CC5500;">**Modo Companion e Aprendizado**</span>
- <span style="color: #CC5500;">**Controle Compartilhado:**</span> O bot deve detectar inputs do jogador (modo Companion) e ceder o controle, assumindo tarefas delegadas de forma transparente.
- <span style="color: #CC5500;">**Eventos Estruturados:**</span> O aprendizado do bot não usará Imitation Learning via pixels brutos. Ele gravará logs de eventos (ex: "6 bichos, vida em 72%, jogador apertou m4") para gerar regras editáveis via Decision Trees.

## <span style="color: #CC5500;">**Segurança e Evasão (Kill Event)**</span>
- <span style="color: #CC5500;">**Anti-Ban Assíncrono:**</span> Leitura de chat para identificação de Game Masters opera com Zero-Bloat. Ferramentas pesadas como Tesseract operam estritamente após filtros de diferença de pixel (MSE), economizando CPU para o Core de Combate.

## <span style="color: #CC5500;">**Interface Gráfica Integrada (Dashboard React + API FastAPI)**</span>
- <span style="color: #CC5500;">**Bot com GUI Própria:**</span> O bot não é mais apenas um script headless: possui uma Interface Gráfica Integrada (`frontend/`, React + Vite + Tailwind) que roda localmente e se comunica com o `otpbot/interface/api_server.py` (FastAPI) via HTTP/WebSocket, sem depender de processos externos de terceiros.
- <span style="color: #CC5500;">**Fonte Única de Verdade:**</span> O `config.json` em disco é a fonte de verdade. A UI lê via `GET /api/config` e grava via `POST /api/config` (agrupando edições seguidas), com o backend sobrescrevendo o arquivo inteiro. A `decision_thread` relê o config a cada frame, então as mudanças valem sem reiniciar (exceto o arquivo do modelo).
- <span style="color: #CC5500;">**Console por Schema:**</span> Abas, seções e campos vêm de `frontend/src/schema/features.js`, cada campo apontando para um caminho do `config.json`. Seções têm `status: ativo | planejado` para a UI nunca prometer o que o bot ainda não faz.
- <span style="color: #CC5500;">**Console Exclusivo:**</span> API presa em `127.0.0.1`, sem CORS, com token aleatório por execução (`X-OTP-Token`). Janela própria via `pywebview`.
- <span style="color: #CC5500;">**Telemetria em Tempo Real:**</span> `/ws/logs` transmite o log do bot; `/api/status` entrega estado, telemetria e as leituras da tela (HP, EXP, postura, time).

## <span style="color: #CC5500;">**Calibração da Interface**</span>
- <span style="color: #CC5500;">**Perfis por Resolução:**</span> A interface do cliente não escala com o monitor. As regiões ficam em pixels reais por resolução (`calibration.profiles["LxA"]`) e o perfil é escolhido pelo tamanho do frame.
- <span style="color: #CC5500;">**Leitura por Cor:**</span> Barras lidas por máscara HSV e última coluna colorida; postura pela mediana do brilho do fundo da mão ativa. Leitura incerta retorna `None` e o bot não age sobre ela.
