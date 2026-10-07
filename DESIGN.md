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
