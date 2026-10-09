import { useState } from 'react'
import { apiFetch } from '../lib/api.js'
import { useBotStatus } from '../hooks/useBotStatus.js'
import Icon from './Icon.jsx'

const DELAY_S = 3
const ACTIONS = [
  { id: 'healer', label: 'Chamar o curador' },
  { id: 'farm', label: 'Chamar o de farm' },
  { id: 'full', label: 'Rodar a cura completa' },
]

/** Botões para conferir no jogo se a troca e a rotação estão certas. */
export default function HealTestPanel() {
  const { status } = useBotStatus()
  const [countdown, setCountdown] = useState(0)
  const [error, setError] = useState(null)
  const step = status?.heal_routine ?? 'parado'

  const run = async (action) => {
    setError(null)
    try {
      await apiFetch('/api/heal/test', { method: 'POST', body: JSON.stringify({ action, delay_s: DELAY_S }) })
      setCountdown(DELAY_S)
      const timer = setInterval(() => {
        setCountdown((s) => {
          if (s <= 1) clearInterval(timer)
          return Math.max(0, s - 1)
        })
      }, 1000)
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <div className="rounded-b-2xl border-t border-base-800 bg-base-950/40 px-5 py-4">
      <div className="mb-3 flex items-center justify-between gap-3">
        <p className="text-xs text-base-400">
          Testar no jogo: clique e volte para o jogo em {DELAY_S}s. Funciona com o bot pausado.
        </p>
        <span className="shrink-0 text-xs text-base-500">
          Agora: <span className={step === 'parado' ? 'text-base-300' : 'text-accent-300'}>{step}</span>
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {ACTIONS.map((action) => (
          <button
            key={action.id}
            type="button"
            disabled={countdown > 0 || step !== 'parado'}
            onClick={() => run(action.id)}
            className="inline-flex items-center gap-1.5 rounded-lg border border-base-700 px-3 py-1.5 text-xs text-base-200 transition-colors hover:bg-base-800 disabled:opacity-50"
          >
            <Icon name="play" filled className="h-3 w-3" />
            {action.label}
          </button>
        ))}
        {countdown > 0 && <span className="self-center text-xs text-accent-300">Mude para o jogo… {countdown}</span>}
      </div>
      {error && <p className="mt-2 text-xs text-red-400">{error}</p>}
    </div>
  )
}
