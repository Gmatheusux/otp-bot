# Prompt de pesquisa — estado da arte para o OTP Bot

> Cole o bloco abaixo numa ferramenta de pesquisa profunda (Claude Research, ChatGPT Deep Research, Perplexity Pro, Gemini Deep Research). Ele já traz o contexto do projeto, o hardware e o formato de resposta esperado.

---

```text
Você é um engenheiro sênior de visão computacional, sistemas de tempo real e IA aplicada a jogos.
Faça uma pesquisa profunda e ATUAL (priorize fontes de 2025–2026; diga a data e a versão de cada
ferramenta citada) para definir a arquitetura de um assistente de jogo externo, 100% customizado
para o PC descrito abaixo.

## 1. Contexto do projeto
- Jogo: Poke Alliance, um servidor de "Poketibia" (OT Pokémon), jogo 2D top-down baseado em
  OpenTibia/OTClient. Sprites pequenos em grid de tiles, interface com painéis fixos (HP, battle
  list, hotbar, minimapa com coordenadas x,y,z, chat).
- O programa é EXTERNO: só lê pixels da tela e envia teclado/mouse pelo sistema operacional
  (SendInput). Requisito inegociável: nunca ler memória, injetar DLL, interceptar pacotes,
  usar drivers de kernel ou modificar o cliente.
- Objetivo da v1.0: ciclo de hunt automatizado — andar numa rota gravada (ou num mapa), juntar
  selvagens (lure), parar quando a quantidade for suficiente, usar antídoto se houver debuff,
  soltar o combo, matar, jogar pokébola SOMENTE nos corpos de pokémons shiny e seguir a rota.
  Se tomar dano: trocar para o pokémon curador, rotação de cura, revive (zera recarga) e voltar
  ao pokémon de dano.
- Comportamento: jogador "try hard" (decisões rápidas e eficientes), mas SEMPRE dentro de
  limites humanos (tempo de reação, ações por minuto, precisão de mira) e com variação natural
  de ritmo entre ações, sessões e ao longo do dia.
- Aprendizado: o assistente deve melhorar a eficiência da hunt (EXP/h, capturas/h, zero mortes)
  a partir de sessões gravadas e de demonstrações do próprio jogador.

## 2. Hardware e ambiente (otimizar para ISTO, não para o caso genérico)
- GPU: NVIDIA GeForce RTX 5060 Ti 8 GB (arquitetura Blackwell, sm_120, PCIe 5.0 x8).
- CPU: AMD Ryzen 7 5800X3D (8 núcleos / 16 threads, 96 MB de L3).
- RAM: 32 GB.
- Windows 10/11, dois monitores: o jogo fica sozinho no monitor principal; o outro monitor tem o
  console do bot e tarefas leves (navegador, música). Resoluções usadas: 3440x1440 e 1920x1080.
- O jogo, a captura, a inferência e o bot rodam juntos no mesmo PC; o treino pode rodar com o
  jogo fechado.

## 3. Stack atual (para comparar, não para manter por inércia)
Python 3.14, asyncio; captura com mss; YOLO via Ultralytics em CUDA + FP16 (ainda sem modelo
treinado); OpenCV (máscara HSV para barras, template matching para itens); Tesseract para o chat;
pydirectinput para entrada; FastAPI + React (Vite/Tailwind) + pywebview como console local.

## 4. Perguntas de pesquisa
Para cada área: liste as 2–4 melhores opções atuais, compare em tabela e recomende UMA para
este PC, justificando com números (latência, VRAM, CPU, FPS) medidos ou publicados.

A. Captura de tela no Windows
   - DXGI Desktop Duplication vs Windows Graphics Capture vs mss/GDI (bibliotecas Python como
     dxcam, bettercam, windows-capture). Latência por frame em 3440x1440, uso de CPU/GPU,
     captura só da janela do jogo vs monitor inteiro, comportamento com janela sem borda e com
     HDR/escala do Windows (DPI). Como evitar cópias GPU→CPU desnecessárias até a inferência.

B. Detecção de objetos em tempo real (sprites 2D pequenos e sobrepostos)
   - Famílias atuais: YOLO (versões mais recentes da Ultralytics e forks), RT-DETR/D-FINE/
     DEIM e similares. Qual escala de modelo (n/s/m) cabe no orçamento de ~2–3 GB de VRAM com o
     jogo aberto e entrega ≥ 30 FPS em recortes da área do jogo.
   - Export e aceleração na RTX 50xx: TensorRT (FP16, INT8, FP8?), ONNX Runtime + TensorRT EP,
     suporte real ao sm_120 hoje (versões de CUDA/cuDNN/TensorRT/PyTorch que funcionam).
   - Técnicas para objetos pequenos: tiling/SAHI, entrada em resolução nativa do tile do jogo,
     anchors, recorte só da área do jogo.
   - Classes necessárias: meu pokémon, selvagem, selvagem shiny, corpo, corpo de shiny, itens no
     chão. Diferenciar shiny por cor de sprite: detector com classe própria vs detector + classificador
     leve de recorte vs análise de paleta/histograma.
   - Rastreamento multi-objeto para lembrar qual selvagem era shiny até virar corpo
     (ByteTrack, BoT-SORT, OC-SORT, trackers mais novos): custo em CPU e robustez com oclusão.

C. Dataset e rotulagem com pouco esforço humano
   - Ferramentas de rotulagem locais (CVAT, Label Studio, X-AnyLabeling, Roboflow local),
     pré-rotulagem automática com modelos de base (SAM 2/SAM 3, Grounding DINO, YOLO-World,
     Florence-2 ou mais novos) e active learning.
   - Geração sintética: compor sprites do jogo sobre fundos de mapa para criar lures cheios
     artificiais. Quanto isso substitui dados reais?
   - Quantas imagens por classe são necessárias para mAP alto nesse domínio; augmentations certas
     para pixel art (sem borrar, sem rotação).
   - Plano de treino na RTX 5060 Ti 8 GB: batch, tamanho de imagem, AMP, tempo estimado por época.

D. Leitura de interface (texto e números)
   - OCR rápido para fontes pixel/bitmap pequenas (números de HP, coordenadas x,y,z, nomes na
     battle list, chat): Tesseract vs PaddleOCR vs EasyOCR vs OCR por template de dígitos
     vs modelo CRNN minúsculo treinado com a fonte do jogo. Latência e precisão em CPU.
   - Detecção de ícones de status (debuff) e de cooldown de golpes na barra de skills.

E. Navegação
   - Localização pelo minimapa (template matching do minimapa contra um mapa completo, ou
     leitura das coordenadas por OCR) e pathfinding (A*, JPS) num grid de tiles com andares (z).
   - Como montar o mapa a partir de minimapas gravados ou de arquivos públicos do servidor.
   - Detecção de "travado", "empurrado" ou "teleportado" e recuperação.

F. Decisão e aprendizado
   - Arquitetura de decisão para jogo em tempo real: Utility AI vs Behavior Trees vs GOAP vs
     state machines hierárquicas; bibliotecas Python maduras.
   - Aprendizado por imitação a partir de LOGS ESTRUTURADOS (estado: HP, nº de selvagens,
     debuff, recargas; ação; resultado), não de pixels brutos: behavior cloning com árvores de
     decisão/gradient boosting vs redes pequenas; como evitar que copie erros do jogador.
   - Otimização de parâmetros da hunt com poucas tentativas reais (Bayesian optimization /
     Optuna, bandits multi-armed): tamanho do lure, ponto de parada, limiar de HP.
   - Vale a pena reforço (RL) com um simulador simplificado do ciclo de hunt? Custo vs ganho.

G. Comportamento humano e limites motores (área central)
   - Modelos de movimento de mouse com base científica: lei de Fitts, perfil de jerk mínimo,
     WindMouse, curvas de Bézier com overshoot e correção, modelos aprendidos de trajetórias
     humanas reais (datasets públicos de movimento de mouse). Qual reproduz melhor velocidade,
     aceleração e erro de mira humanos.
   - Distribuições de tempo humano com referências: tempo de reação simples e de escolha
     (lognormal/ex-Gaussiana), duração de tecla apertada e intervalo entre teclas (keystroke
     dynamics), APM sustentável de jogadores rápidos em jogos 2D, efeito de cansaço e ritmo
     circadiano.
   - Como introduzir variação de jogabilidade de forma coerente (não só ruído): perfis de estilo,
     erros ocasionais plausíveis, pausas, mudança de ritmo entre sessões — mantendo eficiência.
   - Como MEDIR se o comportamento ficou humano: métricas e testes estatísticos para comparar
     logs do bot com logs do próprio jogador (distribuições de intervalos, entropia, autocorrelação).
   - Entrada pelo sistema operacional: SendInput vs alternativas em modo usuário; diferenças
     entre eventos sintéticos e de hardware (flag LLMHF_INJECTED etc.) e o que isso implica
     para um programa que se recusa a usar drivers ou injeção.

H. Desempenho do pipeline em um único PC
   - Arquitetura de processos/threads em Python para captura → inferência → decisão → entrada
     com latência total < 100 ms: asyncio + threads vs multiprocessing vs subinterpretadores/
     free-threaded Python 3.14; uso de memória compartilhada; afinidade de CPU no 5800X3D.
   - Como medir e limitar o impacto no FPS do jogo (prioridade de processo, limite de FPS da
     visão, CUDA streams).

I. Empacotamento e entrega
   - PyInstaller vs Nuitka vs alternativas para empacotar Python + PyTorch/TensorRT + console
     web num executável Windows; tamanho final, tempo de inicialização, atualização automática.
   - Rodar só com ONNX Runtime/TensorRT (sem PyTorch) no executável final para reduzir tamanho.

J. Projetos de referência
   - Projetos open source atuais de automação por visão computacional para jogos 2D (OpenTibia,
     Tibia, MMOs 2D, RPA de jogos) que só leem a tela: o que fazem bem, arquitetura, licença.

## 5. Formato da resposta
1. Resumo executivo (10 linhas): a stack recomendada para este PC, em uma tabela
   "componente → escolha → por quê → custo estimado (VRAM/CPU/latência)".
2. Uma seção por área (A–J) com: tabela comparativa, recomendação, riscos, e links para as
   fontes (documentação oficial, papers, benchmarks, repositórios) com data de acesso.
3. Orçamento de recursos do pipeline completo rodando junto com o jogo (VRAM, RAM, núcleos de CPU,
   latência ponta a ponta).
4. Roteiro de implementação em fases, com critério de pronto mensurável em cada fase
   (ex.: "mAP50 ≥ 0,9 na classe corpo_shiny em 500 imagens de validação").
5. Lista do que NÃO usar e por quê (obsoleto, não suporta sm_120, pesado demais para 8 GB).

Regras: não invente números; quando não houver benchmark público, diga "sem dado" e proponha
como medir. Não recomende nada que leia memória, injete código, use driver de kernel ou altere o
cliente do jogo.
```
