# GUIA DO PROJETO: OTP Bot v1.0

> **Este é o documento-mestre do projeto.** Toda conversa de desenvolvimento começa lendo este guia e termina
> atualizando-o. Se algo aqui contradiz a memória de uma conversa, **vale o que está aqui e no código**.

"OTP" = **OT Pokémon** (Poke Alliance / Poketibia). Sem relação com One Time Password.

---

## 0. Estado atual

| Campo | Valor |
|---|---|
| **Etapa atual** | **Em paralelo: E06 e E15** (abertas em 2026-10-10; regras na §1.5). E09 liberada (depende só da E08); **E05 liberada** (depende só da E04) |
| Última etapa concluída | E04: coleta de prints e ferramenta de rotular (2026-10-10); antes, E08 (2026-10-10) |
| Bloqueios | Material do jogo: faltam shiny vivo e corpo de shiny (classe `corpo_shiny` com 0 exemplos), Battle cheia, debuff etc. (§6); E06 coleta prints ao vivo com o usuário (§1.5) |
| Ferramentas | Tesseract 5.4.0 instalado em `C:\Program Files\Tesseract-OCR` (2026-10-10, só inglês; português na E07). Teste com imagem gerada: lê `[GM] Tutor: …` certo. Falta validar com print real do chat |
| Git | ✅ liberado em 2026-10-09; remoto `origin` = github.com/Gmatheusux/otp-bot (branch `main`) |
| Material do jogo recebido | 🟡 4 vídeos de hunt manual (3 em 3440, 1 em 1920), dataset da visão com 46 prints rotulados (ver §6) |
| Última atualização | 2026-10-10, conversa E04 |

---

## 1. Como usar este guia em cada conversa

### 1.1 Para você, ao abrir uma conversa nova

Use o prompt da etapa em **[`docs/PROMPTS.md`](docs/PROMPTS.md)**: há um para cada etapa, com os pontos de atenção
específicos dela. Se preferir a versão genérica, cole esta mensagem trocando o número da etapa:

```
Vamos executar a etapa E0X do OTP Bot. Leia o GUIA.md inteiro e os documentos que a etapa E0X lista em
"Leitura obrigatória" antes de qualquer coisa. Siga o protocolo da seção 1.2. Comece me dizendo o que
entendeu do escopo, o que vai fazer e o que está fora do escopo.
```

### 1.2 Protocolo da IA (obrigatório)

**No início**
1. Ler este guia inteiro, a etapa da vez e os documentos da "Leitura obrigatória" dela.
2. Conferir que a etapa anterior está ✅ na §4. Se não estiver, **parar e avisar**.
3. Ler o código que a etapa vai tocar **antes** de propor mudanças. Nunca citar arquivo, função ou config sem ter aberto.
4. Resumir para o usuário: escopo, plano e o que está fora. Esperar o "ok" antes de mudanças grandes.

**Durante**
5. Fazer **só** o que a etapa pede. Trabalho de outra etapa vira anotação na passagem, não código.
6. **Fatos do jogo** (nomes, mensagens, posições, regras) vêm de `docs/ESPECIFICACAO.md`, do material do jogo ou do
   usuário. **Nunca inventar.** Se faltar, perguntar. Fato novo confirmado → registrar na especificação com a fonte
   (`[Exx]` ou `[Qnn]`).
7. Seguir a arquitetura de `docs/ARQUITETURA.md`. Mudança de arquitetura → **perguntar**, registrar como decisão nova
   (D20, D21…) e atualizar o documento.
8. Testes: todo módulo novo com testes em `tests/`; `python -m pytest` passando antes de encerrar.
9. Nada de rodar o bot apertando teclas no jogo sem o usuário pedir.

**No fim (rito de encerramento)**
10. Conferir os **critérios de aceite** da etapa, um a um, com evidência (teste, log, print).
11. Atualizar este guia:
    - §0 Estado atual (etapa atual = a próxima);
    - status da etapa na §4 (✅ concluída, 🟡 parcial com o que faltou);
    - checkboxes da etapa na §5;
    - entrada nova na §7 Registro de passagem.
12. Atualizar `docs/ESPECIFICACAO.md` e `docs/ARQUITETURA.md` se algo mudou.
13. Acrescentar uma entrada curta no `ActiveContext.md` (diário, conforme o `task.md`).
14. Commit semântico (`feat(eXX): …`, `docs(eXX): …`) e, se houver remoto, push. Pedir confirmação ao usuário antes do push.
15. Dizer ao usuário qual é a próxima etapa e o que ele precisa providenciar para ela.

### 1.3 Conversa central (orquestração)

Existe **uma conversa central** que não executa etapas: ela coordena. Cada etapa roda numa conversa própria, aberta
por um card de sessão (o app cria a worktree sozinho).

**Papel da central, a cada etapa que termina:**
1. Reler este guia na `main` (nunca confiar na memória da conversa).
2. Conferir o portão de qualidade:
   - a etapa está ✅ na §4 (ou 🟡 com o que faltou) e tem entrada na §7;
   - o merge da branch da etapa chegou à `main` e foi enviado (`git log origin/main`);
   - `python -m pytest` passa na `main`;
   - links dos documentos e diagramas Mermaid continuam válidos, se a etapa mexeu neles.
3. Se o portão falhar: avisar o usuário e corrigir (ou abrir um card de correção) antes de liberar a próxima.
4. Se passar: abrir o card da(s) próxima(s) etapa(s) com o prompt de `docs/PROMPTS.md`, respeitando as dependências
   da §4 e o material do jogo disponível (§6). Depois da E03, abrir em paralelo as frentes independentes.
5. Dizer ao usuário o que ele precisa ter em mãos para a etapa aberta (jogo aberto, prints etc.).

A central não edita código. Só ajusta o guia e os documentos quando o plano muda, sempre com commit e push.

**Prompt para abrir uma central nova** (se a atual ficar longa demais):

```
Você é a conversa central do OTP Bot. Leia o GUIA.md inteiro, em especial a §1.3. Não execute etapas: confira o
estado do projeto, rode o portão de qualidade da última etapa concluída e me diga qual card de etapa abrir em seguida.
```

### 1.4 Regras para não alucinar
- O que existe no código se confirma **abrindo o arquivo**, não pela memória nem por este guia.
- Números (tamanhos de região, tempos, limites) vêm da config, da especificação ou de medição. Se forem estimativa,
  dizer que são.
- Não marcar critério de aceite como cumprido sem evidência.
- Etapa que não terminou fica 🟡 com a lista do que faltou; nunca ✅.

### 1.5 Etapas em paralelo

Depois da E03, algumas etapas rodam ao mesmo tempo, cada uma na sua worktree. Regras extras para elas:

1. **Pré-requisito:** conferir as dependências da própria etapa na §4 (não "a etapa anterior da lista").
2. **Material do jogo:** se o que a etapa precisa (§6) ainda não chegou, **coletar ao vivo com o usuário**, com o jogo
   aberto, pela captura da janela do jogo (`perception/capture.GameLocator`), em vez de parar. Registrar na §6 o que foi
   coletado e onde ficou (prints em `%APPDATA%\OTPBot`, nunca no git).
3. **Um jogo para várias conversas:** só enviar tecla ou clique ao jogo com o ok do usuário **naquele momento**; outras
   etapas podem estar lendo a tela ao mesmo tempo. O bot precisa rodar **como administrador** para a entrada chegar (D20).
4. **Antes do merge:** trazer a `main` atualizada para a branch da etapa (no app, a ferramenta de sincronizar com a
   branch base; ou `git merge origin/main`), rodar os testes de novo e só então fazer o merge na `main`.
5. **Conflitos no guia:** manter as entradas das outras etapas. §0 "Etapa atual" lista as frentes que ainda estão em
   andamento (tirar só a sua); §4 muda só a linha da sua etapa; §7 recebe a sua entrada no topo, sem apagar as outras.
6. **Conflitos no código:** em arquivos compartilhados (`frontend/src/schema/features.js`, `config_manager.py`,
   `main.py`, `api_server.py`), manter as mudanças das duas etapas; na dúvida, perguntar ao usuário.

---

## 2. Documentos do projeto

| Documento | Papel | Quem atualiza |
|---|---|---|
| **`GUIA.md`** (este) | Plano, estado, etapas e passagens | Toda conversa, no fim |
| `docs/ESPECIFICACAO.md` | Regras do jogo e do bot (o "o quê") | Quando um fato ou regra muda |
| `docs/ARQUITETURA.md` | Arquitetura, decisões D1–D22, riscos (o "como") | Quando a arquitetura muda |
| `docs/PROMPTS.md` | Prompt de início de cada etapa | Quando uma etapa mudar de escopo |
| `docs/analise-bot-externo/` | Comparativo com o bot externo + 11 relatórios de vídeo | Referência; não muda |
| `ActiveContext.md` | Diário histórico das sessões | Toda conversa, uma entrada curta |
| `CLAUDE.md` | Carregado automaticamente; aponta para este guia | Só se o protocolo mudar |
| `DESIGN.md` | Diretrizes originais | Referência |
| `task.md` | Processo de trabalho (rito transversal) | Referência |
| `README.md` | Instalação e uso | Na etapa E15 e quando o uso mudar |
| `tools/analisar_playlist.py` | Script que analisou os vídeos com o Gemini | Referência |

---

## 3. Resumo do que foi decidido na E00

**Objetivo da v1.0:** fazer sozinho a hunt "tipo 1" do Poke Alliance com 1 personagem: andar pela rota, lurar, parar,
antídoto se preciso, combo, revive, **capturar só shiny**, curar com pokémon curador e seguir, pausando sozinho se
aparecer GM ou jogador. Tudo vendo a tela, sem ler memória do jogo.

**Ordem de prioridade (Q62):** visão → captura de shiny → rota por coordenadas + lure → cura validada → debuff →
aprendizado → executável.

**Arquitetura (detalhes em `docs/ARQUITETURA.md`):**
- Camadas: **Percepção → WorldState → Decisão → Atuação**.
- Decisão: prioridade fixa **Segurança > Companion > Sobrevivência > Hunt**; a Hunt é uma **máquina de fases**.
- Visão: **YOLO** (posições) + **leitor da Battle** (contagem, shiny, ícone de "longe do spawn", GM).
- Jogo no **monitor secundário**: captura pela janela do jogo e **entrada sem foco** (PostMessage), com plano B.
- Rota por **coordenadas `x, y, z`** e **teclado numérico** (Num Lock desligado), gravada **jogando**.
- Executável: **PyInstaller onedir** + **Velopack** (instalador e atualização automática), **ONNX Runtime** no núcleo,
  **kit de treino** separado com torch. Dados em `%APPDATA%\OTPBot`.
- Decisões **D1–D19 aprovadas** pelo usuário em 2026-10-09. D11 confirmada pelo spike da E01; **D20** (núcleo como
  administrador) entrou na E01.

### 3.1 Estrutura de pastas alvo

```
OTP Bot/
├─ GUIA.md · CLAUDE.md · README.md · ActiveContext.md · DESIGN.md · task.md
├─ main.py                       entrada
├─ otpbot/
│  ├─ app/          paths.py, runtime.py, updater.py
│  ├─ platform/     game_window.py, input_backend.py, dpi.py
│  ├─ perception/   capture.py, bars.py, battle.py, yolo_onnx.py, coords.py,
│  │                debuff.py, chat.py, hunt_analyzer.py, sprites.py
│  ├─ state/        world_state.py
│  ├─ brain/        arbiter.py, behaviors/ (safety, companion, survival, hunt), hunt/phases.py
│  ├─ actuation/    action_queue.py, input_lock.py, mouse.py, movement.py
│  ├─ hunts/        hunt_model.py, recorder.py
│  ├─ learning/     session_recorder.py, dataset.py, optimizer.py
│  ├─ extras/       launcher.py, overlay.py, alerts.py
│  └─ interface/    api_server.py, config_manager.py
├─ defaults/                      padrões do programa (prints de referência da calibração)
├─ trainer/                       kit de treino (processo separado)
├─ frontend/                      console React
├─ tests/
├─ tools/
├─ build/                         specs do PyInstaller e do Velopack
└─ docs/                          ESPECIFICACAO, ARQUITETURA, analise-bot-externo/
```

Módulos que **saem**: `ai/`, `core/keyboard.py`, `core/mouse.py`, `modules/vision.py`, `modules/ui_analyzer.py`
(removidos na E02) e `core/navigator.py` (rota por pixel). O navigator ficou em `otpbot/hunts/navigator.py` até a
**E09**, quando o gravador e a rota por coordenadas o substituem (decisão do usuário na E02: remover agora mudaria o
comportamento).

### 3.2 Estado do código no início (E00)

| Área | Situação |
|---|---|
| Leitura de barras por cor (HP jogador/pokémon, EXP, Pokébar, postura) | ✅ funciona |
| Calibração por resolução (3440×1440, 1920×1080) | ✅ |
| Biblioteca de sprites + template matching | ✅ |
| Console por abas (React) + API local com token | ✅ |
| Monitor de GM no chat (Tesseract) | ✅ |
| Mouse humanizado (Bézier) | ✅ |
| Combo, defesa quando cercado, captura | ⚠️ implementados, **cegos**: sem modelo YOLO |
| Cura com pokémon | ⚠️ implementada, não validada no jogo |
| Rota | ⚠️ cliques gravados em pixel; será substituída |
| Opções da rota, poção, medicine, alertas, Telegram, comida, guild | 🟡 só configuração no console |
| DPI, captura por janela, entrada sem foco, Battle, coordenadas, debuff | ❌ (E01: janela, DPI, captura e spike de entrada feitos; E03: sensores na área cliente, entrada sem foco no bot) |

---

## 4. Mapa das etapas

Cada etapa = **uma conversa**. Tamanho: **P** (horas), **M** (1–2 dias), **G** (vários dias).
📦 = precisa do material do jogo.

| Etapa | Nome | Bloco | Tam. | Depende de | Status |
|---|---|---|---|---|---|
| E00 | Análise e arquitetura | — | — | — | ✅ |
| E01 | Git, spike de entrada sem foco e janela do jogo | Fundação | M | E00 | ✅ |
| E02 | Nova estrutura de pastas, dados em %APPDATA% e limpeza | Fundação | M | E01 | ✅ |
| E03 | WorldState, árbitro, fila e trava de entrada | Fundação | G | E02 | ✅ |
| E04 | Coleta de prints e ferramenta de rotular | Visão | G | E03 📦 | ✅ |
| E05 | Treino, ONNX e visão ao vivo | Visão | G | E04 📦 | ⬜ |
| E06 | Leitor da Battle e alertas de segurança | Visão | G | E03 📦 | 🔵 |
| E07 | Captura de shiny | Captura | G | E05, E06 📦 | ⬜ |
| E08 | Coordenadas, movimento e modelo de hunt | Rota | G | E03 📦 | ✅ |
| E09 | Gravador de hunt e editor de rota | Rota | G | E08 | ⬜ |
| E10 | Fases da hunt (lure, parada, combo, revive) e Companion | Rota | G | E06, E09 | ⬜ |
| E11 | Cura e troca de pokémon validadas | Cura | M | E10 | ⬜ |
| E12 | Debuff e antídoto | Debuff | M | E10 📦 | ⬜ |
| E13 | Gravador de sessões, analisador do jogo e aba Sessão | Aprendizado | M | E10 📦 | ⬜ |
| E14 | Aprender comigo e otimizador | Aprendizado | G | E13 | ⬜ |
| E15 | Build, instalador e atualização automática | Executável | M | E03 | 🔵 |
| E16 | Launcher, auto-login e overlay | Executável | G | E15 | ⬜ |
| E17 | Validação final da v1.0 | Entrega | M | todas | ⬜ |

Ordem sugerida: E01 → E02 → E03 → (material do jogo) → E04 → E05 → E06 → E07 → E08 → E09 → E10 → E11 → E12 → E13 →
E14 → E15 → E16 → E17. A E06 e a E08 só dependem da E03 e podem vir antes da E04/E05 se o material chegar em partes. A
E15 pode ser antecipada se você quiser usar o .exe mais cedo.

Legenda de status: ⬜ não iniciada · 🔵 em andamento · 🟡 parcial · ✅ concluída.

---

## 5. Etapas em detalhe

### E01: Git, spike de entrada sem foco e janela do jogo
**Objetivo:** destravar o git e responder a maior dúvida técnica do projeto: o cliente aceita teclas e cliques com o
jogo **fora de foco**?
**Leitura obrigatória:** `docs/ARQUITETURA.md` §4 e §9 (R1); `docs/ESPECIFICACAO.md` §1.
**Pré-requisito do usuário:** ter o jogo aberto no monitor secundário em DirectX.

- [x] Git funcionando (`safe.directory` adicionado); documentos da E00 no commit `157326c`, enviado ao GitHub.
- [x] `platform/game_window.py`: achar a janela do cliente, monitor, retângulo, foco; DPI aware.
- [x] Script de spike em `tools/spike_input.py`: teclado numérico (Num Lock off), hotkeys F1–F12 e clique, via
  PostMessage com o jogo **sem foco**; registrar o que funcionou. *(Testados: numérico 8, F5 e clique esquerdo.)*
- [x] Captura **só da janela do jogo** no monitor secundário; escolher o perfil de calibração pelo tamanho da janela.
  *(Função `pick_window_profile`; o `main.py` ainda captura o monitor inteiro, ver pendências da E01 na §7.)*
- [x] Medir a área do jogo nas duas resoluções (pendência P3 da especificação).

**Aceite:** (1) commit feito; (2) relatório do spike com o veredito de D11 (segundo plano funciona? para quais
entradas?) registrado em `docs/ARQUITETURA.md`; (3) captura da janela do jogo no monitor secundário mostrada no console
ou salva em arquivo; (4) testes passando.
**Fora do escopo:** reorganizar pastas (E02), WorldState (E03).

### E02: Nova estrutura de pastas, dados em %APPDATA% e limpeza
**Objetivo:** levar o código atual para a estrutura da §3.1 **sem mudar comportamento**.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §7 e §8.3.

- [x] Criar o pacote `otpbot/` e mover os módulos atuais para as camadas (renomeando conforme a §7 da arquitetura).
  *(Renomeados só os 1:1; `vision_engine`, `decision_thread`, `heal_routine` e `action_orchestrator` mantêm o nome
  até a etapa que cria o substituto: E05, E03, E11, E03.)*
- [x] `app/paths.py`: dados em `%APPDATA%\OTPBot` (config, sprites, calibração, modelos, rota, logs); migração
  automática dos arquivos atuais (só copia, nunca apaga nem sobrescreve).
- [x] Remover os módulos sem uso e as dependências sem uso do `requirements.txt`. *(O `navigator` fica até a E09.)*
- [x] Unificar a região do chat (`features.safety.chat_roi` × calibração). *(Fonte única: região `chat` do perfil.)*
- [x] Atualizar o `README.md` (estrutura e caminhos).

**Aceite:** bot abre, console funciona, leituras de barras e sprites iguais às de antes; testes passando; nenhum
arquivo de dados dentro da pasta do código.
**Fora do escopo:** mudar lógica de decisão.

### E03: WorldState, árbitro, fila e trava de entrada
**Objetivo:** a espinha dorsal da arquitetura nova.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §3 e §4; resultado do spike da E01.

- [x] `state/world_state.py`: snapshot por tick com valor, confiança e idade de cada leitura.
- [x] Sensores atuais (barras, chat, YOLO) publicando no WorldState.
- [x] `brain/arbiter.py` com a prioridade Segurança > Companion > Sobrevivência > Hunt e interrupção com limpeza.
  *(Companion e Sobrevivência no lugar, sem regra até a E10; limpeza conforme D21.)*
- [x] `actuation/action_queue.py` (a partir do `action_orchestrator`), `input_lock.py` e `platform/input_backend.py`
  (segundo plano e primeiro plano, conforme D11). Segundo plano = o que o `tools/spike_input.py` provou (lParam com
  scan code, numérico sem o bit *extended*). Ao iniciar, checar se o bot tem a mesma integridade do jogo (D20).
- [x] Sensores capturando **só a área cliente** (`capture_client`) com regiões **relativas ao cliente**: a calibração
  atual está em coordenadas da tela em tela cheia e erra com o jogo maximizado com barra de título.
  *(Perfis `1920x1009` e `3440x1369`; jogo coberto = sem leitura, D22.)*
- [x] Portar as regras atuais (combo, defesa, postura, cura, captura) para comportamentos, sem mudar o que fazem.

**Aceite:** o comportamento atual continua igual; nenhuma ação de entrada acontece fora da trava (teste); a Segurança
interrompe uma rotina longa (teste); testes passando.
**Fora do escopo:** novas regras de hunt (E10).

### E04: Coleta de prints e ferramenta de rotular 📦
**Objetivo:** criar o dataset da visão.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §6; `docs/ESPECIFICACAO.md` §3 e §8.

- [x] Coleta: botão no console + captura automática periódica durante a hunt, nas duas resoluções.
  *(Ao vivo testado em 1920; 3440 pelos vídeos (`tools/extrair_frames_video.py`). Funciona com o bot pausado.)*
- [x] Aba **Visão/IA**: ferramenta de rotular (caixas) com as classes `meu_pokemon`, `selvagem`, `selvagem_shiny`,
  `corpo`, `corpo_shiny`.
- [x] Formato do dataset compatível com o treino YOLO; divisão treino/validação. *(Por grupo de 30 s, ARQUITETURA §6.1.)*
- [x] Rotular junto com o usuário um primeiro lote. *(46 prints, 326 caixas.)*

**Aceite:** dataset salvo em `%APPDATA%\OTPBot\dataset` com um primeiro lote rotulado; a ferramenta abre, salva e
reabre rótulos.

### E05: Treino, ONNX e visão ao vivo 📦
**Objetivo:** o bot passa a enxergar.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §2, §6, §8.1 e R2.

- [ ] `trainer/`: treino YOLO em processo separado, prioridade baixa, limite de VRAM.
- [ ] Métricas por classe; exportar `.onnx`; registro de modelos.
- [ ] `perception/yolo_onnx.py` (ONNX Runtime) no lugar do `vision_engine`; troca de modelo sem reiniciar.
- [ ] Rotulagem automática com o modelo treinado (volta para a E04 em ciclos).
- [ ] Visão ao vivo no console (print com caixas).

**Aceite:** métricas por classe registradas aqui no guia; visão ao vivo detecta selvagens e corpos na hunt real;
jogo + bot + treino rodando juntos sem travar.

### E06: Leitor da Battle e alertas de segurança 📦
**Objetivo:** contagem confiável, shiny, limite do lure e detecção de GM/jogador.
**Leitura obrigatória:** `docs/ESPECIFICACAO.md` §2.2, §3 e §7.

- [ ] `perception/battle.py`: linhas, quantidade, HP, ícone de shiny, **ícone de "longe do spawn"**, nome fora da
  espécie da hunt, linha de jogador.
- [ ] Alertas: GM e jogador na tela → **pausa + aviso + alarme sonoro** no console.
- [ ] Mostrar a leitura da Battle na "Leitura ao vivo".

**Aceite:** com prints reais, contagem certa, shiny e ícone de distância detectados; alerta disparado num teste com
nome estranho.

### E07: Captura de shiny 📦
**Leitura obrigatória:** `docs/ESPECIFICACAO.md` §3.

- [ ] Configuração: recorte do corpo-alvo e do sprite da bola (shiny e normal) com a tecla de cada.
- [ ] Fase "capturar": achar o corpo (`corpo_shiny` + cor), cursor sobre o corpo, hotkey da bola; segurar a rota.
- [ ] Confirmação pelo chat (pt/en) e corpo sumiu; até N tentativas.
- [ ] Notificar fim das bolas; alerta de shiny capturado.

**Aceite:** captura de um shiny real confirmada pela mensagem do chat; falha tenta de novo até N.

### E08: Coordenadas, movimento e modelo de hunt 📦
**Leitura obrigatória:** `docs/ESPECIFICACAO.md` §6; `docs/ARQUITETURA.md` §5.

- [x] `perception/coords.py`: `x, y, z` por dígitos-modelo. *(Modelos 0–9 e vírgula em `defaults/coords/`; sensor
  `coords` no WorldState ~10x/s, copiando só a caixinha.)*
- [x] `actuation/movement.py`: teclado numérico com Num Lock desligado, 8 direções, confirmado pela coordenada.
  *(`Mover.step` / `walk_to`, pela fila com lease; tecla engolida é repetida.)*
- [x] `hunts/hunt_model.py`: rota, alvos, bolas, **equipe com papéis**, regras; `hunts/*.json`.

**Aceite:** o bot anda de A a B por coordenadas numa área real; leitura de coordenada sem erro numa sequência de passos.

### E09: Gravador de hunt e editor de rota
- [ ] `hunts/recorder.py`: grava posições, paradas (tempo), teclas apertadas e escadas → rascunho de rota.
- [ ] Aba **Rota/Mapa**: posição atual, editor de pontos (andar, lurar, matar, escada).
- [ ] Aba **Hunt**: escolher a hunt salva e iniciar.
- [ ] Remover o cavebot por pixel (`otpbot/hunts/navigator.py`, `/api/route` antigo, F10/F11 e `route.json`),
  substituído pelo gravador (adiado da E02).

**Aceite:** gravar uma volta real e obter um rascunho coerente (pontos de matar onde o combo foi usado).

### E10: Fases da hunt e Companion
**Leitura obrigatória:** `docs/ESPECIFICACAO.md` §2 inteiro e §7.

- [ ] `brain/hunt/phases.py`: andar, lurar (defensivo, buff com 5+), critério de parada (N, ponto de matar com N mín.,
  ícone de distância), combo (ofensivo), revive, sobras ficam para a próxima volta.
- [ ] Perdido → para e avisa.
- [ ] Pokémon desmaiou → revive e continua.
- [ ] **Companion**: sua entrada no jogo pausa; retomar pelo console.

**Aceite:** uma volta completa da hunt sem intervenção; Companion pausa e retoma.

### E11: Cura e troca de pokémon validadas
- [ ] Portar o `heal_routine` para a fase "curar": HP vermelho < 90%, box morta, área limpa; troca por hotkey.
- [ ] Curador e pokémon de dano apontados no console.
- [ ] Validação no jogo de ponta a ponta.

**Aceite:** cura real feita e o pokémon de dano de volta, com a hunt continuando.

### E12: Debuff e antídoto 📦
- [ ] Nova região de calibração sob a barra de skills do pokémon; `perception/debuff.py`.
- [ ] Fase "antídoto" antes do combo; esperar o debuff sair e a recarga, se preciso.

**Aceite:** com debuff real, o bot usa o antídoto e só comba depois que o ícone some.

### E13: Gravador de sessões, analisador do jogo e aba Sessão 📦
- [ ] `learning/session_recorder.py`: estado + ação + resultado.
- [ ] `perception/hunt_analyzer.py`: saldo do analisador do jogo.
- [ ] Aba **Sessão**: mortos, bolas, dinheiro +/−, itens usados, EXP/h.

**Aceite:** uma sessão real gravada e os números da aba batendo com o analisador do jogo.

### E14: Aprender comigo e otimizador
**Leitura obrigatória:** `docs/ESPECIFICACAO.md` §8.

- [ ] "Aprender comigo": a partir das sessões, aprender quando você para, comba e cura.
- [ ] Otimizador dentro dos limites duros; aba **Aprender** com sugestões para aceitar/recusar.

**Aceite:** sugestões geradas a partir de sessões reais; nenhuma sugestão viola os limites.

### E15: Build, instalador e atualização automática
**Leitura obrigatória:** `docs/ARQUITETURA.md` §8.

- [ ] PyInstaller onedir do núcleo e do kit de treino; console compilado; Tesseract e ONNX Runtime embutidos.
- [ ] Velopack: instalador + atualização a partir de GitHub Releases privado (D9).
- [ ] Teste no PC leve (só núcleo).

**Aceite:** instalar, abrir, atualizar para uma versão nova sem perder dados.

### E16: Launcher, auto-login e overlay
- [ ] Aba **Contas**: abrir o jogo, escolher DirectX, escolher a conta.
- [ ] Auto-login: credenciais no Gerenciador de Credenciais do Windows; conta secundária, depois a principal, depois
  a hunt.
- [ ] Overlay sobre o jogo (caixas e status).

**Aceite:** do zero até a hunt rodando, só com cliques no console; nenhuma senha em arquivo ou log.

### E17: Validação final da v1.0
- [ ] Hunt completa de 1 hora sem intervenção, com captura de shiny, cura, debuff e alertas.
- [ ] Revisão do `README.md`, `docs/` e deste guia; versão 1.0 publicada.

**Aceite:** sessão de 1 hora gravada, com os números na aba Sessão e zero mortes.

---

## 6. Material do jogo (pendente)

Necessário a partir da **E04**. Pode chegar em partes; registrar aqui o que chegou e onde foi salvo.

| Item | Para qual etapa | Recebido? |
|---|---|---|
| 10–20 prints de hunt com lure cheio, em 1920×1080 **e** 3440×1440 | E04, E05 | ✅ E04: dataset em `%APPDATA%\OTPBot\dataset` (fora do git): 46 prints rotulados (36 treino / 10 validação; 31 de 3440 e 13 de 1920 tirados dos vídeos + 2 ao vivo de 1920), 326 caixas (meu_pokemon 45, selvagem 190, selvagem_shiny 28, corpo 63, corpo_shiny 0); 304 frames descartados pelo usuário (repetidos); 5 prints ao vivo de 1920 (hunt de Seviper) ainda para rotular. Hunts vistas: Swellow, Girafarig, Bastiodon (3440 e 1920), Seviper |
| Shiny vivo ao lado de normal; corpo de shiny ao lado de corpo normal | E05, E07 | 🟡 E04: 28 selvagens shiny rotulados nos vídeos; **nenhum corpo de shiny** ainda |
| Battle list cheia (com shiny e com o ícone de "longe do spawn") | E06 | ⬜ |
| Minimapa com as coordenadas visíveis | E08 | ✅ E08: 3 prints da E01 já no git (`docs/e01/`: `433, 1501, 7`, `2690, 4170, 2`, `457, 1457, 7`) + o 8 coletado ao vivo (`1713, 4158, 7`). Modelos dos dígitos em `defaults/coords/`; prints ao vivo em `%APPDATA%\OTPBot\e08` |
| Pokémon com debuff ativo e o mesmo sem debuff | E12 | ⬜ |
| Hotbar e bag com poções, antídotos, revives e bolas | E07, E11 | ⬜ |
| Mensagens do chat de captura com sucesso e com falha | E07 | ⬜ |
| Analisador de hunt do jogo aberto | E13 | ⬜ |
| Tabela de itens da Q26 (nome, como usa, tecla) | E07, E11 | ⬜ |
| Vídeo de 5–10 min fazendo a hunt na mão | E04, E09, E14 | 🟡 E03: 2 vídeos em 3440 (~5,9 min e ~2,6 min) em `C:\Users\Gabe\Videos\Captures` (fora do git). Gravados da janela: 2560×1020 = área cliente 3440×1369 reduzida ×0,744 (ampliar de volta antes de medir). Faltam vídeos em 1920 · **E04:** + `!!! ALERTA_ Recebi PM !!! 2026-10-10 08-11-46.mp4` (**1920×1012**, 4,6 min, hunt de Bastiodon; o nome é o título da janela na hora) e `Service 2026-10-10 15-25-19.mp4` (3440 em 2560×1020, 4,6 min, hunt de Girafarig), na mesma pasta. Frames dos 4 vídeos extraídos a cada 3 s para o dataset |

---

## 7. Registro de passagem

Uma entrada por conversa, da mais recente para a mais antiga. Modelo:

```
### Exx: nome (AAAA-MM-DD)
- Feito:
- Critérios de aceite: (cada um com a evidência)
- Decisões novas / mudanças na arquitetura:
- Fatos novos do jogo (registrados na especificação):
- Pendências e desvios:
- Próxima etapa e o que o usuário precisa providenciar:
```

### E04: Coleta de prints e ferramenta de rotular (2026-10-10)
- **Feito:** `otpbot/learning/dataset.py`: as 5 classes fixas; dataset em `%APPDATA%\OTPBot\dataset` com
  `pending/`, `images|labels/{train,val}`, `data.yaml` e `manifest.json`; só o recorte da `game_area`; divisão por grupo
  de 30 s; relê o manifest se outro processo gravou e recupera PNG órfão; `AutoCollector` pula repetidos.
  `otpbot/interface/dataset_api.py`: rotas `/api/dataset/*` num APIRouter, com uma linha no `api_server`.
  `tools/extrair_frames_video.py`: frame a cada N s, amplia o 3440 gravado em 2560 e não duplica ao rodar de novo.
  Aba **Visão/IA** (`VisionTab.jsx`): coletar (botão + automático), lista, caixas (desenhar, mover, cantos, 1–5,
  Del, ←/→ salvando, C cola), descartar e contadores. README e ARQUITETURA §6.1 e §7 atualizados.
- **Critérios de aceite:**
  1. Dataset em `%APPDATA%\OTPBot\dataset` com um primeiro lote rotulado: **46 prints, 326 caixas**, rotulados pelo
     usuário na ferramenta (36 treino / 10 validação; contagem por classe na §6). Conferi as caixas desenhadas em
     8 prints.
  2. A ferramenta abre, salva e reabre rótulos: `test_salvar_e_reabrir_rotulos` (instância nova lê do disco) e
     `test_rotas_do_dataset`. No uso real, o usuário corrigiu os 46 pela lista "Rotuladas" depois de dois reinícios
     do bot.
  3. Coleta: botão testado ao vivo (`live_20261010-085831_105`, perfil `1920x1009`, 1124×588); captura automática ao
     vivo com o jogo visível = 5 prints em 20 s; com o jogo coberto, nenhum print e o motivo na tela. 3440 coletado
     pelos vídeos (recortes conferidos: área do jogo em (552, 4) e (398, 133), batendo com os perfis).
  4. Testes: antes **87 passed** (E03); E04 sozinha **106 passed**; depois do merge com a `main` (E08) **145 passed**.
- **Decisões novas / mudanças na arquitetura:** sem D nova. Do usuário: imagem = recorte da `game_area`;
  `meu_pokemon` = só o pokémon fora da bola; caixa justa no sprite, com o nome dentro só quando ele fica por cima.
  Minhas: grupo de 30 s (60 s deixava 45/1); rotas da Visão num APIRouter à parte.
- **Fatos novos do jogo (registrados na especificação §3):** corpo = deitado, sem nome e sem barra; caveira = selvagem
  mais forte; nome com ícone acima do personagem = guild; "Mark" = NPC; mensagem de falha da bola (pt): "Desculpe, sua
  Poké Bola quebrou."; regra de rótulo.
- **Pendências e desvios:**
  - **`corpo_shiny` com 0 exemplos:** o treino da E05 não vai aprender essa classe sem prints de corpo de shiny (§6).
  - 5 prints ao vivo (hunt de Seviper, 1920) estão em "Para rotular". O usuário descartou 304 frames repetidos (ficam
    no manifest como descartados; a extração não traz de volta).
  - Captura ao vivo em 3440 não testada (o jogo estava em 1920); o recorte é o mesmo código, com o perfil `3440x1369`.
  - No layout de 3440 a hotbar e a EXP ficam por cima da faixa de baixo da área do jogo e entram no recorte. O vídeo
    `15-25-19` tem uma faixa escura fina na direita e embaixo.
  - Um print foi salvo como "sem nada" por um arraste meu no teste; desfiz (voltou para a fila) e o usuário rotulou.
  - Bug achado no uso: com o console aberto, a extração de vídeo gravava o manifest por fora e o próximo salvar o
    sobrescreveria. Corrigido (releitura + recuperação) antes de qualquer perda.
  - A ferramenta de sincronizar do app recusou porque o `origin` não está fixado no app; fiz `git merge origin/main`.
- **Próxima etapa:** **E05** (treino, ONNX e visão ao vivo), liberada. O usuário precisa ter prints de **shiny vivo
  e corpo de shiny**, e seguir rotulando (os 5 de Seviper + mais frames). E06 e E15 continuam em paralelo; E09
  liberada.

### E08: Coordenadas, movimento e modelo de hunt (2026-10-10)
- **Feito:** `perception/coords.py` (recorte da caixinha "x, y, z" do minimapa → pixels claros → caracteres separados
  por coluna vazia → Jaccard contra os modelos de `defaults/coords/`, nota ≥ 0,92 **e** folga ≥ 0,08 sobre o 2º;
  confiança = pior caractere; formato errado ou caractere desconhecido = `None`); sensor `coords_monitor` publicando
  `coords` no WorldState ~10x/s (copia **só a caixinha**: `capture_client`/`GameLocator.capture` ganharam `region`) e
  em `/api/status.coords`; região `coords` dos perfis `1920x1009` e `3440x1369` medida de novo (largura − 386, y 31,
  88×18); `actuation/movement.py` (`Mover.step`: lê, aperta pela fila com o lease, espera leitura nova e confere o sqm
  exato → ok / bloqueado / fora / sem_leitura / recusado; sem mudança em 0,4 s **aperta de novo**; `walk_to`: diagonal
  enquanto faltar x e y, se bloquear tenta as 2 vizinhas, `perdido` com outro andar, destino > 30 sqm, desvio para
  longe ou 3 rodadas sem avançar); `hunts/hunt_model.py` (rota com `walk`/`lure`/`kill`/`stairs` + espera, alvos,
  bolas shiny/normal, **equipe com papéis** `damage`/`healer`/`lure`/`damage2` com a v1 aceitando só 1 dano e até 1
  curador, regras com os padrões da especificação, JSON versionado em `%APPDATA%\OTPBot\hunts`, validação com
  mensagens em português, gravação atômica); `paths.hunts_dir()`; ferramentas `tools/coord_glyphs.py` (lê e cria
  modelos, só tela) e `tools/move_test.py` (read / step / walk pela pilha real, checa D20).
- **Critérios de aceite:**
  1. **Anda de A a B por coordenadas numa área real** (bot como administrador, PostMessage, jogo sem foco, print do
     usuário): `837, 1584 → 848, 1600` (16 teclas, chegou), `848, 1600 → 852, 1596` (4, chegou),
     `852, 1596 → 848, 1600` (6, chegou; 1 diagonal bloqueada e desvio por ↓). Antes, um passo em cada uma das 8
     direções: 8/8 ok, voltando ao sqm inicial.
  2. **Leitura sem erro numa sequência de passos:** nos 26 passos do aceite e nos 8 do teste de direções, toda
     coordenada lida depois da tecla era exatamente o sqm esperado (nenhum "fora"). Só leitura: 68 + 83 + 70 leituras
     seguidas sem falha. Os 3 prints reais da E01 leem certo com confiança 1,00 (`tests/test_coords.py`).
  3. Testes: antes **87 passed**; depois **126 passed** (coordenadas 14, movimento 15, hunt 9, captura por região 1).
- **Decisões novas / mudanças na arquitetura:** nenhuma D nova. `coords` entrou no WorldState (idade máx. 1 s).
- **Fatos novos do jogo (registrados na especificação):** formato `x, y, z` (texto branco com contorno preto) numa
  caixinha no canto do minimapa, **no mesmo lugar e com os mesmos pixels em 1920 e 3440**; 8 (↑) diminui o y e 6 (→)
  aumenta o x; a coordenada muda 0,20–0,28 s depois da tecla; **o jogo ignora a tecla que chega logo depois de um passo**
  (fim da animação): repetida 0,4 s depois, passa (passos de 0,55–0,66 s).
- **Pendências e desvios:**
  - **Bot como administrador não achou o `config.json`:** no terminal elevado do usuário o `ConfigManager` disse
    "config.json não encontrado" em `C:\Users\Gabe\AppData\Roaming\OTPBot`, e o terminal da IA vê o arquivo no mesmo
    caminho (o terminal da IA parece ver uma cópia isolada do %APPDATA%; os logs gravados pelo terminal elevado não
    aparecem para ela). Para o teste não importou (calibração padrão). **Conferir antes de rodar o bot de verdade como
    administrador** (E10/E15).
  - Durante os testes, outro bot estava rodando e movia o personagem (o usuário pausou). Na mesma máquina havia um
    `main.py --port 8044` de outra conversa. Ao testar movimento, conferir antes que o personagem está parado.
  - Se a janela do jogo fica coberta (ex.: a ferramenta de print no meio do teste), o movimento para com `sem_leitura`
    (D22). Tirar o print só depois.
  - A diagonal `850, 1598 → 849, 1599` foi bloqueada no último trecho, embora o sqm tenha sido usado no trecho
    anterior; causa não confirmada (pokémon/criatura no sqm, ou regra de diagonal do jogo).
  - Tempos (`step_timeout` 1,5 s, `repress_s` 0,4 s) medidos só em 1920 e no chão; escada (mudar o `z`) e contorno de
    obstáculo pelo minimapa não existem (`walk_to` só no mesmo andar). O `Mover` ainda não está ligado à Hunt (E10).
  - Leitura de coordenada ao vivo testada só em 1920; o 3440 foi conferido pelo print da E01.
- **Próxima etapa:** E09 (gravador de hunt e editor de rota), que depende só da E08; E04, E06 e E15 seguem em
  paralelo. Para a E09 o usuário precisa do jogo aberto para gravar uma volta real da hunt, com o outro bot desligado.

### E03: WorldState, árbitro, fila e trava de entrada (2026-10-10)
- **Feito:** `state/world_state.py` (leitura = valor + confiança + horário; vencida/incerta = `None`); sensores
  publicando (`detections` + `window` do YOLO, `bars`, `gm_alert` do chat, que não desliga mais o bot sozinho);
  `brain/arbiter.py` + `brain/behaviors/` (`safety`, `companion` e `survival` vazios até a E10, `hunt` com as regras da
  antiga `decision_thread` copiadas na mesma ordem); `actuation/action_queue.py` (cooldowns do orchestrator + envio FIFO
  que confere a trava antes de cada tecla/clique), `actuation/input_lock.py`, `platform/input_backend.py` (background =
  PostMessage do spike, padrão; foreground = foca + SendInput + Bézier; `config.input.backend`; numérico com e sem Num
  Lock, setas com bit *extended*, modificadores); checagem D20 ao achar a janela (log + `/api/status.integrity`);
  `perception/capture.GameLocator` (só a área cliente; `None` com o jogo fechado, minimizado ou **coberto**, D22);
  perfis `1920x1009` e `3440x1369` medidos; prints do console (sprites, calibração) também pela área cliente; cura,
  navigator e botões de teste passando pela fila com lease; removidos `decision_thread.py` e `action_orchestrator.py`;
  README e ARQUITETURA (§3.1, §7, D21, D22) atualizados.
- **Critérios de aceite:**
  1. Comportamento igual: os 11 testes da antiga `decision_thread` foram portados para `tests/test_hunt_behavior.py`
     com **as mesmas expectativas** (teclas, ordem, ponto da postura (166, 118)) e agora rodam pela pilha inteira
     (WorldState → árbitro → Hunt → fila → trava → backend gravador); `test_heal_routine.py` sem mudança. Leituras ao
     vivo com o bot rodando (`python main.py --no-window`, pausado): perfil `1920x1009`, HP 100, pokémon 100, EXP
     92,6, Pokébar [97,6, 99,2, 74,4, 99,2, 99,2], postura ofensiva, batendo com o print. **Nenhuma tecla foi enviada
     ao jogo nesta conversa** (combo e captura seguem cegos sem modelo YOLO).
  2. Nada fora da trava: `tests/test_input_guard.py`: varredura AST de `otpbot/` + `main.py` (só o
     `input_backend.py` chama PostMessage/SendInput/keyboard.send/pydirectinput…) + cenários reais com todo envio com
     dono válido + trava revogada = nada chega ao backend.
  3. Segurança interrompe rotina longa: `test_arbiter.py::test_seguranca_interrompe_a_cura_no_meio_sem_limpeza`
     (a cura chama o curador, o GM aparece, o bot desliga e a volta ao farm é barrada). Teste de mutação: tirar a
     revogação da trava faz esse teste falhar. Também testado: outro comportamento interrompe e a cura volta ao farm
     antes da troca de dono; pausa corta a entrada; teste do console passa pela trava.
  4. Testes: antes **47 passed**; depois **87 passed**.
- **Decisões novas / mudanças na arquitetura:** **D21** (limpeza na interrupção; a Segurança não permite, aprovada
  pelo usuário); **D22** (jogo coberto = sem leitura; aplicada, **falta o ok do usuário**). Backend padrão =
  background (D11).
- **Fatos novos do jogo (registrados na especificação):** na área cliente os painéis da esquerda ficam nas mesmas
  coordenadas nas duas resoluções; o painel de baixo e a Battle mudam de altura com o layout (área do jogo em y 142 →
  133 e EXP 816 → 798 no mesmo 1920).
- **Pendências e desvios:**
  - **Rodar o bot como administrador:** sem isso o D20 avisa e toda entrada é bloqueada pelo Windows (o teste ao vivo
    desta conversa rodou sem admin e o aviso apareceu: "bot média, jogo alta").
  - Não testado no jogo: entrada pelo bot novo (só o spike da E01), teclas com modificador (`ctrl+f1`) sem foco, o
    backend foreground, as outras teclas do numérico/F.
  - Mudanças pequenas de comportamento, todas por causa da trava: pausar no meio da cura **corta** a rotina (antes ela
    terminava); com o bot **pausado** o cavebot (F11) não clica mais (antes clicava); sem o jogo visível nada é lido
    nem enviado (antes lia o monitor principal e mandava tecla para a janela em foco); barras com mais de 3 s não
    valem.
  - O perfil `3440x1369` foi medido no print da E01 e conferido em frames dos vídeos (reduzidos e ampliados); falta
    conferir ao vivo em 3440. A Pokébar lê uns 4–6 pontos abaixo do número do jogo (82% → 75–79%), igual ao de
    antes. O painel de baixo depende do layout: conferir na Calibração depois de mexer na interface.
  - Na primeira análise eu disse que o perfil de tela cheia "errava" no 3440 (pokémon 61,9%); nos vídeos o pokémon
    realmente estava baixo, então isso não era prova de erro.
  - `platform/dpi.py` não foi criado (o DPI aware continua no `game_window`); `scratch/test_decision_thread.py`
    continua quebrado e fora do pytest.
- **Próxima etapa:** E04 (e, em paralelo, E06/E08/E15). Para a E04 o usuário precisa dos prints de hunt com lure
  cheio nas duas resoluções (§6); os vídeos em 3440 já servem para extrair frames.

### E02: Nova estrutura de pastas, dados em %APPDATA% e limpeza (2026-10-10)
- **Feito:** `core/` e `modules/` movidos para `otpbot/{app,interface,perception,brain,actuation,hunts}` com `git mv`
  (mapa de/para em `docs/ARQUITETURA.md` §7); `otpbot/app/paths.py` (dados em `%APPDATA%\OTPBot`, `OTPBOT_DATA_DIR`
  para trocar, migração que só copia e nunca sobrescreve nem apaga); prints de referência padrão em
  `defaults/calibration/`; `config.json` e `assets/sprites/sprites.json` fora do git (e no `.gitignore`); log em
  arquivo (`logs/otpbot.log`); `model_path` relativo vale a partir da pasta de dados; monitor de GM lê a região `chat`
  da calibração (OCR em bloco, `--psm 6`) e `features.safety.chat_roi` saiu do config e da aba Segurança; removidos
  `ai/`, `core/keyboard.py`, `core/mouse.py`, `modules/vision.py`, `modules/ui_analyzer.py` (+ `test_fuzzy.py` e
  `test_e2e_emulation.py`, que só testavam o `ai/`) e as dependências `scikit-fuzzy`, `scikit-learn`, `bezier`,
  `py_trees`; 10 testes novos (`test_paths.py`, `test_chat.py`, `conftest.py` isola a pasta de dados); README atualizado.
- **Critérios de aceite:**
  1. Bot abre e console funciona: `python main.py --no-window` na `main` com os dados reais → "Dados em
     C:\Users\Gabe\AppData\Roaming\OTPBot", `GET /` = 200 com o console compilado (`npm run build` refeito),
     `/api/status`, `/api/config`, `/api/sprites`, `/api/route` e `/api/calibration/test` respondendo; bot abre
     pausado. A janela pywebview não foi aberta nesta conversa.
  2. Leituras de barras iguais: `read_regions` do código antigo (`git show HEAD:modules/screen_calibration.py`) e do
     novo dão resultado **idêntico** nas duas imagens de referência (1920: HP 100, pokémon 96,1, EXP 93,8, time
     [95,2, 100, 100, 100], postura ofensiva). Sprites: código igual, nenhum sprite salvo ainda; testes de sprites
     passando. **Conferência ao vivo com o jogo aberto fica com o usuário.**
  3. Testes: antes **41 passed**; depois **47 passed** (41 − 4 do `ai/` + 10 novos), na worktree e na `main`.
  4. Nenhum arquivo de dados na pasta do código: migração real da pasta principal para `%APPDATA%\OTPBot` conferida
     por hash (config.json, sprites.json, 2 prints de referência: todos iguais) **antes** do merge, que tirou o
     `config.json` e o `sprites.json` versionados. Na pasta do código sobraram só pastas vazias (`assets/`, `logs/`,
     `models/`).
- **Decisões novas / mudanças na arquitetura:** sem D nova. Por decisão do usuário: o `navigator` (rota por pixel)
  fica em `otpbot/hunts/navigator.py` até a **E09** (item novo na §5); a região do chat tem fonte única na calibração.
  Módulos cujo nome novo pertence a outra etapa mantiveram o nome (`vision_engine`, `decision_thread`,
  `heal_routine`, `action_orchestrator`).
- **Fatos novos do jogo:** nenhum.
- **Pendências e desvios:**
  - A região `chat` da calibração pega 2–3 linhas; o OCR passou de linha única (`psm 7`) para bloco (`psm 6`). Validar
    com o Tesseract instalado e uma mensagem de GM de teste (o Tesseract não está instalado neste PC: o monitor de GM
    fica desligado na sessão).
  - `reference_3440x1440.png` não tem 3440 de largura e é lida com o perfil 1920 (igual antes da E02; não mexido).
  - `scratch/` versionado tem um `test_decision_thread.py` quebrado (importa `DecisionThread`, que não existe).
  - `platform/dpi.py` e `app/updater.py` não foram criados (E03/E15).
  - Pastas vazias `assets/`, `logs/` e `models/` na pasta principal podem ser apagadas à mão.
- **Próxima etapa:** E03. O usuário precisa ter o jogo aberto (para conferir que as leituras ao vivo não mudaram e
  para os sensores com `capture_client`).

### E01: Git, spike de entrada sem foco e janela do jogo (2026-10-09)
- **Feito:** `otpbot/platform/game_window.py` (janela pela classe `PokeAllianceV3`, monitor, retângulo do cliente,
  foco, DPI aware, `capture_client`, `pick_window_profile`, `save_png`); `tools/spike_input.py` (uma entrada por
  execução: tecla ou clique, por PostMessage/SendMessage/primeiro plano, print antes e depois); 7 testes em
  `tests/test_game_window.py`; medição da área do jogo nas duas resoluções.
- **Critérios de aceite:**
  1. Commit feito: commit `feat(e01)` desta etapa, levado para a `main`.
  2. Veredito da D11 em `docs/ARQUITETURA.md` §4.1: PostMessage **funciona** sem foco para numérico 8 (3/3), F5
     (2/2 com o pokémon na bola) e clique esquerdo (1/1), **com o bot como administrador**. Evidência: confirmação do
     usuário + montagens em `docs/e01/spike/*_lado_a_lado.png`.
  3. Captura só da janela do jogo **no monitor secundário**: `docs/e01/captura_1920_monitor_secundario.png`
     (DISPLAY2, cliente em x = −1920); também `captura_1920_janela.png` e `captura_3440_janela.png` no principal.
  4. Testes: `python -m pytest` → **41 passed**.
- **Decisões novas / mudanças na arquitetura:** **D20** (núcleo como administrador; revisa a D10). D11 confirmada.
- **Fatos novos do jogo (registrados na especificação):** classe da janela `PokeAllianceV3` (título `Service` e
  processo `AudioEngine.exe`, disfarçados); o jogo roda como administrador; janela maximizada com barra de título;
  área do jogo **1124×588** (1920) e **2336×1224** (3440), escala ~2,08× (os sprites mudam de tamanho); F5 na
  hotbar do usuário chama o pokémon selecionado. P3 e P5 resolvidas.
- **Pendências e desvios:**
  - Não testados: as outras teclas do numérico, F1–F4 e F6–F12, clique direito, plano B. 1 das F5 com o pokémon na
    bola não teve efeito visível (causa não confirmada).
  - Não testado se o jogo abre **sem** administrador quando não há bot externo injetado.
  - `PrintWindow` dá imagem preta: a captura exige o jogo **visível** (sem janela por cima).
  - A calibração (`modules/screen_calibration.py`) está em coordenadas da tela em tela cheia; com a janela maximizada
    o cliente começa em y = 23 e a área do jogo em y = 142 (não 138). O `main.py` continua capturando o monitor
    inteiro. Fica para a E03 (sensores com `capture_client` e regiões relativas ao cliente), anotado na §5.
  - Bug corrigido: `cv2.imwrite` falha calado em caminho com acento → `save_png` (imencode + tofile).
- **Próxima etapa:** E02. O usuário precisa ter o jogo aberto (para conferir que as leituras de barras não mudaram).

### E00: Análise e arquitetura (2026-10-09)
- **Feito:** análise da playlist do bot externo (11 vídeos via Gemini, `tools/analisar_playlist.py`); comparativo com
  o código (`docs/analise-bot-externo/00-comparativo.md`); anamnese respondida pelo usuário e convertida em
  `docs/ESPECIFICACAO.md`; arquitetura v2 com 11 diagramas validados (`docs/ARQUITETURA.md`); este guia com 17 etapas.
- **Decisões:** D1–D19 aprovadas; D11 (entrada sem foco) depende do spike da E01.
- **Removido do escopo:** combo sequencial, Stun, mira em alvo único, rota por *Map Marks*/clique no minimapa, poção,
  itens por tempo, pausas aleatórias, compra de itens, loot, respostas automáticas (motivos na §8).
- **Git:** liberado (`safe.directory`); commit `157326c` enviado para `origin/main`.
- **Pendências:** material do jogo (§6); P2–P6 da especificação.
- **Próxima etapa:** E01. O usuário precisa ter o jogo aberto no monitor secundário, em DirectX.

---

## 8. Fora da v1.0

**Fica para a v2.0:** segundo tipo de hunt [Q8]; endgame com 6 pokémons em revezamento de lure e dano [Q63] (a
equipe com papéis já nasce na E08); vários personagens; Telegram.

**Removido pelas respostas da anamnese:**

| Item | Por quê |
|---|---|
| Combo sequencial (até 6 teclas) | O combo é uma tecla, o auto combo do jogo [Q12] |
| Tecla Stun, finalizar sobras, mira em alvo único | O controle de grupo é a última skill do combo; sobras morrem na próxima volta [Q13] |
| Rota por *Map Marks* ou clique no minimapa | Movimento pelo teclado numérico com coordenadas [Q43] |
| Poção, itens por tempo, comida | Não há cura por item; a cura passiva é manual [Q36] |
| Pausas aleatórias, limite de sessão | O usuário pausa na mão [Q56] |
| Compra e reposição de itens | Não precisa [Q29] |
| Loot | O servidor coleta sozinho [Q25] |
| Respostas automáticas a jogadores/GMs | Fora do escopo: servem para enganar a moderação |
