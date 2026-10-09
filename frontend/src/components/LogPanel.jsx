import { useEffect, useRef } from 'react'
import { Card } from './Section.jsx'

const LEVEL_TONE = {
  WARNING: 'text-amber-300',
  ERROR: 'text-red-400',
  CRITICAL: 'text-red-400',
}

export default function LogPanel({ logs, connected }) {
  const listRef = useRef(null)

  // Acompanha o fim do log enquanto chegam eventos novos
  useEffect(() => {
    const el = listRef.current
    if (el) el.scrollTop = el.scrollHeight
  }, [logs])

  return (
    <Card>
      <div className="flex items-center justify-between border-b border-base-800 px-5 py-3">
        <h3 className="text-sm font-semibold text-base-100">O que o bot está fazendo</h3>
        <span className={`flex items-center gap-1.5 text-xs ${connected ? 'text-emerald-400' : 'text-base-500'}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${connected ? 'bg-emerald-400' : 'bg-base-600'}`} />
          {connected ? 'ao vivo' : 'desconectado'}
        </span>
      </div>
      <div ref={listRef} className="scrollbar-thin h-72 overflow-y-auto px-5 py-3">
        {logs.length === 0 ? (
          <p className="text-sm text-base-500">Sem eventos ainda.</p>
        ) : (
          <ul className="space-y-1.5">
            {logs.map((entry) => (
              <li key={entry.id} className="flex gap-3 text-[13px] leading-relaxed">
                <span className="shrink-0 font-mono text-xs leading-relaxed text-base-600">{entry.time}</span>
                <span className={LEVEL_TONE[entry.level] ?? 'text-base-300'}>{entry.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  )
}
