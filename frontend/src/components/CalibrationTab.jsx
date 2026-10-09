import { useEffect, useRef, useState } from 'react'
import { apiFetch, apiFetchImage } from '../lib/api.js'
import { useConfig } from '../context/ConfigContext.jsx'
import { Card, StatusBadge } from './Section.jsx'
import { Field } from './fields.jsx'
import ReadingsPanel, { STANCE_LABELS } from './ReadingsPanel.jsx'
import Icon from './Icon.jsx'

const CAPTURE_DELAY_S = 3

const REGIONS = [
  { id: 'player_hp', label: 'HP do jogador', hint: 'Barra vermelha do painel Pokémon (ex: 5560 / 5560).', color: '#ef4444', group: 'bars' },
  { id: 'pokemon_hp', label: 'HP do pokémon', hint: 'Barra azul do painel Pokémon (ex: 47459 / 47949).', color: '#3b82f6', group: 'bars' },
  { id: 'stance', label: 'Postura (mãos)', hint: 'As 3 mãos: vermelha ofensivo, cinza neutro, verde defensivo. Cubra as três.', color: '#f472b6', group: 'bars' },
  { id: 'exp_bar', label: 'Barra de EXP', hint: 'Barra amarela inteira, do começo até o fim do trilho.', color: '#eab308', group: 'bars' },
  { id: 'team', label: 'Seus pokémons (Pokébar)', hint: 'Cubra só as barras verdes de vida, de cima a baixo. Ajuste a quantidade abaixo.', color: '#38bdf8', group: 'bars' },
  { id: 'game_area', label: 'Área do jogo', hint: 'Onde a IA procura selvagens, corpos e o seu pokémon.', color: '#f97316', group: 'areas' },
  { id: 'battle_list', label: 'Lista Batalha', hint: 'Nomes e vidas de quem está em combate.', color: '#a855f7', group: 'areas' },
  { id: 'skills', label: 'Golpes do pokémon', hint: 'Barra roxa de golpes; serve para saber quando estão em recarga.', color: '#ec4899', group: 'areas' },
  { id: 'hotbar', label: 'Hotbar (F1–F12)', hint: 'Itens e quantidades na barra de atalhos.', color: '#f43f5e', group: 'areas' },
  { id: 'minimap', label: 'Minimapa', hint: 'Mapa pequeno no canto.', color: '#14b8a6', group: 'areas' },
  { id: 'coords', label: 'Coordenadas', hint: 'Texto "x, y, z" acima do minimapa.', color: '#06b6d4', group: 'areas' },
  { id: 'chat', label: 'Chat', hint: 'Últimas linhas do chat.', color: '#94a3b8', group: 'areas' },
]

function formatReading(region, readings) {
  if (!readings || !(region.id in readings)) return null
  const value = readings[region.id]
  if (region.id === 'stance') return value ? STANCE_LABELS[value] : 'não encontrado'
  if (Array.isArray(value)) return value.map((v) => (v === null ? '—' : Math.round(v))).join(' · ') + '%'
  return value === null ? 'não encontrado' : `${Math.round(value)}%`
}

function useReferenceImage(profileKey, version) {
  const [image, setImage] = useState(null) // { src, w, h }
  const [error, setError] = useState(null)

  useEffect(() => {
    if (!profileKey) return
    let url
    let cancelled = false
    setImage(null)
    setError(null)
    apiFetchImage(`/api/calibration/reference/${profileKey}`)
      .then((u) => {
        url = u
        const img = new Image()
        img.onload = () => !cancelled && setImage({ src: u, w: img.naturalWidth, h: img.naturalHeight })
        img.src = u
      })
      .catch((err) => !cancelled && setError(err))
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [profileKey, version])

  return { image, error }
}

function CalibrationCanvas({ image, baseWidth, regions, selected, onSelect, onCommit }) {
  const viewport = useRef(null)
  const surface = useRef(null)
  const start = useRef(null)
  const [fitWidth, setFitWidth] = useState(0)
  const [zoomMode, setZoomMode] = useState('fit')
  const [draft, setDraft] = useState(null)

  useEffect(() => {
    const el = viewport.current
    if (!el) return
    setFitWidth(el.clientWidth) // medida inicial: o observer só dispara quando a página desenha
    const observer = new ResizeObserver(() => setFitWidth(el.clientWidth))
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  // Regiões estão em pixels da referência (baseWidth); a imagem pode ter outra largura
  const toImage = image.w / baseWidth
  const zoom = zoomMode === 'fit' ? (fitWidth || image.w) / image.w : zoomMode
  const f = toImage * zoom

  const toBase = (event) => {
    const rect = surface.current.getBoundingClientRect()
    return {
      x: Math.max(0, Math.min(baseWidth, Math.round((event.clientX - rect.left) / f))),
      y: Math.max(0, Math.min(image.h / toImage, Math.round((event.clientY - rect.top) / f))),
    }
  }

  const onPointerDown = (event) => {
    if (!selected) return
    event.preventDefault()
    try {
      surface.current.setPointerCapture(event.pointerId) // continua o arraste mesmo saindo da imagem
    } catch {
      // ponteiro inválido (ex: evento sintético): o arraste funciona sem a captura
    }
    start.current = toBase(event)
    setDraft({ ...start.current, w: 0, h: 0 })
  }
  const onPointerMove = (event) => {
    if (!start.current) return
    const p = toBase(event)
    const s = start.current
    setDraft({ x: Math.min(s.x, p.x), y: Math.min(s.y, p.y), w: Math.abs(p.x - s.x), h: Math.abs(p.y - s.y) })
  }
  const onPointerUp = () => {
    if (start.current && draft && draft.w >= 3 && draft.h >= 3) onCommit(selected, draft)
    start.current = null
    setDraft(null)
  }

  return (
    <div>
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-base-400">
          {selected
            ? <>Arraste na imagem para redesenhar <b className="text-base-200">{REGIONS.find((r) => r.id === selected)?.label}</b>.</>
            : 'Escolha uma região na lista para redesenhar.'}
        </p>
        <div className="inline-flex gap-1 rounded-lg border border-base-800 bg-base-950 p-1">
          {['fit', 1, 2, 3].map((z) => (
            <button
              key={z}
              type="button"
              onClick={() => setZoomMode(z)}
              className={`rounded-md px-2.5 py-1 font-mono text-[11px] ${
                z === zoomMode ? 'bg-accent-500/15 text-accent-300' : 'text-base-400 hover:bg-base-800'
              }`}
            >
              {z === 'fit' ? 'Ajustar' : `${z * 100}%`}
            </button>
          ))}
        </div>
      </div>
      <div ref={viewport} className="scrollbar-thin max-h-[62vh] overflow-auto rounded-xl border border-base-800 bg-base-950">
        <div
          ref={surface}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          className={`relative touch-none select-none ${selected ? 'cursor-crosshair' : ''}`}
          style={{ width: image.w * zoom, height: image.h * zoom }}
        >
          <img src={image.src} alt="Tela de referência do jogo" draggable={false} className="absolute inset-0 h-full w-full" />
          {REGIONS.map((meta) => {
            const r = draft && meta.id === selected ? draft : regions[meta.id]
            if (!r) return null
            const active = meta.id === selected
            return (
              <div
                key={meta.id}
                className="pointer-events-none absolute"
                style={{
                  left: r.x * f,
                  top: r.y * f,
                  width: r.w * f,
                  height: r.h * f,
                  border: `${active ? 2 : 1}px solid ${meta.color}`,
                  backgroundColor: active ? `${meta.color}33` : 'transparent',
                  opacity: selected && !active ? 0.45 : 1,
                }}
              >
                <button
                  type="button"
                  onPointerDown={(e) => e.stopPropagation()}
                  onClick={() => onSelect(meta.id)}
                  className="pointer-events-auto absolute -top-4 left-0 whitespace-nowrap rounded px-1 text-[9px] font-semibold leading-4 text-black"
                  style={{ backgroundColor: meta.color }}
                >
                  {meta.label}
                </button>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function RegionList({ group, regions, selected, onSelect, readings }) {
  return (
    <ul className="divide-y divide-base-800/70">
      {REGIONS.filter((r) => r.group === group).map((meta) => {
        const active = meta.id === selected
        const reading = formatReading(meta, readings)
        const r = regions[meta.id]
        return (
          <li key={meta.id}>
            <button
              type="button"
              onClick={() => onSelect(active ? null : meta.id)}
              className={`flex w-full items-start gap-3 px-5 py-3 text-left transition-colors ${active ? 'bg-base-800/60' : 'hover:bg-base-850'}`}
            >
              <span className="mt-1 h-3 w-3 shrink-0 rounded-sm" style={{ backgroundColor: meta.color }} />
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline justify-between gap-3">
                  <span className="text-sm text-base-100">{meta.label}</span>
                  {reading && <span className="shrink-0 font-mono text-xs text-base-200">{reading}</span>}
                </span>
                <span className="block text-xs leading-relaxed text-base-500">{meta.hint}</span>
                {r ? (
                  <span className="mt-0.5 block font-mono text-[10px] text-base-600">
                    x {r.x} · y {r.y} · {r.w}×{r.h}
                  </span>
                ) : (
                  <span className="mt-0.5 block text-[10px] text-amber-300/80">não marcada nesta resolução: selecione e desenhe</span>
                )}
              </span>
            </button>
          </li>
        )
      })}
    </ul>
  )
}

export default function CalibrationTab({ status }) {
  const { config, setValue, reload } = useConfig()
  const calibration = config?.calibration
  const profiles = calibration?.profiles ?? {}
  const profileKeys = Object.keys(profiles).sort((a, b) => profiles[b].width - profiles[a].width)
  const liveProfile = status?.readings?.profile

  const [chosenProfile, setChosenProfile] = useState(null)
  // Sem escolha manual, mostra o perfil que o bot está usando agora na tela
  const profileKey = chosenProfile ?? (profiles[liveProfile] ? liveProfile : profileKeys[0])
  const profile = profiles[profileKey]
  const regions = profile?.regions ?? {}

  const [version, setVersion] = useState(0)
  const { image, error: imageError } = useReferenceImage(profileKey, version)
  const [selected, setSelected] = useState(null)
  const [testResult, setTestResult] = useState(null)
  const [busy, setBusy] = useState(null) // 'reference' | 'capture'
  const [countdown, setCountdown] = useState(0)
  const [error, setError] = useState(null)

  const chooseProfile = (key) => {
    setChosenProfile(key)
    setTestResult(null)
    setSelected(null)
  }

  const commitRegion = (id, rect) => {
    setValue(`calibration.profiles.${profileKey}.regions.${id}`, { ...regions[id], ...rect })
    setTestResult(null)
  }

  const withCountdown = async (seconds, task) => {
    setCountdown(seconds)
    const timer = setInterval(() => setCountdown((s) => Math.max(0, s - 1)), 1000)
    try {
      return await task()
    } finally {
      clearInterval(timer)
      setCountdown(0)
    }
  }

  const testReference = async () => {
    setBusy('reference')
    setError(null)
    try {
      setTestResult(
        await apiFetch('/api/calibration/test', { method: 'POST', body: JSON.stringify({ source: 'reference', profile: profileKey }) }),
      )
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  const newReference = async () => {
    setBusy('capture')
    setError(null)
    try {
      const result = await withCountdown(CAPTURE_DELAY_S, () =>
        apiFetch('/api/calibration/reference', { method: 'POST', body: JSON.stringify({ delay_s: CAPTURE_DELAY_S }) }),
      )
      await reload()
      // O print vai para o perfil da resolução atual da tela
      setChosenProfile(result.profile)
      setVersion((v) => v + 1)
      setTestResult(null)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(null)
    }
  }

  if (!calibration) return <p className="text-sm text-base-500">Carregando calibração…</p>

  // A leitura ao vivo só faz sentido no perfil que a tela está usando
  const liveMatches = liveProfile === profileKey
  const shownReadings = testResult?.readings ?? (liveMatches ? status?.readings : null)

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4 px-5 py-4">
          <div className="max-w-2xl">
            <h3 className="text-sm font-semibold text-base-100">Onde fica cada coisa na sua tela</h3>
            <p className="mt-1 text-xs leading-relaxed text-base-400">
              A interface do jogo tem o mesmo tamanho em qualquer monitor, então cada resolução tem suas próprias regiões. O
              bot escolhe sozinho pelo tamanho da tela. Para corrigir, clique numa região e arraste na imagem.
            </p>
            <div className="mt-3 inline-flex flex-wrap gap-1 rounded-lg border border-base-800 bg-base-950 p-1">
              {profileKeys.map((key) => (
                <button
                  key={key}
                  type="button"
                  onClick={() => chooseProfile(key)}
                  className={`inline-flex items-center gap-2 rounded-md px-3 py-1.5 font-mono text-xs transition-colors ${
                    key === profileKey ? 'bg-accent-500/15 text-accent-300' : 'text-base-400 hover:bg-base-800 hover:text-base-200'
                  }`}
                >
                  {key.replace('x', ' × ')}
                  {key === liveProfile && (
                    <span className="rounded bg-emerald-500/15 px-1.5 py-0.5 font-sans text-[10px] text-emerald-300">em uso</span>
                  )}
                </button>
              ))}
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={testReference}
              disabled={Boolean(busy)}
              className="inline-flex items-center gap-2 rounded-lg border border-base-700 px-3.5 py-2 text-sm text-base-200 hover:bg-base-800 disabled:opacity-50"
            >
              <Icon name="search" className="h-4 w-4" />
              {busy === 'reference' ? 'Lendo…' : 'Ler na imagem'}
            </button>
            <button
              type="button"
              onClick={newReference}
              disabled={Boolean(busy)}
              className="inline-flex items-center gap-2 rounded-lg bg-accent-500 px-3.5 py-2 text-sm font-medium text-base-950 hover:bg-accent-400 disabled:opacity-70"
            >
              <Icon name="camera" className="h-4 w-4" />
              {busy === 'capture' ? `Mude para o jogo… ${countdown}` : `Usar print atual (${CAPTURE_DELAY_S}s)`}
            </button>
          </div>
        </div>
        {error && <p className="border-t border-base-800 px-5 py-3 text-sm text-red-400">{error}</p>}
      </Card>

      <div className="grid items-start gap-5 2xl:grid-cols-[minmax(0,1fr)_22rem]">
        {/* min-w-0: sem isso o grid cresce até a largura da imagem (2000px) e o "Ajustar" não encaixa */}
        <div className="min-w-0">
        <Card>
          <div className="p-4">
            {image ? (
              <CalibrationCanvas
                image={image}
                baseWidth={profile?.width || image.w}
                regions={regions}
                selected={selected}
                onSelect={setSelected}
                onCommit={commitRegion}
              />
            ) : (
              <p className="px-1 py-10 text-center text-sm text-base-500">
                {imageError
                  ? `Sem imagem de referência para ${profileKey}. Coloque o jogo nessa resolução e clique em "Usar print atual".`
                  : 'Carregando imagem…'}
              </p>
            )}
          </div>
        </Card>
        </div>

        <div className="space-y-5">
          <Card title="Barras" status="ativo" description="O bot já lê estas barras pela cor, 2 vezes por segundo.">
            <RegionList group="bars" regions={regions} selected={selected} onSelect={setSelected} readings={shownReadings} />
            <div className="border-t border-base-800 px-5">
              <Field
                field={{ type: 'number', path: `calibration.profiles.${profileKey}.regions.team.slots`, label: 'Pokémons na Pokébar', min: 1, max: 6 }}
              />
              <Field field={{ type: 'text', path: 'calibration.summon_name', label: 'Seu pokémon', hint: 'Nome que aparece em cima dele no jogo.' }} />
            </div>
          </Card>
          <Card title="Áreas" status="planejado" description="Marcadas para as próximas funções (IA, coordenadas, golpes, itens).">
            <RegionList group="areas" regions={regions} selected={selected} onSelect={setSelected} readings={null} />
          </Card>
        </div>
      </div>

      <ReadingsPanel
        readings={shownReadings}
        title={testResult ? `Leitura na imagem de referência (${profileKey})` : 'Leitura ao vivo da sua tela'}
        description={
          testResult
            ? 'Resultado do botão "Ler na imagem". Mude qualquer região para voltar à leitura ao vivo.'
            : liveMatches
              ? 'Com o jogo aberto na tela, estes valores acompanham o jogo em tempo real.'
              : `Sua tela agora está em ${liveProfile ?? '—'}; a leitura ao vivo aparece no perfil dessa resolução.`
        }
      />
      <p className="flex items-center gap-2 text-xs text-base-500">
        <StatusBadge status="planejado" /> Usar essas leituras para curar e reviver sozinho vem na próxima etapa.
      </p>
    </div>
  )
}
