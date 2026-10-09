import { useConfig, useConfigField } from '../context/ConfigContext.jsx'
import { Toggle } from './fields.jsx'
import { Card } from './Section.jsx'
import TelemetryPanel from './TelemetryPanel.jsx'
import LogPanel from './LogPanel.jsx'
import Icon from './Icon.jsx'

const QUICK = [
  { path: 'features.combat.auto_combo', label: 'Combo automático', hint: 'Ataca selvagens com o combo', tab: 'combate' },
  { path: 'features.combat.boxed_defense', label: 'Defesa quando cercado', hint: 'Defesa + combo + revive no lure', tab: 'combate' },
  { path: 'features.catch.enabled', label: 'Captura automática', hint: 'Joga pokébola nos corpos', tab: 'captura' },
  { path: 'features.safety.gm_monitor', label: 'Monitor de GM', hint: 'Desliga o bot se um GM falar', tab: 'seguranca' },
]

function QuickToggle({ item, onNavigate }) {
  const [value, setValue, disabled] = useConfigField(item.path, false)
  return (
    <div className="flex items-center justify-between gap-4 py-3">
      <button type="button" onClick={() => onNavigate(item.tab)} className="group min-w-0 text-left">
        <p className="flex items-center gap-1 text-sm text-base-100 group-hover:text-accent-300">
          {item.label}
          <Icon name="chevron" className="h-3.5 w-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
        </p>
        <p className="text-xs text-base-500">{item.hint}</p>
      </button>
      <Toggle checked={Boolean(value)} onChange={setValue} disabled={disabled} label={item.label} />
    </div>
  )
}

function Notice({ tone, children }) {
  const tones = {
    warn: 'border-amber-500/30 bg-amber-500/10 text-amber-200',
    error: 'border-red-500/30 bg-red-500/10 text-red-200',
  }
  return (
    <div className={`flex items-start gap-3 rounded-xl border px-4 py-3 text-sm ${tones[tone]}`}>
      <Icon name="alert" className="mt-0.5 h-4 w-4 shrink-0" />
      <p className="leading-relaxed">{children}</p>
    </div>
  )
}

export default function OverviewTab({ status, offline, logs, connected, control, onNavigate }) {
  const { config } = useConfig()
  const hotkeys = config?.hotkeys ?? {}
  const modelPath = config?.engine?.model_path ?? 'models/otp_yolo.pt'
  const running = status?.running

  return (
    <div className="space-y-5">
      {offline && <Notice tone="error">Sem conexão com o bot. Ele pode ter sido desligado; abra de novo pelo main.py.</Notice>}
      {!offline && status?.device === 'mock' && (
        <Notice tone="warn">
          Nenhum modelo de visão carregado ({modelPath}). O bot roda, mas ainda não enxerga selvagens nem corpos.
        </Notice>
      )}
      {!offline && status?.device === 'CPU' && (
        <Notice tone="warn">A visão está rodando no processador. Instale o PyTorch com CUDA para usar a placa de vídeo.</Notice>
      )}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card title="Estado do bot">
          <div className="flex items-center gap-5 px-5 py-6">
            <button
              type="button"
              disabled={offline}
              onClick={() => control('toggle')}
              aria-label={running ? 'Pausar' : 'Iniciar'}
              className={`flex h-16 w-16 shrink-0 items-center justify-center rounded-full transition-colors disabled:opacity-40 ${
                running ? 'bg-base-800 text-base-100 hover:bg-base-700' : 'bg-accent-500 text-base-950 hover:bg-accent-400'
              }`}
            >
              <Icon name={running ? 'pause' : 'play'} filled className="h-6 w-6" />
            </button>
            <div>
              <p className="text-lg font-semibold text-base-100">
                {offline ? 'Desconectado' : status.stopping ? 'Desligando…' : running ? 'Rodando' : 'Pausado'}
              </p>
              <p className="mt-1 text-xs leading-relaxed text-base-500">
                Atalhos no jogo: <Kbd>{hotkeys.pause ?? 'f8'}</Kbd> pausa/retoma · <Kbd>{hotkeys.kill ?? 'f9'}</Kbd> desliga
              </p>
            </div>
          </div>
        </Card>

        <Card title="Funções principais">
          <div className="divide-y divide-base-800/70 px-5">
            {QUICK.map((item) => (
              <QuickToggle key={item.path} item={item} onNavigate={onNavigate} />
            ))}
          </div>
        </Card>
      </div>

      <TelemetryPanel status={offline ? null : status} />

      <LogPanel logs={logs} connected={connected} />
    </div>
  )
}

export function Kbd({ children }) {
  return (
    <kbd className="rounded border border-base-700 bg-base-800 px-1.5 py-0.5 font-mono text-[11px] uppercase text-base-200">
      {children}
    </kbd>
  )
}
