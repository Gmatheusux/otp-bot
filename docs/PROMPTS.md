# Prompts de início das etapas

Um prompt por etapa do [`GUIA.md`](../GUIA.md). Abra **uma conversa nova por etapa**, **na ordem**, e cole o prompt da
vez. Só comece a etapa seguinte depois que a anterior estiver ✅ no guia (§4).

Todos seguem o mesmo esqueleto: ler o guia → conferir a etapa anterior → dizer o plano → executar só o escopo →
rito de encerramento. As partes específicas lembram a IA do que é mais fácil errar em cada etapa.

> **Se a conversa abrir num worktree** (pasta separada criada pelo app), a IA deve, no fim, levar a branch para a
> `main` (merge) e fazer o push. Senão a etapa seguinte não enxerga o guia atualizado. Isso já está em cada prompt.

---

## E01: Git, spike de entrada sem foco e janela do jogo

```
Vamos executar a etapa E01 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E01: docs/ARQUITETURA.md §4 e §9 (risco R1) e
   docs/ESPECIFICACAO.md §1. Confira que a E00 está ✅ na §4 do guia.
2. Me diga o que entendeu do escopo, o plano e o que está fora do escopo. Espere meu ok.

Pontos de atenção desta etapa:
- O jogo está aberto no monitor secundário, em DirectX, e eu uso o monitor principal ao mesmo tempo.
- O spike é um TESTE: me avise antes de enviar qualquer tecla ou clique ao jogo e diga o que vai acontecer.
- O resultado do spike decide a D11. Registre o veredito em docs/ARQUITETURA.md com o que funcionou e o que não
  funcionou (teclado numérico com Num Lock desligado, F1–F12, clique), sem suposições.
- Meça a área do jogo nas duas resoluções (pendência P3 da especificação).

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E02: Nova estrutura de pastas, dados em %APPDATA% e limpeza

```
Vamos executar a etapa E02 do OTP Bot.

1. Leia o GUIA.md inteiro (inclusive a passagem da E01 na §7) e, da "Leitura obrigatória" da E02:
   docs/ARQUITETURA.md §7 e §8.3. Confira que a E01 está ✅.
2. Me diga o escopo, o plano de movimentação dos arquivos (de → para) e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- É uma reorganização SEM mudar comportamento. Antes de mover, rode os testes e anote o resultado; depois de
  mover, tudo tem que continuar igual.
- Ao migrar os dados para %APPDATA%\OTPBot, não apague nada do lugar antigo até confirmar a cópia.
- Remova só os módulos listados no guia como "saem"; confira com busca no código que nada mais os importa.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E03: WorldState, árbitro, fila e trava de entrada

```
Vamos executar a etapa E03 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E03: docs/ARQUITETURA.md §3 e §4, e o veredito do spike
   da E01 (D11). Confira que a E02 está ✅.
2. Me diga o escopo, o desenho das interfaces (WorldState, comportamento, ação, backend de entrada) e o que está
   fora. Espere meu ok.

Pontos de atenção desta etapa:
- O comportamento atual (combo, defesa, postura, cura, captura) tem que continuar igual; é portar, não reescrever regra.
- Nenhuma tecla ou clique pode sair fora da trava de entrada: prove com teste.
- Use o backend de entrada que o spike da E01 aprovou; o outro fica como alternativa configurável.
- Regras novas de hunt NÃO entram aqui (são da E10).

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E04: Coleta de prints e ferramenta de rotular

```
Vamos executar a etapa E04 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E04: docs/ARQUITETURA.md §6 e docs/ESPECIFICACAO.md §3 e
   §8. Confira que a E03 está ✅ e veja na §6 do guia que material do jogo já chegou.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- As classes são exatamente: meu_pokemon, selvagem, selvagem_shiny, corpo, corpo_shiny. Não crie outras sem me perguntar.
- O dataset fica em %APPDATA%\OTPBot\dataset, no formato que o treino YOLO lê, com divisão treino/validação.
- Vou rotular junto com você um primeiro lote: me guie na ferramenta.
- Registre na §6 do guia o material que eu entregar nesta conversa.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E05: Treino, ONNX e visão ao vivo

```
Vamos executar a etapa E05 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E05: docs/ARQUITETURA.md §2, §6, §8.1 e o risco R2.
   Confira que a E04 está ✅.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Minha GPU é uma RTX 5060 Ti de 8 GB e vou jogar, rodar o bot e treinar ao mesmo tempo: treino em processo
  separado, prioridade baixa, limite de VRAM.
- O núcleo usa ONNX Runtime; torch/ultralytics ficam só no kit de treino (trainer/).
- Registre no guia as métricas por classe do modelo treinado, com números reais.
- O modelo novo entra sem reiniciar o bot.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E06: Leitor da Battle e alertas de segurança

```
Vamos executar a etapa E06 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E06: docs/ESPECIFICACAO.md §2.2, §3 e §7.
   Confira que a E03 está ✅ e que os prints da Battle (§6 do guia) já chegaram.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- O leitor da Battle precisa de: quantidade, ícone de shiny, ícone de "longe do spawn", nome fora da espécie da
  hunt (possível GM) e linha de jogador. Use os meus prints reais para calibrar e testar.
- GM aparece como pokémon com nome diferente da espécie (ex.: Pikachu chamado "xyz").
- GM ou jogador na tela: pausa sozinho + aviso + alarme sonoro no console. Nada de respostas automáticas.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E07: Captura de shiny

```
Vamos executar a etapa E07 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E07: docs/ESPECIFICACAO.md §3. Confira que a E05 e a E06
   estão ✅ e que as mensagens de captura do chat (§6 do guia) já chegaram.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Eu escolho no console o corpo a capturar e o sprite da bola (shiny e normal), cada um com a sua tecla.
- Usar a bola = cursor sobre o corpo + hotkey da bola (auto use).
- Captura confirmada pela mensagem do chat (pt e en) e pelo corpo sumir; até N tentativas.
- A rota fica segurada até resolver a captura. Bolas acabaram: só notificar.
- Me avise antes de testar no jogo.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E08: Coordenadas, movimento e modelo de hunt

```
Vamos executar a etapa E08 do OTP Bot.

1. Leia o GUIA.md inteiro e, da "Leitura obrigatória" da E08: docs/ESPECIFICACAO.md §6 e docs/ARQUITETURA.md §5.
   Confira que a E03 está ✅ e que o print do minimapa com coordenadas (§6 do guia) já chegou.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Coordenadas x, y, z lidas por dígitos-modelo (fonte fixa do jogo), não por Tesseract.
- Movimento só pelo teclado numérico com Num Lock DESLIGADO: 7 ↖, 8 ↑, 9 ↗, 4 ←, 6 →, 1 ↙, 2 ↓, 3 ↘.
  Cada passo é confirmado pela coordenada.
- O modelo de hunt já nasce com "equipe com papéis" (dano e curador na v1; lure e 2º dano ficam para a v2).
- Me avise antes de mover o personagem no jogo.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E09: Gravador de hunt e editor de rota

```
Vamos executar a etapa E09 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §6 e docs/ARQUITETURA.md §5. Confira que a E08 está ✅.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Eu faço a hunt jogando e o gravador registra: posições, onde eu paro e por quanto tempo, todas as teclas que eu
  aperto e as trocas de andar (z). O resultado é um RASCUNHO que eu reviso.
- Ponto de matar = onde eu apertei o combo; escada = onde o z mudou.
- Abas novas: Rota/Mapa (editor de pontos: andar, lurar, matar, escada) e Hunt (escolher e iniciar).
- O teste é gravar uma volta real minha; me diga quando começar e parar.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E10: Fases da hunt e Companion

```
Vamos executar a etapa E10 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §2 inteiro e §7. Confira que a E06 e a E09 estão ✅.
2. Me diga o escopo, o plano (as fases e as transições) e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Siga o diagrama de fases da especificação §2 sem inventar regras.
- Lure com postura defensiva; buff de defesa com 5+ na tela; parada por N juntos, ponto de matar com N mínimo,
  ou ícone de "longe do spawn" (o que vier primeiro).
- Combo com postura ofensiva; revive depois; sobras ficam para a próxima volta.
- Perdido: para e avisa. Pokémon desmaiou: revive e continua.
- Companion: só minha entrada NO JOGO pausa (mexer no outro monitor não conta); retomar pelo console.
- Aceite = uma volta completa sem intervenção; me avise antes de rodar no jogo.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E11: Cura e troca de pokémon validadas

```
Vamos executar a etapa E11 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §4. Confira que a E10 está ✅.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Reaproveite a rotina de cura que já existe (heal_routine), portada para a fase "curar".
- Gatilho: MEU HP (barra vermelha) abaixo de 90%, com a box morta e a área limpa.
- Troca de pokémon por hotkey. Curador e pokémon de dano eu aponto no console.
- Validação no jogo de ponta a ponta: me avise antes de cada teste.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E12: Debuff e antídoto

```
Vamos executar a etapa E12 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §2.3 e §5. Confira que a E10 está ✅ e que os prints com e sem
   debuff (§6 do guia) já chegaram.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- O debuff aparece embaixo da barra de skills do pokémon: nova região de calibração nos dois perfis.
- Todos os debuffs (veneno, queimadura, paralisia, sono, confusão) saem com o mesmo antídoto.
- Com debuff as skills não saem: o combo só pode ser solto sem debuff. Antídoto em recarga = esperar.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E13: Gravador de sessões, analisador do jogo e aba Sessão

```
Vamos executar a etapa E13 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §8 e §9 e docs/ARQUITETURA.md §6. Confira que a E10 está ✅ e
   que o print do analisador de hunt do jogo (§6 do guia) já chegou.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- O gravador de sessões registra estado + ação + resultado; é a base da E14, então o formato precisa ser estável
  e documentado em docs/ARQUITETURA.md.
- O saldo vem do analisador de hunt do próprio jogo.
- Aba Sessão: mortos, bolas jogadas, dinheiro positivo e negativo, itens usados, EXP/h.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E14: Aprender comigo e otimizador

```
Vamos executar a etapa E14 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §8 e docs/ARQUITETURA.md §6. Confira que a E13 está ✅ e que
   existem sessões gravadas.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Eficiência = mais selvagens mortos por hora (normais e shiny) com o maior saldo positivo.
- Limites duros: nunca passar do ícone de "longe do spawn"; nunca baixar o HP de cura que eu defini.
- O otimizador SUGERE; eu aceito ou recuso na aba Aprender. Nada é aplicado sozinho.
- Sem aprendizado por reforço direto no jogo.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E15: Build, instalador e atualização automática

```
Vamos executar a etapa E15 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ARQUITETURA.md §8 inteiro. Confira que a E03 está ✅ (as etapas de jogo não são
   pré-requisito desta).
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- PyInstaller onedir para o núcleo e para o kit de treino; console compilado; Tesseract e ONNX Runtime embutidos.
- Velopack para instalador e atualização; a ferramenta vpk precisa do .NET só na máquina de build.
- Atualizações a partir de GitHub Releases privado (repo Gmatheusux/otp-bot). Nenhum token ou segredo no repositório.
- Atualizar não pode apagar nada de %APPDATA%\OTPBot: teste isso.
- Atualize o README com instalação e uso pelo instalador.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E16: Launcher, auto-login e overlay

```
Vamos executar a etapa E16 do OTP Bot.

1. Leia o GUIA.md inteiro e docs/ESPECIFICACAO.md §9 e docs/ARQUITETURA.md §2, §8.4 e o risco R6. Confira que a
   E15 está ✅.
2. Me diga o escopo, o plano e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Aba Contas: abrir o jogo, escolher DirectX, escolher a conta.
- Auto-login: conta secundária primeiro, depois a principal, depois a hunt.
- Senhas SÓ no Gerenciador de Credenciais do Windows: nunca no config.json, em log, em print ou no chat.
  Eu mesmo cadastro as senhas pelo console; você não digita nem pede as minhas senhas.
- Overlay: janela transparente sobre o jogo, que não recebe clique.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```

## E17: Validação final da v1.0

```
Vamos executar a etapa E17 do OTP Bot.

1. Leia o GUIA.md inteiro, docs/ESPECIFICACAO.md e docs/ARQUITETURA.md. Confira que E01–E16 estão ✅; liste as que
   não estiverem e pare se alguma for necessária para a v1.0.
2. Me diga o roteiro de validação e o que está fora. Espere meu ok.

Pontos de atenção desta etapa:
- Aceite: hunt completa de 1 hora sem intervenção, com captura de shiny, cura, debuff e alertas, e zero mortes.
- Confira cada regra da especificação contra o que o bot fez na sessão gravada; anote divergências.
- Revise README, docs/ e o GUIA.md; publique a versão 1.0 pelo instalador.

No fim, execute o rito de encerramento do GUIA.md (§1.2, itens 10 a 15). Se esta conversa estiver num worktree,
faça o merge na main e o push.
```
