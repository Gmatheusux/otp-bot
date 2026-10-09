import { Card } from './Section.jsx'

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
  return (
    <Card title={title} description={description}>
      <div className="grid gap-5 px-5 py-4 sm:grid-cols-2">
        <div className="space-y-3">
          <Meter label="HP do jogador" value={readings?.player_hp} color="#22c55e" />
          <Meter label="HP do pokémon" value={readings?.pokemon_hp} color="#10b981" />
          <Meter label="EXP" value={readings?.exp_bar} color="#eab308" />
        </div>
        <div className="space-y-3">
          {team.length === 0 ? (
            <p className="text-xs text-base-500">Time: sem leitura ainda.</p>
          ) : (
            team.map((value, i) => <Meter key={i} label={`Pokémon ${i + 1} do time`} value={value} color="#38bdf8" />)
          )}
        </div>
      </div>
    </Card>
  )
}
