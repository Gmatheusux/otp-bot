import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { apiFetch, apiFetchImage } from '../lib/api.js'
import { Card } from './Section.jsx'
import Icon from './Icon.jsx'

// A ordem é o número da classe no YOLO (otpbot/learning/dataset.py CLASSES): não mudar.
const CLASSES = [
  { id: 0, name: 'meu_pokemon', label: 'Meu pokémon', color: '#38bdf8', hint: 'Só o pokémon fora da bola. Nunca o personagem.' },
  { id: 1, name: 'selvagem', label: 'Selvagem', color: '#f87171', hint: 'Selvagem vivo, cor normal.' },
  { id: 2, name: 'selvagem_shiny', label: 'Selvagem shiny', color: '#facc15', hint: 'Selvagem vivo com a cor de shiny.' },
  { id: 3, name: 'corpo', label: 'Corpo', color: '#a3a3a3', hint: 'Corpo de selvagem normal no chão.' },
  { id: 4, name: 'corpo_shiny', label: 'Corpo shiny', color: '#c084fc', hint: 'Corpo com a cor de shiny.' },
]
const CAPTURE_DELAY_S = 3
const MIN_SIDE = 4
const HANDLE_PX = 9

const FILTERS = [
  { id: 'pending', label: 'Para rotular' },
  { id: 'labeled', label: 'Rotuladas' },
  { id: 'all', label: 'Todas' },
]

function useDataset() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)
  const reload = useCallback(async () => {
    try {
      setData(await apiFetch('/api/dataset'))
      setError(null)
    } catch (err) {
      setError(err.message)
    }
  }, [])
  useEffect(() => {
    reload()
  }, [reload])
  return { data, error, reload }
}

function normalize(b) {
  return { ...b, x: Math.min(b.x, b.x + b.w), y: Math.min(b.y, b.y + b.h), w: Math.abs(b.w), h: Math.abs(b.h) }
}

function clampBox(b, size) {
  const x0 = Math.max(0, Math.min(size.w, b.x))
  const y0 = Math.max(0, Math.min(size.h, b.y))
  const x1 = Math.max(0, Math.min(size.w, b.x + b.w))
  const y1 = Math.max(0, Math.min(size.h, b.y + b.h))
  return { ...b, x: x0, y: y0, w: x1 - x0, h: y1 - y0 }
}

function corners(b) {
  return [
    [b.x, b.y],
    [b.x + b.w, b.y],
    [b.x, b.y + b.h],
    [b.x + b.w, b.y + b.h],
  ]
}

function Labeler({ item, position, total, onSaved, onNavigate, onDelete, clipboard, setClipboard }) {
  const [src, setSrc] = useState(null)
  const [size, setSize] = useState(null)
  const [boxes, setBoxes] = useState([])
  const [selected, setSelected] = useState(null)
  const [cls, setCls] = useState(1)
  const [original, setOriginal] = useState('[]') // rótulos como estão no disco
  const [labeled, setLabeled] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [zoom, setZoom] = useState('fit')
  const [fitScale, setFitScale] = useState(1)
  const [draft, setDraft] = useState(null)
  const viewport = useRef(null)
  const surface = useRef(null)
  const drag = useRef(null)

  const scale = zoom === 'fit' ? fitScale : zoom
  // Só conta como alterada se ficou diferente do disco (desenhar e apagar não vira "sem nada")
  const dirty = JSON.stringify(boxes) !== original

  // Carrega imagem + rótulos ao trocar de print
  useEffect(() => {
    let cancelled = false
    let url
    setSrc(null)
    setError(null)
    setSelected(null)
    Promise.all([apiFetchImage(`/api/dataset/${item.id}/image`), apiFetch(`/api/dataset/${item.id}/labels`)])
      .then(([u, labels]) => {
        url = u
        if (cancelled) return
        setSrc(u)
        setSize({ w: labels.width, h: labels.height })
        setBoxes(labels.boxes)
        setOriginal(JSON.stringify(labels.boxes))
        setLabeled(labels.labeled)
      })
      .catch((err) => !cancelled && setError(err.message))
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [item.id])

  // Ajustar à largura do painel
  useEffect(() => {
    if (!viewport.current || !size) return undefined
    const update = () => setFitScale(Math.min(1.5, (viewport.current.clientWidth - 2) / size.w))
    update()
    const observer = new ResizeObserver(update)
    observer.observe(viewport.current)
    return () => observer.disconnect()
  }, [size])

  const change = (next) => setBoxes(next)

  const save = useCallback(async () => {
    setSaving(true)
    setError(null)
    const rounded = boxes.map((b) => ({ cls: b.cls, x: Math.round(b.x), y: Math.round(b.y), w: Math.round(b.w), h: Math.round(b.h) }))
    try {
      const result = await apiFetch(`/api/dataset/${item.id}/labels`, { method: 'PUT', body: JSON.stringify({ boxes: rounded }) })
      setBoxes(result.boxes)
      setOriginal(JSON.stringify(result.boxes))
      setLabeled(true)
      if (rounded.length) setClipboard(rounded)
      onSaved()
      return true
    } catch (err) {
      setError(err.message)
      return false
    } finally {
      setSaving(false)
    }
  }, [boxes, item.id, onSaved, setClipboard])

  const navigate = useCallback(
    async (step) => {
      if (dirty && !(await save())) return
      onNavigate(step)
    },
    [dirty, save, onNavigate],
  )

  const remove = async () => {
    if (!window.confirm('Descartar este print do dataset? (o vídeo de origem não é tocado)')) return
    try {
      await apiFetch(`/api/dataset/${item.id}`, { method: 'DELETE' })
      onDelete()
    } catch (err) {
      setError(err.message)
    }
  }

  // Teclado: 1–5 classe, Del apaga, ←/→ navega (salva antes), S salva, C cola as caixas do último salvo, Esc solta
  useEffect(() => {
    const onKeyDown = (event) => {
      if (event.target.closest?.('input, textarea, select')) return
      const key = event.key.toLowerCase()
      if (key >= '1' && key <= '5') {
        const id = Number(key) - 1
        setCls(id)
        if (selected !== null) change(boxes.map((b, i) => (i === selected ? { ...b, cls: id } : b)))
      } else if ((key === 'delete' || key === 'backspace') && selected !== null) {
        change(boxes.filter((_, i) => i !== selected))
        setSelected(null)
      } else if (key === 'arrowright' || key === 'd') {
        navigate(1)
      } else if (key === 'arrowleft' || key === 'a') {
        navigate(-1)
      } else if (key === 's') {
        save()
      } else if (key === 'c' && clipboard?.length) {
        change([...boxes, ...clipboard.map((b) => ({ ...b }))])
      } else if (key === 'escape') {
        setSelected(null)
      } else {
        return
      }
      event.preventDefault()
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  })

  const toPoint = (event) => {
    const rect = surface.current.getBoundingClientRect()
    return {
      x: Math.min(size.w, Math.max(0, (event.clientX - rect.left) / scale)),
      y: Math.min(size.h, Math.max(0, (event.clientY - rect.top) / scale)),
    }
  }

  const onPointerDown = (event) => {
    if (event.button !== 0) return
    event.preventDefault()
    try {
      surface.current.setPointerCapture(event.pointerId)
    } catch {
      // sem captura o arraste ainda funciona dentro da imagem
    }
    const p = toPoint(event)
    const tolerance = HANDLE_PX / scale
    if (selected !== null) {
      const corner = corners(boxes[selected]).findIndex(([cx, cy]) => Math.abs(cx - p.x) <= tolerance && Math.abs(cy - p.y) <= tolerance)
      if (corner >= 0) {
        const [ox, oy] = corners(boxes[selected])[3 - corner] // canto oposto fica parado
        drag.current = { mode: 'resize', index: selected, ox, oy }
        return
      }
    }
    // Caixa sob o cursor: a selecionada tem preferência, depois a menor (caixas pequenas dentro de grandes)
    const hits = boxes
      .map((b, i) => ({ b, i }))
      .filter(({ b }) => p.x >= b.x && p.x <= b.x + b.w && p.y >= b.y && p.y <= b.y + b.h)
      .sort((a, b) => (a.i === selected ? -1 : b.i === selected ? 1 : a.b.w * a.b.h - b.b.w * b.b.h))
    if (hits.length && !event.shiftKey) {
      const { b, i } = hits[0]
      setSelected(i)
      setCls(b.cls)
      drag.current = { mode: 'move', index: i, dx: p.x - b.x, dy: p.y - b.y, moved: false }
      return
    }
    setSelected(null)
    drag.current = { mode: 'draw', sx: p.x, sy: p.y }
    setDraft({ cls, x: p.x, y: p.y, w: 0, h: 0 })
  }

  const onPointerMove = (event) => {
    const d = drag.current
    if (!d) return
    const p = toPoint(event)
    if (d.mode === 'draw') {
      setDraft(normalize({ cls, x: d.sx, y: d.sy, w: p.x - d.sx, h: p.y - d.sy }))
    } else if (d.mode === 'move') {
      const b = boxes[d.index]
      const x = Math.max(0, Math.min(size.w - b.w, p.x - d.dx))
      const y = Math.max(0, Math.min(size.h - b.h, p.y - d.dy))
      d.moved = true
      setBoxes(boxes.map((bb, i) => (i === d.index ? { ...bb, x, y } : bb)))
    } else if (d.mode === 'resize') {
      const b = boxes[d.index]
      setBoxes(boxes.map((bb, i) => (i === d.index ? normalize({ ...b, x: d.ox, y: d.oy, w: p.x - d.ox, h: p.y - d.oy }) : bb)))
    }
  }

  const onPointerUp = () => {
    const d = drag.current
    drag.current = null
    if (d?.mode === 'draw' && draft) {
      if (draft.w >= MIN_SIDE && draft.h >= MIN_SIDE) {
        change([...boxes, clampBox(draft, size)])
        setSelected(boxes.length)
      }
      setDraft(null)
    }
  }

  const shown = draft ? [...boxes, draft] : boxes
  const counts = CLASSES.map((c) => boxes.filter((b) => b.cls === c.id).length)

  return (
    <Card>
      <div className="flex flex-wrap items-center gap-2 border-b border-base-800 px-4 py-3">
        <div className="inline-flex flex-wrap gap-1">
          {CLASSES.map((c, i) => (
            <button
              key={c.id}
              type="button"
              title={c.hint}
              onClick={() => {
                setCls(c.id)
                if (selected !== null) change(boxes.map((b, j) => (j === selected ? { ...b, cls: c.id } : b)))
              }}
              className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs transition-colors ${
                cls === c.id ? 'border-base-500 bg-base-800 text-base-100' : 'border-base-800 text-base-400 hover:bg-base-850'
              }`}
            >
              <span className="h-2.5 w-2.5 rounded-sm" style={{ background: c.color }} />
              <span className="font-mono text-[10px] text-base-500">{i + 1}</span>
              {c.label}
              {counts[i] > 0 && <span className="font-mono text-[10px] text-base-400">×{counts[i]}</span>}
            </button>
          ))}
        </div>
        <div className="ml-auto inline-flex gap-1 rounded-lg border border-base-800 bg-base-950 p-1">
          {['fit', 0.5, 1, 2].map((z) => (
            <button
              key={z}
              type="button"
              onClick={() => setZoom(z)}
              className={`rounded-md px-2 py-0.5 font-mono text-[11px] ${z === zoom ? 'bg-accent-500/15 text-accent-300' : 'text-base-400 hover:bg-base-800'}`}
            >
              {z === 'fit' ? 'ajustar' : `${z * 100}%`}
            </button>
          ))}
        </div>
      </div>

      <div ref={viewport} className="scrollbar-thin max-h-[68vh] overflow-auto bg-base-950">
        {src && size ? (
          <div
            ref={surface}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={onPointerUp}
            className="relative cursor-crosshair touch-none select-none"
            style={{ width: size.w * scale, height: size.h * scale }}
          >
            <img src={src} alt={item.id} draggable={false} className="absolute inset-0 h-full w-full" style={{ imageRendering: scale >= 2 ? 'pixelated' : 'auto' }} />
            {shown.map((b, i) => {
              const color = CLASSES[b.cls]?.color ?? '#fff'
              const isSel = i === selected && b !== draft
              return (
                <div
                  key={i}
                  className="pointer-events-none absolute"
                  style={{
                    left: b.x * scale,
                    top: b.y * scale,
                    width: b.w * scale,
                    height: b.h * scale,
                    border: `${isSel ? 2 : 1.5}px ${b === draft ? 'dashed' : 'solid'} ${color}`,
                    background: isSel ? `${color}22` : 'transparent',
                  }}
                >
                  <span className="absolute -top-4 left-0 whitespace-nowrap px-1 text-[10px] font-medium leading-4 text-base-950" style={{ background: color }}>
                    {CLASSES[b.cls]?.name}
                  </span>
                  {isSel &&
                    corners({ x: 0, y: 0, w: b.w * scale, h: b.h * scale }).map(([cx, cy], k) => (
                      <span key={k} className="absolute h-2 w-2 border border-base-950" style={{ left: cx - 5, top: cy - 5, background: color }} />
                    ))}
                </div>
              )
            })}
          </div>
        ) : (
          <p className="px-4 py-16 text-center text-sm text-base-500">{error ?? 'Carregando…'}</p>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3 border-t border-base-800 px-4 py-3">
        <button type="button" onClick={() => navigate(-1)} className="rounded-lg border border-base-700 px-3 py-1.5 text-xs text-base-200 hover:bg-base-800" title="Anterior (← ou A)">
          ← Anterior
        </button>
        <span className="font-mono text-[11px] text-base-500">
          {position + 1}/{total}
        </span>
        <button type="button" onClick={() => navigate(1)} className="rounded-lg border border-base-700 px-3 py-1.5 text-xs text-base-200 hover:bg-base-800" title="Próxima (→ ou D); salva antes">
          Próxima →
        </button>
        <span className="min-w-0 truncate text-[11px] text-base-500" title={item.id}>
          {item.id} · {item.profile ?? '?'} · {labeled ? (dirty ? 'alterada, não salva' : `salva (${item.split === 'val' ? 'validação' : 'treino'})`) : dirty ? 'não salva' : 'ainda não revisada'}
        </span>
        <div className="ml-auto flex items-center gap-2">
          {error && src && <span className="text-xs text-red-400">{error}</span>}
          <button type="button" onClick={remove} className="rounded-lg p-2 text-base-500 hover:bg-red-500/10 hover:text-red-300" title="Descartar print (ruim, repetido, tela de loading…)">
            <Icon name="trash" className="h-4 w-4" />
          </button>
          <button
            type="button"
            onClick={save}
            disabled={saving}
            className="rounded-lg bg-accent-500 px-4 py-1.5 text-sm font-medium text-base-950 hover:bg-accent-400 disabled:opacity-50"
            title="Salvar (S)"
          >
            {saving ? 'Salvando…' : boxes.length ? `Salvar ${boxes.length} caixa${boxes.length > 1 ? 's' : ''}` : 'Salvar como "sem nada"'}
          </button>
        </div>
      </div>
    </Card>
  )
}

function CollectCard({ data, reload }) {
  const [countdown, setCountdown] = useState(0)
  const [message, setMessage] = useState(null)
  const [interval, setIntervalS] = useState(data?.auto?.interval_s ?? 10)
  const auto = data?.auto ?? { enabled: false }

  const capture = async () => {
    setMessage(null)
    setCountdown(CAPTURE_DELAY_S)
    const timer = setInterval(() => setCountdown((s) => Math.max(0, s - 1)), 1000)
    try {
      const r = await apiFetch('/api/dataset/capture', { method: 'POST', body: JSON.stringify({ delay_s: CAPTURE_DELAY_S }) })
      setMessage({ ok: true, text: `Print guardado: ${r.id}` })
      reload()
    } catch (err) {
      setMessage({ ok: false, text: err.message })
    } finally {
      clearInterval(timer)
      setCountdown(0)
    }
  }

  const setAuto = async (enabled) => {
    try {
      await apiFetch('/api/dataset/auto', { method: 'POST', body: JSON.stringify({ enabled, interval_s: Number(interval) || 10 }) })
      reload()
    } catch (err) {
      setMessage({ ok: false, text: err.message })
    }
  }

  return (
    <Card title="Coletar prints" description="Só lê a tela: nenhuma tecla é enviada ao jogo. O jogo precisa estar visível, sem janela por cima. Guarda só a área do jogo.">
      <div className="space-y-3 px-5 py-4">
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={capture}
            disabled={countdown > 0}
            className="inline-flex items-center gap-2 rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-base-950 hover:bg-accent-400 disabled:opacity-70"
          >
            <Icon name="camera" className="h-4 w-4" />
            {countdown > 0 ? `Mude para o jogo… ${countdown}` : `Capturar agora (${CAPTURE_DELAY_S}s)`}
          </button>
        </div>
        <div className="flex flex-wrap items-center gap-3 rounded-lg border border-base-800 px-3 py-2.5">
          <span className="text-xs text-base-300">Captura automática a cada</span>
          <input
            type="number"
            min={2}
            max={600}
            value={interval}
            onChange={(e) => setIntervalS(e.target.value)}
            className="w-16 rounded-md border border-base-700 bg-base-950 px-2 py-1 text-xs text-base-100"
          />
          <span className="text-xs text-base-400">s</span>
          <button
            type="button"
            onClick={() => setAuto(!auto.enabled)}
            className={`ml-auto rounded-lg px-3 py-1.5 text-xs font-medium ${auto.enabled ? 'bg-red-500/15 text-red-300 hover:bg-red-500/25' : 'border border-base-700 text-base-200 hover:bg-base-800'}`}
          >
            {auto.enabled ? 'Parar' : 'Ligar'}
          </button>
        </div>
        <p className="text-[11px] text-base-500">
          {auto.enabled ? 'Ligada. ' : ''}
          {auto.saved ?? 0} guardados · {auto.skipped ?? 0} repetidos pulados
          {auto.last_error ? ` · ${auto.last_error}` : ''}
        </p>
        {message && <p className={`text-xs ${message.ok ? 'text-emerald-300' : 'text-red-400'}`}>{message.text}</p>}
      </div>
    </Card>
  )
}

function StatsCard({ stats }) {
  if (!stats) return null
  return (
    <Card title="Dataset" description={stats.root}>
      <div className="grid grid-cols-3 gap-2 px-5 pt-4 text-center">
        {[
          ['para rotular', stats.images.pending],
          ['treino', stats.images.train],
          ['validação', stats.images.val],
        ].map(([label, value]) => (
          <div key={label} className="rounded-lg border border-base-800 py-2">
            <p className="font-mono text-lg text-base-100">{value}</p>
            <p className="text-[11px] text-base-500">{label}</p>
          </div>
        ))}
      </div>
      <ul className="space-y-1 px-5 py-4">
        {CLASSES.map((c) => (
          <li key={c.id} className="flex items-center gap-2 text-xs">
            <span className="h-2.5 w-2.5 rounded-sm" style={{ background: c.color }} />
            <span className="text-base-300">{c.name}</span>
            <span className="ml-auto font-mono text-base-400">{stats.boxes[c.name]}</span>
          </li>
        ))}
      </ul>
    </Card>
  )
}

export default function VisionTab() {
  const { data, error, reload } = useDataset()
  const [filter, setFilter] = useState('pending')
  const [currentId, setCurrentId] = useState(null)
  const [clipboard, setClipboard] = useState(null)
  const autoOn = data?.auto?.enabled

  useEffect(() => {
    if (!autoOn) return undefined
    const timer = setInterval(reload, 5000)
    return () => clearInterval(timer)
  }, [autoOn, reload])

  const images = useMemo(() => data?.images ?? [], [data])
  const visible = useMemo(
    () => images.filter((e) => filter === 'all' || (filter === 'pending' ? !e.labeled : e.labeled)),
    [images, filter],
  )
  const current = images.find((e) => e.id === currentId) ?? null
  const position = visible.findIndex((e) => e.id === currentId)

  // Abre o primeiro da lista quando não há nenhum aberto
  useEffect(() => {
    if (!current && visible.length) setCurrentId(visible[0].id)
  }, [current, visible])

  const navigate = (step) => {
    if (!visible.length) return
    const index = position < 0 ? 0 : Math.min(visible.length - 1, Math.max(0, position + step))
    setCurrentId(visible[index].id)
  }

  const afterDelete = () => {
    const next = visible[position + 1] ?? visible[position - 1]
    setCurrentId(next ? next.id : null)
    reload()
  }

  return (
    <div className="space-y-5">
      <div className="grid items-start gap-5 lg:grid-cols-2">
        <CollectCard data={data} reload={reload} />
        <StatsCard stats={data?.stats} />
      </div>

      <Card>
        <div className="px-5 py-3 text-xs leading-relaxed text-base-400">
          <b className="text-base-200">Como rotular:</b> escolha a classe (teclas <b>1–5</b>) e arraste uma caixa justa em volta de cada
          pokémon (do contorno do sprite, sem o nome nem a barra de vida). Clique numa caixa para selecionar; arraste para mover, puxe
          os cantos para ajustar, <b>Del</b> apaga, um número troca a classe dela. <b>Shift</b> + arrastar desenha por cima de outra
          caixa. <b>→</b>/<b>D</b> salva e vai para a próxima, <b>←</b>/<b>A</b> volta, <b>S</b> salva, <b>C</b> cola as caixas do
          último print salvo. Print sem nenhum pokémon: salve vazio (vira exemplo de &quot;sem nada&quot;). Print ruim ou repetido:
          lixeira.
        </div>
      </Card>

      {error && <p className="text-sm text-red-400">Não foi possível carregar o dataset ({error}).</p>}

      <div className="flex flex-wrap items-center gap-3">
        <div className="inline-flex gap-1 rounded-lg border border-base-800 bg-base-950 p-1">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              onClick={() => setFilter(f.id)}
              className={`rounded-md px-3 py-1 text-xs ${f.id === filter ? 'bg-accent-500/15 text-accent-300' : 'text-base-400 hover:bg-base-800'}`}
            >
              {f.label}
            </button>
          ))}
        </div>
        <select
          value={currentId ?? ''}
          onChange={(e) => setCurrentId(e.target.value)}
          className="min-w-0 max-w-md flex-1 rounded-lg border border-base-700 bg-base-950 px-3 py-1.5 text-xs text-base-200"
        >
          {visible.map((e) => (
            <option key={e.id} value={e.id}>
              {e.id} {e.labeled ? `· ${e.boxes} caixa${e.boxes === 1 ? '' : 's'}` : ''}
            </option>
          ))}
        </select>
        <span className="text-[11px] text-base-500">{visible.length} na lista</span>
      </div>

      {current ? (
        <Labeler
          key={current.id}
          item={current}
          position={position}
          total={visible.length}
          onSaved={reload}
          onNavigate={navigate}
          onDelete={afterDelete}
          clipboard={clipboard}
          setClipboard={setClipboard}
        />
      ) : (
        <p className="rounded-lg border border-dashed border-base-700 px-4 py-10 text-center text-sm text-base-500">
          {filter === 'pending' ? 'Nenhum print para rotular. Capture prints do jogo ou extraia frames de um vídeo.' : 'Nenhum print nesta lista.'}
        </p>
      )}
    </div>
  )
}
