# <span style="color: #CC5500;">**Contexto Ativo: Bot Poketibia**</span>

## <span style="color: #CC5500;">**Escopo Global e Progresso**</span>
- <span style="color: #CC5500;">**Fase 1 (Concluída):**</span> Logger de tela e motor base de Visão (`vision.py`) para leitura via OpenCV/PyTesseract homologados.
- <span style="color: #CC5500;">**Fase 1.5 (Concluída):**</span> Motor matemático de Mouse (`core/mouse.py`) com trajetórias Bezier humanizadas implementadas.
- <span style="color: #CC5500;">**Fase 2 (Concluída):**</span> Módulo de Visão de Alta Performance (`modules/vision_engine.py`) focado em YOLOv8 + TensorRT + PyCUDA via abstração Zero-Context (matemática pura).

## <span style="color: #CC5500;">**Decisões Arquiteturais Tomadas**</span>
- <span style="color: #CC5500;">**Zero-Context & Matemática:**</span> Todos os módulos de hardware (visão, mouse) operam como conversores brutos (pixels -> coordenadas -> movimentos reais), sem conhecimento das regras de negócio do jogo.
- <span style="color: #CC5500;">**Performance Extrema (GPU):**</span> Uso de Pinned Memory via PyCUDA para zerar o gargalo de alocação de memória na transição CPU-GPU para as inferências da engine de visão.
- <span style="color: #CC5500;">**Utility AI:**</span> Decisão de abandonar State Machines em favor de árvores de utilidade fuzzy (`scikit-fuzzy`).

## <span style="color: #CC5500;">**Handoff: Preparação para a Fase 3**</span>
- <span style="color: #CC5500;">**Status:**</span> Prontos para iniciar a próxima fase focada na finalização das interações de input.
- <span style="color: #CC5500;">**Próxima Etapa (Fase 3):**</span> Arquitetura matemática do Teclado (`core/keyboard.py`), incorporando atrasos de input aleatorizados e humanização dos keystrokes, ou integração do `vision_engine.py` com a arquitetura `Utility AI`.
