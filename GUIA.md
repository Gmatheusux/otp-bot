# GUIA DO PROJETO: OTP Bot v1.0

> **Este é o documento-mestre do projeto.** Toda conversa de desenvolvimento começa lendo este guia e termina
> atualizando-o. Se algo aqui contradiz a memória de uma conversa, **vale o que está aqui e no código**.

"OTP" = **OT Pokémon** (Poke Alliance / Poketibia). Sem relação com One Time Password.

---

## 0. Estado atual

| Campo | Valor |
|---|---|
| **Etapa atual** | **E02: Nova estrutura de pastas, dados em %APPDATA% e limpeza** |
| Última etapa concluída | E01: Git, spike de entrada sem foco e janela do jogo (2026-10-09) |
| Bloqueios | Material do jogo pendente (necessário a partir da E04) |
| Git | ✅ liberado em 2026-10-09; remoto `origin` = github.com/Gmatheusux/otp-bot (branch `main`) |
| Material do jogo recebido | ❌ nenhum ainda (ver §6) |
| Última atualização | 2026-10-09, conversa E01 |

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

### 1.3 Regras para não alucinar
- O que existe no código se confirma **abrindo o arquivo**, não pela memória nem por este guia.
- Números (tamanhos de região, tempos, limites) vêm da config, da especificação ou de medição. Se forem estimativa,
  dizer que são.
- Não marcar critério de aceite como cumprido sem evidência.
- Etapa que não terminou fica 🟡 com a lista do que faltou; nunca ✅.

---

## 2. Documentos do projeto

| Documento | Papel | Quem atualiza |
|---|---|---|
| **`GUIA.md`** (este) | Plano, estado, etapas e passagens | Toda conversa, no fim |
| `docs/ESPECIFICACAO.md` | Regras do jogo e do bot (o "o quê") | Quando um fato ou regra muda |
| `docs/ARQUITETURA.md` | Arquitetura, decisões D1–D19, riscos (o "como") | Quando a arquitetura muda |
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
├─ trainer/                       kit de treino (processo separado)
├─ frontend/                      console React
├─ tests/
├─ tools/
├─ build/                         specs do PyInstaller e do Velopack
└─ docs/                          ESPECIFICACAO, ARQUITETURA, analise-bot-externo/
```

Módulos que **saem**: `ai/`, `core/keyboard.py`, `core/mouse.py`, `modules/vision.py`, `modules/ui_analyzer.py`,
`core/navigator.py` (rota por pixel).

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
| DPI, captura por janela, entrada sem foco, Battle, coordenadas, debuff | ❌ (E01: janela, DPI, captura e spike de entrada feitos) |

---

## 4. Mapa das etapas

Cada etapa = **uma conversa**. Tamanho: **P** (horas), **M** (1–2 dias), **G** (vários dias).
📦 = precisa do material do jogo.

| Etapa | Nome | Bloco | Tam. | Depende de | Status |
|---|---|---|---|---|---|
| E00 | Análise e arquitetura | — | — | — | ✅ |
| E01 | Git, spike de entrada sem foco e janela do jogo | Fundação | M | E00 | ✅ |
| E02 | Nova estrutura de pastas, dados em %APPDATA% e limpeza | Fundação | M | E01 | ⬜ **próxima** |
| E03 | WorldState, árbitro, fila e trava de entrada | Fundação | G | E02 | ⬜ |
| E04 | Coleta de prints e ferramenta de rotular | Visão | G | E03 📦 | ⬜ |
| E05 | Treino, ONNX e visão ao vivo | Visão | G | E04 📦 | ⬜ |
| E06 | Leitor da Battle e alertas de segurança | Visão | G | E03 📦 | ⬜ |
| E07 | Captura de shiny | Captura | G | E05, E06 📦 | ⬜ |
| E08 | Coordenadas, movimento e modelo de hunt | Rota | G | E03 📦 | ⬜ |
| E09 | Gravador de hunt e editor de rota | Rota | G | E08 | ⬜ |
| E10 | Fases da hunt (lure, parada, combo, revive) e Companion | Rota | G | E06, E09 | ⬜ |
| E11 | Cura e troca de pokémon validadas | Cura | M | E10 | ⬜ |
| E12 | Debuff e antídoto | Debuff | M | E10 📦 | ⬜ |
| E13 | Gravador de sessões, analisador do jogo e aba Sessão | Aprendizado | M | E10 📦 | ⬜ |
| E14 | Aprender comigo e otimizador | Aprendizado | G | E13 | ⬜ |
| E15 | Build, instalador e atualização automática | Executável | M | E03 | ⬜ |
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

- [ ] Criar o pacote `otpbot/` e mover os módulos atuais para as camadas (renomeando conforme a §7 da arquitetura).
- [ ] `app/paths.py`: dados em `%APPDATA%\OTPBot` (config, sprites, calibração, logs); migração automática dos
  arquivos atuais.
- [ ] Remover os módulos sem uso e as dependências sem uso do `requirements.txt`.
- [ ] Unificar a região do chat (`features.safety.chat_roi` × calibração).
- [ ] Atualizar o `README.md` (estrutura e caminhos).

**Aceite:** bot abre, console funciona, leituras de barras e sprites iguais às de antes; testes passando; nenhum
arquivo de dados dentro da pasta do código.
**Fora do escopo:** mudar lógica de decisão.

### E03: WorldState, árbitro, fila e trava de entrada
**Objetivo:** a espinha dorsal da arquitetura nova.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §3 e §4; resultado do spike da E01.

- [ ] `state/world_state.py`: snapshot por tick com valor, confiança e idade de cada leitura.
- [ ] Sensores atuais (barras, chat, YOLO) publicando no WorldState.
- [ ] `brain/arbiter.py` com a prioridade Segurança > Companion > Sobrevivência > Hunt e interrupção com limpeza.
- [ ] `actuation/action_queue.py` (a partir do `action_orchestrator`), `input_lock.py` e `platform/input_backend.py`
  (segundo plano e primeiro plano, conforme D11). Segundo plano = o que o `tools/spike_input.py` provou (lParam com
  scan code, numérico sem o bit *extended*). Ao iniciar, checar se o bot tem a mesma integridade do jogo (D20).
- [ ] Sensores capturando **só a área cliente** (`capture_client`) com regiões **relativas ao cliente**: a calibração
  atual está em coordenadas da tela em tela cheia e erra com o jogo maximizado com barra de título.
- [ ] Portar as regras atuais (combo, defesa, postura, cura, captura) para comportamentos, sem mudar o que fazem.

**Aceite:** o comportamento atual continua igual; nenhuma ação de entrada acontece fora da trava (teste); a Segurança
interrompe uma rotina longa (teste); testes passando.
**Fora do escopo:** novas regras de hunt (E10).

### E04: Coleta de prints e ferramenta de rotular 📦
**Objetivo:** criar o dataset da visão.
**Leitura obrigatória:** `docs/ARQUITETURA.md` §6; `docs/ESPECIFICACAO.md` §3 e §8.

- [ ] Coleta: botão no console + captura automática periódica durante a hunt, nas duas resoluções.
- [ ] Aba **Visão/IA**: ferramenta de rotular (caixas) com as classes `meu_pokemon`, `selvagem`, `selvagem_shiny`,
  `corpo`, `corpo_shiny`.
- [ ] Formato do dataset compatível com o treino YOLO; divisão treino/validação.
- [ ] Rotular junto com o usuário um primeiro lote.

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

- [ ] `perception/coords.py`: `x, y, z` por dígitos-modelo.
- [ ] `actuation/movement.py`: teclado numérico com Num Lock desligado, 8 direções, confirmado pela coordenada.
- [ ] `hunts/hunt_model.py`: rota, alvos, bolas, **equipe com papéis**, regras; `hunts/*.json`.

**Aceite:** o bot anda de A a B por coordenadas numa área real; leitura de coordenada sem erro numa sequência de passos.

### E09: Gravador de hunt e editor de rota
- [ ] `hunts/recorder.py`: grava posições, paradas (tempo), teclas apertadas e escadas → rascunho de rota.
- [ ] Aba **Rota/Mapa**: posição atual, editor de pontos (andar, lurar, matar, escada).
- [ ] Aba **Hunt**: escolher a hunt salva e iniciar.

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
| 10–20 prints de hunt com lure cheio, em 1920×1080 **e** 3440×1440 | E04, E05 | ⬜ |
| Shiny vivo ao lado de normal; corpo de shiny ao lado de corpo normal | E05, E07 | ⬜ |
| Battle list cheia (com shiny e com o ícone de "longe do spawn") | E06 | ⬜ |
| Minimapa com as coordenadas visíveis | E08 | ⬜ |
| Pokémon com debuff ativo e o mesmo sem debuff | E12 | ⬜ |
| Hotbar e bag com poções, antídotos, revives e bolas | E07, E11 | ⬜ |
| Mensagens do chat de captura com sucesso e com falha | E07 | ⬜ |
| Analisador de hunt do jogo aberto | E13 | ⬜ |
| Tabela de itens da Q26 (nome, como usa, tecla) | E07, E11 | ⬜ |
| Vídeo de 5–10 min fazendo a hunt na mão | E04, E09, E14 | ⬜ |

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
