import { Card } from './Section.jsx'

export const STANCE_LABELS = { offensive: 'Ofensivo', neutral: 'Neutro', defensive: 'Defensivo' }
const STANCE_TONES = {
  offensive: 'border-red-500/40 bg-red-500/10 text-red-300',
  neutral: 'border-base-600 bg-base-800 text-base-200',
  defensive: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-300',
}

function Meter({ label, value, color }) {
  const missing = value === null || value === undefined
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between gap-3">
        <span className="text-xs text-base-300">{label}</span>
        <span className={`font-mono text-xs ${missing ? 'text-base-600' : 'text-base-100'}`}>
          {missing ? 'não encontrado' : `${Math.round(value)}%`}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-base-800">
        <div
          className="h-full rounded-full transition-[width] duration-500"
          style={{ width: `${missing ? 0 : Math.max(0, Math.min(100, value))}%`, backgroundColor: color }}
        />
      </div>
    </div>
  )
}

/** Barras que o bot está lendo da tela (vem de status.readings ou de um teste). */
export default function ReadingsPanel({ readings, title = 'O que o bot está lendo da tela', description }) {
  const team = Array.isArray(readings?.team) ? readings.team : []
  const stance = readings?.stance
  return (
    <Card title={title} description={description}>
      <div className="grid gap-5 px-5 py-4 sm:grid-cols-2">
        <div className="space-y-3">
          <Meter label="HP do jogador" value={readings?.player_hp} color="#ef4444" />
          <Meter label="HP do pokémon" value={readings?.pokemon_hp} color="#3b82f6" />
          <Meter label="EXP" value={readings?.exp_bar} color="#eab308" />
          <div className="flex items-center justify-between gap-3">
            <span className="text-xs text-base-300">Postura</span>
            {stance ? (
              <span className={`rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${STANCE_TONES[stance]}`}>
                {STANCE_LABELS[stance]}
              </span>
            ) : (
              <span className="font-mono text-xs text-base-600">não encontrado</span>
            )}
          </div>
        </div>
        <div className="space-y-3">
          {team.length === 0 ? (
            <p className="text-xs text-base-500">Time: sem leitura ainda.</p>
          ) : (
            team.map((value, i) => <Meter key={i} label={`Pokémon ${i + 1} do time`} value={value} color="#22c55e" />)
          )}
        </div>
      </div>
    </Card>
  )
}
