# Escopo do OTP Bot e comparativo com o bot externo

> **Atualização (2026-10-09):** as respostas da anamnese definiram as regras da v1.0 em
> [`docs/ESPECIFICACAO.md`](../ESPECIFICACAO.md). Algumas ideias vindas do bot externo saíram do escopo (combo sequencial,
> Stun, rota por *Map Marks*, poção, itens por tempo); a lista de removidos e o motivo estão na §8 do
> [`GUIA.md`](../../GUIA.md). A comparação abaixo continua válida como retrato do estado do código.

Este documento junta **todo o escopo do projeto** (o que existe, o que está pela metade e o que falta) com a comparação
contra o bot externo *Pokemon Aliiance V3* (canal *PokeTibia Bot*, [playlist com 11 vídeos](https://www.youtube.com/playlist?list=PLbBSxzsuhBwc)).

- Relatórios de cada vídeo: `01-…` a `11-…` nesta pasta (gerados pelo Gemini com `tools/analisar_playlist.py`).
- **Etapas e estado do projeto:** [`GUIA.md`](../../GUIA.md).
- Estado do código conferido em 2026-10-09 (`core/`, `modules/`, `frontend/src/schema/features.js`, `config_manager.py`).

---

## Legenda

| Símbolo | Significado |
|---|---|
| ✅ | Funciona hoje |
| ⚠️ | Implementado, mas **bloqueado** (sem modelo YOLO) ou **falta validar no jogo** |
| 🟡 | Só configuração: o console salva, o bot não executa |
| ❌ | Não existe |
| ⭐ | Nosso é melhor que o do bot externo |
| — | O bot externo não tem |

---

## 1. Como cada bot funciona

| | OTP Bot (nosso) | Bot externo |
|---|---|---|
| Tecnologia | Python + asyncio, YOLO na GPU, OpenCV, console React | AutoIt/AutoHotkey compilado (inferência), 2019 |
| Como enxerga o jogo | Print da tela: IA (YOLO) para selvagens e corpos, cor para as barras, template matching para sprites | Print da tela: só template matching com "tolerância" |
| De onde vem o "tem selvagem?" | YOLO na área do jogo (**sem modelo treinado**) | **Lista Battle** (rosto do pokémon recortado) |
| Sincronia | Lê o estado ao vivo (HP, Pokébar, postura) a cada frame | Tempos fixos em ms configurados pelo usuário |
| Rota | Cliques gravados em posições absolutas da tela | Ícones de *Map Marks* procurados no minimapa |
| Entrada | Teclado + mouse humanizado (Bézier, easing, ruído) | Teclado + clique seco |
| Interface | Um console por abas, configuração ao vivo, API local com token | Várias janelas e 3 programas (bot, SinaptyBot, Hunt Analyzer) |

### Pré-requisitos do cliente (do vídeo 02, valem para nós também)

| Exigência | Motivo | Nosso |
|---|---|---|
| Escala do Windows em **100%** | Prints e cliques desalinham | ❌ não tratamos DPI nem avisamos |
| **Classic view**; 1 painel à esquerda e 1 à direita | Área do jogo com tamanho fixo | 🟡 implícito na calibração, sem checklist |
| **Desligar "Show a Special Shader on Shinies Corpses"** | O brilho muda as cores do corpo shiny | ❌ não documentado |
| Battle aberta e grande | Mais alvos visíveis | ❌ (ainda não lemos a Battle) |
| Minimapa num zoom padrão | Tamanho fixo dos ícones | ❌ (necessário para navegar por marcas) |

---

## 2. Escopo completo × bot externo

### 2.1 Núcleo e percepção
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Loop único asyncio (percepção, calibração, decisão, chat, API) | ✅ | — | |
| Captura de tela | ✅ | ✅ | |
| Visão por IA (YOLO, CUDA + FP16) | ⚠️ sem modelo; roda em *mock* | — | Bloqueio nº 1 do projeto |
| Template matching de sprites | ✅ ⭐ biblioteca + teste de semelhança | ✅ | |
| Leitura de barras por cor (HP jogador, HP pokémon, EXP, Pokébar, postura) | ✅ ⭐ | 🟡 só barra de vida | |
| Calibração por resolução (3440×1440, 1920×1080) com teste | ✅ ⭐ | 🟡 arrastar sobre o jogo | |
| **Leitura da lista Battle** | ❌ região calibrada, não usada | ✅ núcleo do bot | Maior lacuna |
| Leitura das coordenadas `x, y, z` | ❌ região calibrada, não usada | ❌ | |
| Tratamento de DPI / escala do Windows | ❌ | Exige 100% | Risco real em notebook |
| Detecção de configuração do cliente (Battle fechada, shader…) | ❌ | ❌ | |

### 2.2 Combate
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Combo em área / combar enquanto anda | ⚠️ depende do YOLO | ✅ Lure Attack | |
| Defesa quando cercado (defesa → combo → revive, para a rota) | ⚠️ depende do YOLO | ✅ parecido | |
| Gatilho "N selvagens colados" | ⚠️ ⭐ adaptativo | Tempo fixo | |
| Postura automática (ler e clicar a mão) | ✅ ⭐ | ✅ por tecla | Falta opção por tecla |
| Combo sequencial (até 6 teclas + delay + tempo total) | ❌ | ✅ | |
| Perfil de combo por pokémon | ❌ | ✅ | |
| 2º revive (box que não morre numa rotação) | ❌ | ✅ | |
| Fugir antes do revive | ❌ | ✅ | |
| Tecla Stun | ❌ | ✅ | |
| Mira automática / alvo único / finalizar sobras | 🟡 | ✅ | |
| Alvos por sprite (lista normal e lista shiny) | ❌ | ✅ | |
| Regras de shiny (máx. revives, atacar/não, delay) | 🟡 só "prioridade shiny" | ✅ | |
| Ignorar espécies | 🟡 | 🟡 implícito | |

### 2.3 Cura
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Revive (tecla + cooldown) | ✅ | ✅ | |
| Cura com pokémon (rotação + revive no curador + aborta se aparecer selvagem) | ⚠️ ⭐ falta validar no jogo | ✅ mais simples | |
| Achar curador/farm na Pokébar | 🟡 por posição fixa | ✅ por sprite | |
| Trocar pokémon por clique ou tecla | ⚠️ falta validar se o clique troca | ✅ | |
| Botões de teste da cura | ✅ ⭐ | — | |
| Poção por % de HP | 🟡 | ✅ | |
| Instant revive (pokémon caiu) | ❌ | ✅ | |
| Medicine (status) | 🟡 | ✅ tecla | Falta detectar o status |

### 2.4 Itens e consumíveis
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Biblioteca de sprites (print, recorte, categoria, tecla, teste) | ✅ ⭐ | 🟡 prints soltos | |
| Uso automático de itens pela biblioteca | 🟡 | — | |
| Comida por intervalo | 🟡 | ✅ | |
| Itens por tempo (boost XP, Shiny Charm, charm de evento) | ❌ | ✅ 3 slots | Generalizar a "comida" |

### 2.5 Rota (cavebot)
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Gravar a rota clicando no minimapa | ✅ ⭐ | 🟡 marcações manuais | |
| Tocar em loop com mouse humanizado | ✅ | ✅ | |
| Opções: loop, esperar 1º ponto, variar caminho | 🟡 a UI salva, o `navigator.py` não lê | — | |
| Referência da rota | ❌ pixel absoluto (frágil) | ✅ ícone da marca, se corrige sozinho | |
| Ponto de combate × passagem | ❌ | ✅ | |
| Espera para a box se formar (global / por ponto) | ❌ | ✅ | |
| Order (posicionar o pokémon para centralizar a box) | ❌ | ✅ | |
| Poke Stop | ❌ | ✅ | |
| Escada / troca de andar | ❌ | ✅ flag | |
| Navegação por coordenadas reais | ❌ | ❌ | Ultrapassaria o bot externo |
| Loot | — não precisa (auto loot no Poke Alliance) | ✅ | |

### 2.6 Captura
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Achar o corpo e clicar com a pokébola | ⚠️ depende do YOLO | ✅ por sprite | |
| Captura só sem selvagens vivos | ⚠️ | 🟡 | |
| Achar o corpo por sprite (plano B sem YOLO) | ❌ | ✅ | |
| Várias imagens por alvo | 🟡 biblioteca aceita, sem agrupar | ✅ | |
| Categorias com pokébola própria | ❌ uma tecla | ✅ Catch 1/2/3 | |
| Delay pós-morte / segurar a rota | ❌ | ✅ | |

### 2.7 Segurança e alertas
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Monitor de GM no chat (desliga o bot) | ✅ ⭐ precisa do Tesseract | 🟡 alerta | |
| Alerta de jogador na tela | 🟡 | ❌ | |
| Alerta de mensagem privada | 🟡 | ✅ | |
| Alerta de morte / desconexão | 🟡 morte; ❌ desconexão | ✅ | |
| Som | 🟡 | ✅ | |
| Avisos no Telegram | 🟡 | — | |
| Respostas automáticas | **Fora do escopo** | ✅ | Ver §3 |

### 2.8 Console, controle e telemetria
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Console por abas gerado do schema | ✅ ⭐ | — | |
| Configuração ao vivo, sem reiniciar | ✅ ⭐ | — | |
| Abre pausado; Play/Pause; hotkeys F8–F11 | ✅ | ✅ Ctrl+Y / Ctrl+F5 | |
| API local com token + WebSocket de log | ✅ ⭐ | — | |
| Leitura ao vivo da tela no Início | ✅ ⭐ | — | |
| Telemetria (GPU/CPU, FPS, detecções, sessão) | ✅ | 🟡 | |
| Hunt Analyzer (EXP/h, kills/h, consumíveis) | ❌ | ✅ | Já lemos a barra de EXP |
| Seletor de tecla (lista + captura) | ✅ | ✅ | |
| Botões do mouse como atalho | ❌ | ✅ | |
| Vários clientes | ❌ | ✅ | |

### 2.9 Extras
| Funcionalidade | Nosso | Bot externo | Observação |
|---|---|---|---|
| Daily da guild (tier e elemento) | 🟡 | — | |

---

## 3. Fora do escopo

- **Respostas automáticas a jogadores ou GMs.** Servem para o bot se passar por humano diante da moderação; é o caminho
  mais curto para ban. Mantemos o comportamento atual: **parar o bot e avisar o jogador**.

---

## 4. Placar

| | Qtde. |
|---|---|
| Itens na seção 2 | 70 |
| ✅ Funcionam hoje | 19 |
| ⚠️ Prontos, mas bloqueados ou sem validação | 8 |
| 🟡 Só configuração | 16 |
| ❌ Não existem | 25 |
| Sem status (loot desnecessário; fora do escopo) | 2 |
| ⭐ Melhores que o bot externo (entre os acima) | 14 |

**Leitura:** a base (percepção por cor, calibração, sprites, console, mouse, segurança) está sólida e à frente do bot
externo. O que falta é a **camada de jogo**: hoje quase todo o combate e a captura esperam o YOLO. A lista Battle e os
sprites destravam isso já, e o cavebot precisa virar um cavebot de lure.

O que fazer, em ordem: [`GUIA.md`](../../GUIA.md).
