function Stat({ label, value, tone = 'text-base-200' }) {
  return (
    <div className="rounded-xl border border-base-800 bg-base-900/60 px-4 py-3">
      <p className="text-xs font-medium uppercase tracking-wider text-base-500">{label}</p>
      <p className={`mt-1 truncate font-mono text-sm ${tone}`}>{value}</p>
    </div>
  )
}

function formatUptime(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  const s = seconds % 60
  return h > 0 ? `${h}h ${m}m` : `${m}m ${String(s).padStart(2, '0')}s`
}

export default function TelemetryPanel({ status }) {
  const device = status?.device ?? '—'
  const deviceTone = device === 'mock' || device === 'CPU' ? 'text-accent-400' : 'text-emerald-400'

  return (
    <div className="grid w-full grid-cols-2 gap-3 sm:grid-cols-3">
      <Stat label="Visão" value={device} tone={deviceTone} />
      <Stat label="Modelo" value={status?.model ?? 'nenhum'} />
      <Stat label="FPS" value={status ? status.fps.toFixed(1) : '—'} />
      <Stat label="Detecções" value={status?.detections ?? '—'} />
      <Stat
        label="Mobs"
        value={status ? `${status.mobs_on_screen}${status.is_boxed ? ' · BOXED' : ''}` : '—'}
        tone={status?.is_boxed ? 'text-red-400' : 'text-base-200'}
      />
      <Stat label="Sessão" value={status ? formatUptime(status.uptime_s) : '—'} />
    </div>
  )
}
