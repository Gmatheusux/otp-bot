import { useEffect, useState } from 'react'
import { apiFetch } from '../lib/api.js'
import { useConfig } from '../context/ConfigContext.jsx'
import Section, { Card } from './Section.jsx'
import { Kbd } from './OverviewTab.jsx'
import Icon from './Icon.jsx'

const REFRESH_MS = 2000

function useRoute() {
  const [route, setRoute] = useState({ points: [] })

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const data = await apiFetch('/api/route')
        if (!cancelled) setRoute(data)
      } catch {
        // mantém a última lista; o erro de conexão já aparece no cabeçalho
      }
    }
    load()
    const timer = setInterval(load, REFRESH_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  return route
}

function ActionButton({ icon, children, onClick, active, disabled }) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`flex flex-1 items-center justify-center gap-2 rounded-xl border px-4 py-3 text-sm font-medium transition-colors disabled:opacity-40 ${
        active
          ? 'border-accent-500/60 bg-accent-500/15 text-accent-300'
          : 'border-base-700 bg-base-950 text-base-200 hover:bg-base-800'
      }`}
    >
      <Icon name={icon} filled={icon !== 'record'} className="h-4 w-4" />
      {children}
    </button>
  )
}

export default function RouteTab({ tab, status, offline, control }) {
  const route = useRoute()
  const { config } = useConfig()
  const hotkeys = config?.hotkeys ?? {}
  const recording = status?.cavebot_recording
  const playing = status?.cavebot_playing

  return (
    <div className="grid items-start gap-5 xl:grid-cols-2">
      <div className="space-y-5">
        <Card
          title="Gravar e tocar"
          status="ativo"
          description="O bot repete os cliques que você fez no minimapa, com o mesmo intervalo entre eles."
        >
          <div className="space-y-4 px-5 py-5">
            <ol className="space-y-2 text-sm text-base-300">
              <li>1. Clique em <b className="text-base-100">Gravar</b> (ou <Kbd>{hotkeys.record ?? 'f10'}</Kbd>).</li>
              <li>2. No jogo, clique no minimapa para andar pelo caminho da hunt.</li>
              <li>3. Clique em <b className="text-base-100">Parar gravação</b>.</li>
              <li>4. Clique em <b className="text-base-100">Tocar</b> (ou <Kbd>{hotkeys.play ?? 'f11'}</Kbd>) para o bot repetir em loop.</li>
            </ol>
            <div className="flex gap-3">
              <ActionButton icon={recording ? 'stop' : 'record'} active={recording} disabled={offline || playing} onClick={() => control('record_toggle')}>
                {recording ? 'Parar gravação' : 'Gravar'}
              </ActionButton>
              <ActionButton icon={playing ? 'stop' : 'play'} active={playing} disabled={offline || recording} onClick={() => control('cavebot_toggle')}>
                {playing ? 'Parar rota' : 'Tocar'}
              </ActionButton>
            </div>
          </div>
        </Card>
        {tab.sections.map((section) => (
          <Section key={section.title} section={section} />
        ))}
      </div>

      <Card
        title={`Pontos gravados (${route.points.length})`}
        description="As posições são da tela onde você clicou. Se mover a janela do jogo, grave de novo."
      >
        <div className="scrollbar-thin max-h-[28rem] overflow-y-auto">
          {route.points.length === 0 ? (
            <p className="px-5 py-6 text-sm text-base-500">Nenhuma rota gravada ainda.</p>
          ) : (
            <table className="w-full text-left text-sm">
              <thead className="sticky top-0 bg-base-900 text-[11px] uppercase tracking-wider text-base-500">
                <tr>
                  <th className="px-5 py-2 font-medium">#</th>
                  <th className="px-5 py-2 font-medium">Posição na tela</th>
                  <th className="px-5 py-2 text-right font-medium">Espera</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-base-800/70 font-mono text-base-300">
                {route.points.map((point, i) => (
                  <tr key={i}>
                    <td className="px-5 py-2 text-base-500">{i + 1}</td>
                    <td className="px-5 py-2">{point.x}, {point.y}</td>
                    <td className="px-5 py-2 text-right">{Number(point.delay).toFixed(1)}s</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </div>
  )
}
