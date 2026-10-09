# Anamnese — OTP Bot (Poke Alliance) v1.0

> Como responder: escreva embaixo de cada pergunta, na linha `R:`. Pode ser curto.
> 🔴 = bloqueia o desenvolvimento · 🟡 = muda o desenho · ⚪ = detalhe/ajuste fino.
> Se tiver prints (com e sem shiny, corpo, debuff, battle list, minimapa), coloque em `docs/prints/` e cite o nome do arquivo na resposta. Print vale mais que descrição.

---

## Parte 1 — O que já existe × o que você pediu

### 1.1 Diagnóstico do repositório (estado em 2026-10-09)

| Área | Situação hoje | O que falta para o objetivo |
|---|---|---|
| **Captura de tela** | `mss`, tela inteira, perfil por resolução (3440×1440 e 1920×1080) | Escolher monitor/janela; lidar com escala do Windows (DPI) e janela/tela cheia |
| **Leitura de barras (cor)** | ✅ HP jogador (vermelha), HP pokémon (azul), EXP, Pokébar, postura | Validar no jogo; status/debuff ainda não é lido |
| **Visão com IA (YOLO na GPU)** | Código pronto (CUDA + FP16), **sem modelo treinado** → roda em *mock*, não vê nada | **Tudo:** dataset, ferramenta de rotular, treino na 5060 Ti, export TensorRT, métricas |
| **Classes que a IA reconhece** | Só 3 previstas: seu pokémon, selvagem, corpo | Shiny × normal, espécie (talvez), corpo de shiny, itens no chão (?) |
| **Itens / pokébolas** | ✅ Biblioteca de sprites + template matching (só reconhece, não usa) | Usar automaticamente (antídoto, poção, revive, bola certa) |
| **Rota (cavebot)** | Grava cliques **em posição da tela** e repete com tempo fixo | Andar por **coordenada do mapa** (x, y, z via OCR), saber onde está, se perdeu, travou |
| **Lure → parar → matar** | Combo/defesa quando "cercado" (N mobs perto do seu pokémon) | Fase "juntar" consciente da rota, ponto/critério de parada, contagem confiável |
| **Captura** | Joga bola em **qualquer** corpo | **Só em corpo de shiny**; saber qual bola; confirmar se capturou |
| **Cura com pokémon** | ✅ Código pronto: troca p/ curador → rotação → revive → volta ao farm (não validado no jogo) | Validar; decidir gatilho; poção |
| **Debuff → antídoto antes do combo** | `ui_analyzer.py` tem um protótipo **não ligado** | Detectar o debuff, usar antídoto, só então combar |
| **"Número na tela" para parar e bater** | Não existe | Entender que número é esse (Parte 3) |
| **Aprendizado** | `ai/` é protótipo fuzzy não usado; DESIGN.md prevê "logs de eventos → árvores de decisão" | Gravar sessões, métrica de eficiência, mecanismo que ajusta parâmetros sozinho |
| **Segurança** | ✅ Monitor de GM no chat (OCR) | Jogador na tela, PM, morte, Telegram |
| **Console** | ✅ React + pywebview, 12 abas, API local com token | Abas novas (Visão/Treino, Hunt, Estatísticas) |
| **Executável** | Roda com `python main.py` | Empacotar (.exe), instalador, atualização |

**Conclusão:** a casca está boa (console, calibração, cura, teclado/mouse, API). O **coração do pedido — ver pokémons, distinguir shiny, itens e bolas — ainda não existe**, porque não há modelo de visão nem pipeline de dados. Esse é o caminho crítico da v1.0.

### 1.2 Dívidas técnicas que vou resolver junto (não precisa responder)
- Módulos mortos: `ai/`, `core/keyboard.py`, `core/mouse.py`, `modules/vision.py`, `modules/ui_analyzer.py` (será reaproveitado ou removido).
- `catch` dispara em qualquer corpo; cavebot depende da janela não mudar de lugar.
- "Área limpa" da cura é sempre verdadeira enquanto não há modelo.
- Falta a barra de golpes no perfil 1920×1080.

---

## Parte 2 — Jogo, conta e ambiente

1. 🔴 Qual o **client** do Poke Alliance (OTClient próprio / versão)? Ele roda em **janela, tela cheia ou janela sem borda**?
   R:
2. 🔴 Quais **monitores/resoluções** você vai usar de verdade? (já tenho 3440×1440 e 1920×1080). Usa **escala do Windows** diferente de 100% em algum?
   R:
3. 🟡 O jogo fica sempre no **monitor principal**? Você joga com o jogo em um monitor e o console do bot em outro?
   R: Dois monitores: jogo + automação em um (o principal), console e coisas leves no outro.
4. 🟡 O **zoom da área do jogo** muda? (no 3440 a área é ~2× maior que no 1080 → os sprites mudam de tamanho). Existe opção de zoom/escala no client?
   R:
5. 🔴 Sua 5060 Ti é a de **8 GB ou 16 GB**? Qual CPU e RAM? O PC vai rodar jogo + bot + treino ao mesmo tempo?
   R: RTX 5060 Ti 8 GB, Ryzen 7 5800X3D, 32 GB de RAM.
6. 🟡 O bot vai rodar **só no seu PC** ou quer distribuir para outras pessoas (amigos/venda)? Isso muda proteção, instalador e licença.
   R:
7. ⚪ Joga com **1 personagem** ou vários (multi-client)? (multi-client é v2.0?)
   R:

---

## Parte 3 — A hunt (o ciclo principal)

> Meu entendimento atual do ciclo — corrija o que estiver errado:
> **andar na rota → juntar selvagens (lure) → ao atingir o critério, parar → (antídoto se debuff) → combo → matar → bola só nos corpos de shiny → continuar a rota.**
> Em paralelo: se tomar dano → curador → rotação de cura → revive → volta o pokémon de dano.

8. 🔴 Descreva **uma hunt típica do começo ao fim**, como você joga na mão (pode ser em tópicos).
   R:
9. 🔴 **"Lurar"**: você anda e os selvagens te seguem? Ou ataca de leve para puxar? Quantos costuma juntar? Existe um **máximo seguro**?
   R:
10. 🔴 **"Quando o número na tela for suficiente para parar e bater"** — que número é esse exatamente?
    - (a) quantidade de selvagens na **battle list**,
    - (b) um contador que o client mostra,
    - (c) quantidade que você conta na área do jogo,
    - (d) outro. Mande print de onde aparece.
    R:
11. 🔴 O ponto de parar é **fixo na rota** (ex.: "pare no waypoint 7") ou **dinâmico** (parar em qualquer lugar ao atingir N)? Ou os dois?
    R:
12. 🔴 O **combo**: é uma tecla só ou uma sequência de golpes (m1, m2, m3...)? Cada golpe tem recarga própria? O bot precisa ler a **barra de golpes** para saber o que está disponível?
    R:
13. 🟡 Depois do combo, se sobrar selvagem vivo, o que você faz? (golpe single, segundo combo, ataque básico, mirar no de menos vida?)
    R:
14. 🟡 Você usa **postura** (ofensivo/neutro/defensivo) na hunt? Em qual fase cada uma?
    R:
15. 🟡 A **defesa** (buff defensivo) — quando usa? Ainda faz sentido a regra atual "N mobs colados → defesa + combo + revive"?
    R:
16. ⚪ Quanto tempo dura uma volta da rota? Quantas voltas por hora?
    R:

---

## Parte 4 — Shiny, corpos e captura

17. 🔴 Como você **sabe que um pokémon é shiny** no Poke Alliance? Marque tudo que vale:
    - (a) cor diferente do sprite,
    - (b) nome "Shiny X" em cima dele,
    - (c) nome "Shiny X" na battle list,
    - (d) brilho/efeito,
    - (e) mensagem no chat/log. **Mande print de um shiny vivo ao lado de um normal.**
    R:
18. 🔴 O **corpo do shiny** é diferente do corpo normal? (cor, ícone, nome ao passar o mouse/olhar?) Mande print.
    R:
19. 🔴 Quando morre um shiny no meio de 10 normais, como você acha o corpo certo? (se o corpo for igual, o bot precisa **rastrear** o shiny desde vivo até morrer e lembrar onde caiu.)
    R:
20. 🔴 Quais **pokémons** a captura deve buscar? (lista de espécies? "qualquer shiny"? alguns normais também?)
    R:
21. 🔴 **Qual pokébola** para qual caso? (ultra para shiny, poké para normal, por espécie...). Quais bolas existem no servidor?
    R:
22. 🟡 Como se usa a bola: **tecla da hotbar + clique no corpo**, ou arrasta, ou clique direito? (hoje: tecla + clique.)
    R:
23. 🟡 Como você sabe se **capturou ou falhou**? (mensagem no chat, animação, corpo some?) Se falhar, tenta de novo? Quantas vezes?
    R:
24. 🟡 Corpo tem **tempo** para sumir? Quanto? Precisa capturar antes de andar?
    R:
25. ⚪ Tem **loot** para coletar nos corpos/chão? Ou só captura?
    R:

---

## Parte 5 — Itens, pokébolas e inventário

26. 🔴 Lista dos **itens que o bot precisa usar** e como cada um é usado (tecla, clique na bag, clique no pokémon):
    - Poção: 
    - Revive: 
    - Antídoto: 
    - Pokébolas: 
    - Outros (food, buffs, elixires...): 
    R:
27. 🟡 O bot precisa **distinguir itens na tela** onde? (hotbar, bag aberta, chão, loot?) Ou basta saber a tecla?
    R:
28. 🟡 O bot deve **contar estoque** (ex.: "acabaram as ultra balls → parar/ir comprar")? Quando acaba, o que fazer?
    R:
29. ⚪ Refil/depósito/compra automática é v1.0 ou v2.0?
    R:

---

## Parte 6 — Dano, cura e troca de pokémon

30. 🔴 "Se o **player** tomar dano" — o gatilho é a **barra vermelha (você)** ou a **barra azul (seu pokémon)**? Ou os dois com regras diferentes?
    R:
31. 🔴 Limites: com quanto % de HP começa a cura? Existe um % de **emergência** (fugir, poção, deslogar)?
    R:
32. 🔴 A cura pode acontecer **com selvagens perto** ou só com a área limpa? (hoje: só com a área limpa, e aborta se aparecer selvagem.)
    R:
33. 🟡 Quem é o **curador** e quais golpes da rotação de cura (em ordem)? O revive nele serve para **zerar recarga** — confirmado?
    R:
34. 🟡 Trocar de pokémon: **clique na Pokébar** funciona com 1 clique? Ou precisa de tecla / duplo clique? (README marca como não confirmado.)
    R:
35. 🟡 E se o **pokémon de dano morrer** (HP azul = 0)? Revive e continua? Recua?
    R:
36. ⚪ Existe cura do **jogador** por item/skill além do pokémon curador?
    R:

---

## Parte 7 — Debuff e antídoto

37. 🔴 Quais **debuffs** existem (veneno, queimadura, paralisia, sono, confusão...)? Todos curam com o **mesmo antídoto** ou itens diferentes?
    R:
38. 🔴 **Onde aparece** o debuff na tela? (ícone no painel do pokémon, cor da barra, texto, partícula no sprite?) Mande print com e sem debuff.
    R:
39. 🟡 O debuff atrapalha o **combo** (por isso usar antídoto antes)? Ou só causa dano? Se o antídoto estiver em recarga, espera ou combo assim mesmo?
    R:
40. ⚪ O debuff é no **pokémon**, no **jogador** ou nos dois?
    R:

---

## Parte 8 — Mapa e rota

41. 🔴 O que é o **"mapa liberado"**? (a) arquivo do mapa do servidor (OTBM), (b) imagem do minimapa completo, (c) site/wiki com o mapa, (d) outro? Você tem acesso a ele?
    R:
42. 🔴 Como você quer **gravar a rota manualmente**? (a) clicando no minimapa como hoje, (b) andando e o bot lendo as coordenadas x, y, z, (c) desenhando no mapa dentro do console.
    R:
43. 🔴 Como o personagem **anda**? Clique no minimapa, clique na área do jogo, setas/WASD? Qual você prefere que o bot use?
    R:
44. 🟡 As **coordenadas** `x, y, z` aparecem sempre no canto do minimapa? (vi a região `coords` calibrada.) Muda de andar (z) na hunt — escadas, buracos, teleport?
    R:
45. 🟡 Na rota, quais **tipos de ponto** você precisa? Ex.: andar, **parar e lurar**, **parar e matar**, usar escada/corda, esperar X s, falar com NPC.
    R:
46. 🟡 Se o bot **se perder** (empurrado, travado em pokémon, teleporte), o que fazer? Voltar ao ponto mais próximo? Parar e avisar?
    R:
47. ⚪ Quantas hunts/rotas diferentes você pretende ter salvas?
    R:

---

## Parte 9 — Aprendizado de máquina ("aprender a jogar melhor")

> Proposta técnica (para você validar): **não** usar aprendizado por reforço direto no jogo (lento, arriscado, gera comportamento estranho). Em vez disso:
> 1. **Visão** aprende com seus prints rotulados (YOLO treinado na 5060 Ti) — ver pokémon, shiny, corpo, item.
> 2. **Gravador de sessões**: toda hunt gera um log estruturado (estado da tela + ação + resultado).
> 3. **Imitação**: o bot observa **você jogando** (modo "aprender comigo") e aprende *quando* você para, combo, cura.
> 4. **Otimizador**: testa variações dos parâmetros (tamanho do lure, ponto de parada, limites de HP) e fica com o que der **mais eficiência**, com limites de segurança que você define.

48. 🔴 O que é **"eficiência"** para você? Ordene: EXP/hora · shinies capturados/hora · lucro/hora · zero mortes · menos itens gastos.
    R:
49. 🔴 Concorda com a proposta acima? Quer o modo **"aprender comigo"** (você joga e o bot grava/aprende)?
    R:
50. 🟡 O que o bot **pode** mudar sozinho e o que **nunca** pode? (ex.: pode aumentar o lure até X, nunca descer o HP mínimo abaixo de Y.)
    R:
51. 🟡 Para treinar a visão você topa **rotular imagens** (desenhar caixas) por algumas horas? Eu faria uma ferramenta de rotular dentro do console + auto-rotulagem para acelerar.
    R:
52. 🟡 Quantas **espécies** de pokémon aparecem nas hunts da v1.0? O bot precisa saber a **espécie** de cada selvagem ou basta "selvagem / shiny / meu / corpo"?
    R:
53. ⚪ O treino pode rodar **enquanto você joga** ou só com o PC livre?
    R:

---

## Parte 10 — Segurança e comportamento humano

54. 🟡 Além de GM no chat: alertas de **jogador na tela**, **PM**, **morte**, **som**, **Telegram** — quais são obrigatórios na v1.0?
    R:
55. 🟡 Ao detectar GM/perigo: **pausar**, **deslogar**, **fechar o jogo** ou só avisar?
    R:
56. ⚪ Quer pausas aleatórias/tempo máximo de sessão por dia?
    R:
57. ⚪ **Modo Companion**: você mexe no teclado/mouse e o bot cede o controle na hora. Quer isso na v1.0?
    R:

---

## Parte 11 — Executável e console

> Proposta de layout final (corrija/adicione):

```
┌──────────────────────────────────────────────────────────────────────┐
│ OTP Bot  ● Rodando  [▶ Play] [⏸] [⏹]   GPU 5060Ti 18ms · 32 FPS   ⚙ │
├────────────┬─────────────────────────────────────────────────────────┤
│ Início     │  ┌ Visão ao vivo ───────────────┐ ┌ Estado ────────────┐ │
│ Hunt   ★   │  │ print do jogo com caixas:    │ │ HP você   ███▒ 82% │ │
│ Combate    │  │ verde=meu, vermelho=selvagem │ │ HP poké   ████ 96% │ │
│ Cura       │  │ dourado=SHINY, cinza=corpo   │ │ Debuff    —        │ │
│ Captura    │  │ azul=item                    │ │ Fase      LURE 6/8 │ │
│ Itens      │  └──────────────────────────────┘ │ Rota      WP 7/23  │ │
│ Rota/Mapa  │  ┌ Sessão ──────────────────────┐ └────────────────────┘ │
│ Visão/IA ★ │  │ EXP/h 1.2M · shinies 3 · bolas 41 · mortes 0     │ │
│ Aprender ★ │  └──────────────────────────────────────────────────┘ │
│ Segurança  │  ┌ Log ─────────────────────────────────────────────┐ │
│ Calibração │  │ 14:02 Lure 8/8 → parando no WP 7                 │ │
│ Atalhos    │  │ 14:02 Debuff veneno → antídoto → combo            │ │
│ Ajustes    │  │ 14:03 Shiny Scyther morto → ultra ball → capturado│ │
└────────────┴─────────────────────────────────────────────────────────┘
★ = abas novas
```

- **Hunt** – escolhe a hunt salva (rota + pokémons-alvo + regras), botão "Iniciar hunt".
- **Rota/Mapa** – mapa com a posição atual, editor de pontos (andar/lurar/parar/escada).
- **Visão/IA** – teste da visão ao vivo, % de acerto por classe, coletar prints, rotular, treinar, trocar modelo.
- **Aprender** – sessões gravadas, gráficos de eficiência, sugestões do otimizador (aceitar/recusar).

58. 🟡 Esse layout atende? O que tirar/adicionar?
    R:
59. 🟡 Formato da entrega: **pasta com .exe** (mais simples, ~3–4 GB por causa do PyTorch/CUDA) ou **instalador**? Precisa de **atualização automática**?
    R:
60. ⚪ Console sempre **em janela própria** ou também quer um **overlay** em cima do jogo (caixas e status desenhados sobre o client)?
    R:
61. ⚪ Idioma só PT-BR?
    R:

---

## Parte 12 — Prioridade

62. 🔴 Ordene o que você quer **funcionando primeiro** (1 = primeiro):
    - [ ] Visão vendo selvagens/corpos/shiny
    - [ ] Captura só de shiny
    - [ ] Rota por coordenadas + lure/parada
    - [ ] Cura/troca de pokémon validada no jogo
    - [ ] Debuff + antídoto antes do combo
    - [ ] Aprendizado/otimização
    - [ ] Executável empacotado
    R:
63. ⚪ Algo do **endgame (v2.0)** que eu deva já deixar preparado na arquitetura? Explique em 2 linhas como ele funciona diferente.
    R:

---

## Parte 13 — Material que eu preciso de você

- [ ] 10–20 prints de hunt (1920×1080 **e** 3440×1440), com lure cheio.
- [ ] Print de **shiny vivo** ao lado de um normal + **corpo de shiny** ao lado de corpo normal.
- [ ] Print com **debuff** ativo (e o mesmo sem).
- [ ] Print da **battle list** cheia e do **número** que define a parada.
- [ ] Print do **minimapa com coordenadas** e, se existir, o **mapa liberado**.
- [ ] Print da **hotbar** e da **bag** com poções, antídotos, revives e bolas.
- [ ] (ideal) Um **vídeo de 5–10 min** de você fazendo a hunt na mão — serve para rotular e para o modo "aprender comigo".

---

## O que acontece depois das respostas

Com as respostas eu devolvo: (1) **especificação final** (regras em formato Dado/Quando/Então), (2) **arquitetura** atualizada no `DESIGN.md`, (3) **roadmap em fases** com critério de pronto de cada fase, começando pelo caminho crítico: **dataset → treino do YOLO na 5060 Ti → captura de shiny**.
