import { useState } from 'react'
import { ConfigProvider, useConfig } from './context/ConfigContext.jsx'
import { useBotStatus } from './hooks/useBotStatus.js'
import { useBotLogs } from './hooks/useBotLogs.js'
import { TABS } from './schema/features.js'
import Section from './components/Section.jsx'
import OverviewTab from './components/OverviewTab.jsx'
import RouteTab from './components/RouteTab.jsx'
import Icon from './components/Icon.jsx'

const TAB_KEY = 'otp-active-tab'

function readSavedTab() {
  try {
    const saved = localStorage.getItem(TAB_KEY)
    return TABS.some((t) => t.id === saved) ? saved : 'inicio'
  } catch {
    return 'inicio'
  }
}

function StatusPill({ status, offline }) {
  const state = offline
    ? { label: 'Desconectado', dot: 'bg-base-600', text: 'text-base-400' }
    : status.stopping
      ? { label: 'Desligando', dot: 'bg-red-400', text: 'text-red-300' }
      : status.running
        ? { label: 'Rodando', dot: 'bg-emerald-400 animate-pulse', text: 'text-emerald-300' }
        : { label: 'Pausado', dot: 'bg-amber-400', text: 'text-amber-300' }
  return (
    <span className={`inline-flex items-center gap-2 text-xs font-medium ${state.text}`}>
      <span className={`h-2 w-2 rounded-full ${state.dot}`} />
      {state.label}
    </span>
  )
}

function SaveIndicator() {
  const { saveState, loading, error } = useConfig()
  if (loading) return <span className="text-xs text-base-500">Carregando…</span>
  if (saveState === 'saving') return <span className="text-xs text-base-400">Salvando…</span>
  if (saveState === 'error' || (error && saveState !== 'saved'))
    return <span className="text-xs text-red-400">Erro ao salvar</span>
  if (saveState === 'saved')
    return (
      <span className="inline-flex items-center gap-1 text-xs text-emerald-400">
        <Icon name="check" className="h-3.5 w-3.5" /> Salvo
      </span>
    )
  return <span className="text-xs text-base-500">Alterações salvam sozinhas</span>
}

function Sidebar({ active, onSelect, status, offline }) {
  return (
    <nav className="flex w-16 shrink-0 flex-col border-r border-base-800 bg-base-900 md:w-56">
      <div className="flex h-16 items-center gap-3 border-b border-base-800 px-4">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-500 text-base-950">
          <Icon name="ball" className="h-5 w-5" />
        </div>
        <div className="hidden md:block">
          <p className="text-sm font-semibold leading-tight text-base-100">OTP Bot</p>
          <StatusPill status={status} offline={offline} />
        </div>
      </div>
      <ul className="scrollbar-thin flex-1 space-y-0.5 overflow-y-auto p-2">
        {TABS.map((tab) => {
          const selected = tab.id === active
          return (
            <li key={tab.id}>
              <button
                type="button"
                title={tab.label}
                onClick={() => onSelect(tab.id)}
                className={`relative flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition-colors ${
                  selected ? 'bg-base-800 text-base-100' : 'text-base-400 hover:bg-base-850 hover:text-base-200'
                }`}
              >
                {selected && <span className="absolute inset-y-2 left-0 w-0.5 rounded-full bg-accent-500" />}
                <Icon name={tab.icon} className={`h-[18px] w-[18px] shrink-0 ${selected ? 'text-accent-400' : ''}`} />
                <span className="hidden md:inline">{tab.label}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}

function Footer({ status, offline, connected }) {
  const item = (label, value) => (
    <span>
      <span className="text-base-600">{label}</span> <span className="font-mono text-base-300">{value}</span>
    </span>
  )
  return (
    <footer className="flex h-9 shrink-0 items-center gap-5 overflow-hidden whitespace-nowrap border-t border-base-800 bg-base-900 px-5 text-xs">
      <StatusPill status={status} offline={offline} />
      {!offline && (
        <>
          {item('visão', status.device)}
          {item('fps', status.fps.toFixed(1))}
          {item('mobs', status.mobs_on_screen)}
          {item('sessão', `${Math.floor(status.uptime_s / 60)}m`)}
        </>
      )}
      <span className="ml-auto text-base-600">log {connected ? 'ao vivo' : 'desconectado'}</span>
    </footer>
  )
}

function Console() {
  const [active, setActive] = useState(readSavedTab)
  const { status, error: statusError, control } = useBotStatus()
  const { logs, connected } = useBotLogs()
  const offline = !status || Boolean(statusError)
  const tab = TABS.find((t) => t.id === active)
  const running = status?.running

  const select = (id) => {
    setActive(id)
    try {
      localStorage.setItem(TAB_KEY, id)
    } catch {
      // sem storage: só não lembra a aba
    }
  }

  const handleStop = () => {
    if (window.confirm('Desligar o bot? A janela será fechada.')) control('stop')
  }

  let content
  if (tab.custom === 'overview') {
    content = <OverviewTab status={status} offline={offline} logs={logs} connected={connected} control={control} onNavigate={select} />
  } else if (tab.custom === 'route') {
    content = <RouteTab tab={tab} status={status} offline={offline} control={control} />
  } else {
    content = (
      <div className="grid items-start gap-5 xl:grid-cols-2">
        {tab.sections.map((section) => (
          <Section key={section.title} section={section} />
        ))}
      </div>
    )
  }

  return (
    <div className="flex h-full">
      <Sidebar active={active} onSelect={select} status={status} offline={offline} />
      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-4 border-b border-base-800 px-6">
          <div className="min-w-0">
            <h1 className="text-base font-semibold text-base-100">{tab.label}</h1>
            <p className="truncate text-xs text-base-500">{tab.description}</p>
          </div>
          <div className="flex shrink-0 items-center gap-3">
            <SaveIndicator />
            <button
              type="button"
              disabled={offline}
              onClick={() => control('toggle')}
              className={`inline-flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-40 ${
                running ? 'bg-base-800 text-base-100 hover:bg-base-700' : 'bg-accent-500 text-base-950 hover:bg-accent-400'
              }`}
            >
              <Icon name={running ? 'pause' : 'play'} filled className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{running ? 'Pausar' : 'Iniciar'}</span>
            </button>
            <button
              type="button"
              disabled={offline}
              onClick={handleStop}
              aria-label="Desligar o bot"
              title="Desligar o bot"
              className="rounded-lg border border-base-700 p-2 text-base-400 transition-colors hover:border-red-500/40 hover:bg-red-500/10 hover:text-red-300 disabled:opacity-40"
            >
              <Icon name="power" className="h-4 w-4" />
            </button>
          </div>
        </header>
        <div className="scrollbar-thin flex-1 overflow-y-auto p-6">
          <div className="mx-auto max-w-6xl">{content}</div>
        </div>
        <Footer status={status} offline={offline} connected={connected} />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <ConfigProvider>
      <Console />
    </ConfigProvider>
  )
}
