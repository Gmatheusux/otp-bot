/**
 * Descrição das abas do console. Cada campo aponta para um caminho do config.json.
 * status 'ativo'     -> o bot já executa essa função
 * status 'planejado' -> a configuração fica salva, mas o bot ainda não executa
 */

const ELEMENTS = [
  'normal', 'fire', 'fighting', 'water', 'flying', 'grass', 'poison', 'electric', 'ground',
  'psychic', 'rock', 'ice', 'bug', 'dragon', 'ghost', 'dark', 'steel', 'fairy',
].map((value) => ({ value, label: value[0].toUpperCase() + value.slice(1) }))

import HealTestPanel from '../components/HealTestPanel.jsx'

const HEAL = 'features.heal.pokemon_heal'

const STANCE_OPTIONS = [
  { value: 'offensive', label: 'Ofensivo' },
  { value: 'neutral', label: 'Neutro' },
  { value: 'defensive', label: 'Defensivo' },
]

export const TABS = [
  {
    id: 'inicio',
    label: 'Início',
    icon: 'home',
    description: 'Visão geral: estado do bot, funções principais e o que ele está fazendo agora.',
    custom: 'overview',
  },
  {
    id: 'combate',
    label: 'Combate',
    icon: 'swords',
    description: 'Como o bot ataca e se defende quando há pokémons selvagens na tela.',
    sections: [
      {
        title: 'Combo em área',
        status: 'ativo',
        description: 'Solta o combo do seu pokémon quando aparecem selvagens na tela.',
        fields: [
          { type: 'toggle', path: 'features.combat.auto_combo', label: 'Combo automático', hint: 'Desligado, o bot nunca usa o combo.' },
          { type: 'toggle', path: 'features.combat.kite_combo', label: 'Combar enquanto anda', hint: 'Usa o combo assim que houver selvagens, sem esperar juntar.' },
          { type: 'key', path: 'pokemon_profile.auto_combo_key', label: 'Tecla do combo' },
          { type: 'number', path: 'cooldowns.auto_combo', label: 'Intervalo entre combos', unit: 's', min: 0.5, max: 60, step: 0.5 },
        ],
      },
      {
        title: 'Defesa quando cercado',
        status: 'ativo',
        description:
          'Quando muitos selvagens ficam colados no seu pokémon (lure denso), o bot solta defesa, combo e revive em sequência.',
        fields: [
          { type: 'toggle', path: 'features.combat.boxed_defense', label: 'Ativar defesa' },
          { type: 'number', path: 'features.combat.boxed_mobs', label: 'Selvagens para considerar "cercado"', min: 1, max: 30 },
          {
            type: 'slider', path: 'features.combat.boxed_radius_pct', label: 'Distância de "colado"', unit: '%', min: 5, max: 40,
            hint: 'Raio em volta do seu pokémon, em % da largura da tela.',
          },
          { type: 'key', path: 'pokemon_profile.defensive_buff_key', label: 'Tecla da defesa' },
          { type: 'number', path: 'cooldowns.defensive_buff', label: 'Intervalo da defesa', unit: 's', min: 1, max: 120, step: 0.5 },
          { type: 'toggle', path: 'features.combat.revive_on_boxed', label: 'Usar revive na sequência' },
          { type: 'toggle', path: 'features.combat.stop_route_when_boxed', label: 'Parar a rota quando cercado' },
        ],
      },
      {
        title: 'Mira automática',
        status: 'planejado',
        description: 'Escolhe um selvagem por vez como alvo, priorizando shinies.',
        fields: [
          { type: 'toggle', path: 'features.target.auto_target', label: 'Mirar sozinho' },
          { type: 'number', path: 'features.target.range', label: 'Alcance', unit: 'sqm', min: 1, max: 15 },
          { type: 'toggle', path: 'features.target.shiny_priority', label: 'Prioridade para shiny' },
          { type: 'tags', path: 'features.target.shiny_words', label: 'Palavras que indicam shiny', placeholder: 'ex: shiny' },
          { type: 'tags', path: 'features.target.ignore', label: 'Ignorar estes pokémons', placeholder: 'Nome e Enter' },
        ],
      },
      {
        title: 'Postura automática',
        status: 'ativo',
        description:
          'Clica na mão do painel Pokémon conforme a fase: vermelha = ofensivo, cinza = neutro, verde = defensivo. Antes de ligar, confira na aba Calibração se a postura atual está sendo lida certo.',
        fields: [
          { type: 'toggle', path: 'features.stance.auto', label: 'Trocar postura sozinho' },
          { type: 'segmented', path: 'features.stance.normal', label: 'Normal', hint: 'Sem selvagens na tela.', options: STANCE_OPTIONS },
          { type: 'segmented', path: 'features.stance.lure', label: 'Juntando (lure)', hint: 'Selvagens na tela, ainda juntando.', options: STANCE_OPTIONS },
          { type: 'segmented', path: 'features.stance.combo', label: 'Cercado (combo)', hint: 'Hora de soltar o combo.', options: STANCE_OPTIONS },
          { type: 'number', path: 'cooldowns.stance', label: 'Intervalo mínimo entre trocas', unit: 's', min: 0.5, max: 30, step: 0.5 },
        ],
      },
    ],
  },
  {
    id: 'cura',
    label: 'Cura',
    icon: 'heart',
    description: 'Revive do pokémon e cura do jogador.',
    sections: [
      {
        title: 'Revive',
        status: 'ativo',
        description: 'Usado na sequência de defesa quando o seu pokémon fica cercado e, se você não definir outra tecla, também na cura com pokémon.',
        fields: [
          { type: 'key', path: 'pokemon_profile.revive_key', label: 'Tecla do revive' },
          { type: 'number', path: 'cooldowns.revive', label: 'Intervalo mínimo', unit: 's', min: 1, max: 60, step: 0.5 },
        ],
      },
      {
        title: 'Poção de vida',
        status: 'planejado',
        description: 'Usa a poção quando a vida do jogador cair abaixo do limite.',
        fields: [
          { type: 'toggle', path: 'features.heal.potion.enabled', label: 'Curar com poção' },
          { type: 'slider', path: 'features.heal.potion.hp_percent', label: 'Curar abaixo de', unit: '%', min: 10, max: 95 },
          { type: 'key', path: 'features.heal.potion.key', label: 'Tecla da poção' },
        ],
      },
      {
        title: 'Cura com pokémon',
        status: 'ativo',
        description:
          'Quando o seu HP (barra vermelha) cair abaixo do limite, o bot espera a box acabar e não ter selvagem por perto, chama o pokémon de cura, faz a rotação de cura, usa revive nele para zerar a recarga das skills e volta para o pokémon de farm. Se aparecer selvagem no meio, ele volta na hora para o de farm.',
        extra: HealTestPanel,
        fields: [
          { type: 'toggle', path: `${HEAL}.enabled`, label: 'Ativar cura com pokémon', hint: 'Só liga quando você ativar aqui.' },
          { type: 'slider', path: `${HEAL}.hp_percent`, label: 'Curar quando o HP ficar abaixo de', unit: '%', min: 30, max: 99 },
          {
            type: 'segmented', path: `${HEAL}.swap_method`, label: 'Como trocar de pokémon',
            options: [
              { value: 'pokebar', label: 'Clicar na Pokébar' },
              { value: 'key', label: 'Tecla' },
            ],
          },
          {
            type: 'number', path: `${HEAL}.healer_slot`, label: 'Pokémon de cura', min: 1, max: 6,
            hint: 'Posição na Pokébar, contando de cima: 1 = o primeiro.', showIf: { path: `${HEAL}.swap_method`, equals: 'pokebar' },
          },
          { type: 'key', path: `${HEAL}.healer_key`, label: 'Tecla do pokémon de cura', showIf: { path: `${HEAL}.swap_method`, equals: 'key' } },
          { type: 'text', path: `${HEAL}.healer_name`, label: 'Nome do curador', placeholder: 'ex: Togepi', hint: 'Só para aparecer no log.' },
          {
            type: 'number', path: `${HEAL}.farm_slot`, label: 'Pokémon de farm', min: 1, max: 6,
            hint: 'O pokémon que o bot chama de volta depois de curar.', showIf: { path: `${HEAL}.swap_method`, equals: 'pokebar' },
          },
          { type: 'key', path: `${HEAL}.farm_key`, label: 'Tecla do pokémon de farm', showIf: { path: `${HEAL}.swap_method`, equals: 'key' } },
          { type: 'keylist', path: `${HEAL}.rotation`, label: 'Rotação de cura', hint: 'Golpes do curador, na ordem.', addLabel: 'Adicionar golpe' },
          { type: 'number', path: `${HEAL}.rotation_delay_ms`, label: 'Espera entre golpes', unit: 'ms', min: 100, max: 5000, step: 50 },
          { type: 'number', path: `${HEAL}.summon_wait_ms`, label: 'Espera ao trocar de pokémon', unit: 'ms', min: 300, max: 5000, step: 50, hint: 'Tempo para o pokémon sair da bola.' },
          { type: 'toggle', path: `${HEAL}.use_revive`, label: 'Usar revive no curador depois', hint: 'Zera a recarga das skills dele para a próxima cura.' },
          { type: 'key', path: `${HEAL}.revive_key`, label: 'Tecla do revive', hint: 'Sem tecla, usa a do Revive acima.', showIf: { path: `${HEAL}.use_revive`, equals: true } },
          { type: 'number', path: `${HEAL}.cooldown_s`, label: 'Intervalo mínimo entre curas', unit: 's', min: 3, max: 300 },
        ],
      },
      {
        title: 'Medicine',
        status: 'planejado',
        description: 'Cura status negativos (veneno, paralisia…) do pokémon.',
        fields: [
          { type: 'toggle', path: 'features.heal.medicine.enabled', label: 'Curar status' },
          { type: 'key', path: 'features.heal.medicine.key', label: 'Tecla da medicine' },
        ],
      },
    ],
  },
  {
    id: 'itens',
    label: 'Itens',
    icon: 'flask',
    description: 'Ensine o bot a reconhecer seus itens pela imagem (sprite) na tela.',
    custom: 'items',
  },
  {
    id: 'rota',
    label: 'Rota',
    icon: 'route',
    description: 'Grave um caminho clicando no minimapa e deixe o bot repetir (cavebot).',
    custom: 'route',
    sections: [
      {
        title: 'Opções da rota',
        status: 'planejado',
        fields: [
          { type: 'toggle', path: 'features.route.loop', label: 'Repetir a rota em loop' },
          { type: 'toggle', path: 'features.route.wait_first_waypoint', label: 'Esperar no primeiro ponto' },
          { type: 'toggle', path: 'features.route.vary_path', label: 'Variar o caminho' },
          { type: 'number', path: 'features.route.vary_sqm', label: 'Variação', unit: 'sqm', min: 1, max: 5 },
        ],
      },
    ],
  },
  {
    id: 'captura',
    label: 'Captura',
    icon: 'ball',
    description: 'Joga pokébola nos corpos dos selvagens derrotados.',
    sections: [
      {
        title: 'Captura automática',
        status: 'ativo',
        description:
          'Depois que um selvagem morre, aperta a tecla da pokébola e clica no corpo. Só acontece quando não há selvagens vivos na tela.',
        fields: [
          { type: 'toggle', path: 'features.catch.enabled', label: 'Capturar sozinho' },
          { type: 'key', path: 'hotkeys.catch_key', label: 'Tecla da pokébola' },
          { type: 'number', path: 'cooldowns.catch', label: 'Intervalo entre bolas', unit: 's', min: 0.2, max: 10, step: 0.1 },
        ],
      },
    ],
  },
  {
    id: 'seguranca',
    label: 'Segurança',
    icon: 'shield',
    description: 'O que o bot vigia enquanto você está longe, e como ele avisa.',
    sections: [
      {
        title: 'Monitor de GM',
        status: 'ativo',
        description:
          'Lê a última linha do chat; se aparecer GM, Admin ou Tutor, desliga o bot. Precisa do Tesseract instalado.',
        fields: [
          { type: 'toggle', path: 'features.safety.gm_monitor', label: 'Vigiar o chat' },
          {
            type: 'roi', path: 'features.safety.chat_roi', label: 'Área da última linha do chat',
            hint: 'Posição em pixels na tela (X, Y do canto superior esquerdo, largura e altura).',
          },
        ],
      },
      {
        title: 'Alertas',
        status: 'planejado',
        fields: [
          { type: 'toggle', path: 'features.alerts.player_on_screen', label: 'Jogador apareceu na tela' },
          { type: 'toggle', path: 'features.alerts.private_message', label: 'Recebi mensagem privada' },
          { type: 'toggle', path: 'features.alerts.death', label: 'Personagem morreu' },
          { type: 'toggle', path: 'features.alerts.sound', label: 'Tocar som' },
          { type: 'slider', path: 'features.alerts.volume', label: 'Volume', unit: '%', min: 0, max: 100 },
        ],
      },
      {
        title: 'Avisos no Telegram',
        status: 'planejado',
        fields: [
          { type: 'toggle', path: 'features.alerts.telegram', label: 'Enviar avisos para o Telegram' },
          { type: 'text', path: 'features.alerts.telegram_chat_id', label: 'Seu chat ID', placeholder: 'ex: 123456789' },
        ],
      },
    ],
  },
  {
    id: 'extras',
    label: 'Extras',
    icon: 'sparkles',
    description: 'Rotinas de apoio durante a hunt.',
    sections: [
      {
        title: 'Comida',
        status: 'planejado',
        fields: [
          { type: 'toggle', path: 'features.extras.food.enabled', label: 'Comer sozinho' },
          { type: 'key', path: 'features.extras.food.key', label: 'Tecla da comida' },
          { type: 'number', path: 'features.extras.food.interval_s', label: 'A cada', unit: 's', min: 30, max: 3600 },
        ],
      },
    ],
  },
  {
    id: 'guild',
    label: 'Guild',
    icon: 'users',
    description: 'Missões diárias da guild.',
    sections: [
      {
        title: 'Daily da guild',
        status: 'planejado',
        fields: [
          { type: 'toggle', path: 'features.guild.daily', label: 'Fazer a daily' },
          {
            type: 'segmented', path: 'features.guild.tier', label: 'Tier',
            options: [
              { value: 'normal', label: 'Normal' },
              { value: 'wildscape', label: 'Wildscape' },
              { value: 'primal', label: 'Primal' },
            ],
          },
          { type: 'segmented', path: 'features.guild.element', label: 'Elemento', options: ELEMENTS, columns: 6 },
        ],
      },
    ],
  },
  {
    id: 'calibracao',
    label: 'Calibração',
    icon: 'crosshair',
    description: 'Onde ficam HP, EXP, seus pokémons e as outras partes da tela que o bot lê.',
    custom: 'calibration',
  },
  {
    id: 'atalhos',
    label: 'Atalhos',
    icon: 'keyboard',
    description: 'Clique no campo e escolha a tecla na lista, ou aperte a tecla no teclado.',
    sections: [
      {
        title: 'Controle do bot',
        status: 'ativo',
        description: 'Teclas globais: funcionam mesmo com o jogo em foco.',
        fields: [
          { type: 'key', path: 'hotkeys.pause', label: 'Pausar / retomar' },
          { type: 'key', path: 'hotkeys.kill', label: 'Desligar o bot' },
          { type: 'key', path: 'hotkeys.record', label: 'Gravar rota' },
          { type: 'key', path: 'hotkeys.play', label: 'Tocar / parar rota' },
        ],
      },
      {
        title: 'Teclas do jogo',
        status: 'ativo',
        description: 'As teclas que o bot aperta dentro do jogo.',
        fields: [
          { type: 'key', path: 'pokemon_profile.auto_combo_key', label: 'Combo' },
          { type: 'key', path: 'pokemon_profile.defensive_buff_key', label: 'Defesa' },
          { type: 'key', path: 'pokemon_profile.revive_key', label: 'Revive' },
          { type: 'key', path: 'hotkeys.catch_key', label: 'Pokébola' },
        ],
      },
    ],
  },
  {
    id: 'ajustes',
    label: 'Ajustes',
    icon: 'settings',
    description: 'Desempenho, modelo de visão (IA), monitor do jogo e limites humanos.',
    sections: [
      {
        title: 'Visão (IA)',
        status: 'ativo',
        description: 'Quantas vezes por segundo o bot lê a tela e o quão confiante a IA precisa estar para considerar uma detecção.',
        fields: [
          { type: 'slider', path: 'engine.fps_target', label: 'Leituras por segundo', min: 5, max: 60, unit: ' fps' },
          {
            type: 'slider', path: 'engine.confidence', label: 'Confiança mínima', min: 10, max: 95, unit: '%', scale: 100,
            hint: 'Mais alto = menos detecções erradas, mas pode deixar passar alguns pokémons.',
          },
          { type: 'text', path: 'engine.model_path', label: 'Arquivo do modelo', restart: true, wide: true, placeholder: 'models/otp_yolo.pt' },
          {
            type: 'number', path: 'engine.monitor', label: 'Monitor do jogo', min: 0, max: 6,
            hint: '0 = automático (monitor principal do Windows). Os cliques só chegam no monitor principal.',
          },
        ],
      },
      {
        title: 'Comportamento humano',
        status: 'ativo',
        description:
          'Limites de todas as teclas e cliques do bot. Os tempos variam sempre, mudam a cada sessão e ficam um pouco mais lentos com as horas, como uma pessoa.',
        fields: [
          { type: 'slider', path: 'features.human.max_apm', label: 'Máximo de ações por minuto', min: 60, max: 300, unit: ' APM' },
          {
            type: 'number', path: 'features.human.reaction_ms', label: 'Tempo de reação médio', unit: 'ms', min: 160, max: 600, step: 10,
            hint: 'Quanto o bot espera para reagir quando algo novo aparece na tela.',
          },
          {
            type: 'slider', path: 'features.human.cooldown_jitter_pct', label: 'Folga nas recargas', min: 0, max: 30, unit: '%',
            hint: 'O bot nunca usa um golpe no instante exato em que a recarga acaba.',
          },
          { type: 'toggle', path: 'features.human.hesitation', label: 'Hesitar de vez em quando', hint: 'Cerca de 1 em cada 20 reações demora 0,6 a 2,5 s a mais.' },
        ],
      },
    ],
  },
]
