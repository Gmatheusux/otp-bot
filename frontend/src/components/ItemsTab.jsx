import { useCallback, useEffect, useRef, useState } from 'react'
import { apiFetch, apiFetchImage } from '../lib/api.js'
import { Card, StatusBadge } from './Section.jsx'
import { KeyPicker, Segmented } from './fields.jsx'
import Icon from './Icon.jsx'

const CATEGORIES = [
  { id: 'potion', label: 'Poções', hint: 'Poções de vida do jogador.' },
  { id: 'antidote', label: 'Antídotos', hint: 'Curam veneno, paralisia e outros status.' },
  { id: 'revive', label: 'Revive', hint: 'Revivem o pokémon desmaiado.' },
  { id: 'buff', label: 'Buffs', hint: 'Itens de bônus: XP, Shiny Charm, ataque…' },
  { id: 'ball', label: 'Pokébolas', hint: 'Bolas usadas na captura.' },
  { id: 'other', label: 'Outros', hint: 'Qualquer outro item que o bot precise achar.' },
]
const CATEGORY_OPTIONS = CATEGORIES.map((c) => ({ value: c.id, label: c.label }))
const CAPTURE_DELAY_S = 3
const MIN_SIDE = 6

const checkerboard = {
  backgroundColor: '#1d1f24',
  backgroundImage:
    'linear-gradient(45deg,#2a2d33 25%,transparent 25%,transparent 75%,#2a2d33 75%),linear-gradient(45deg,#2a2d33 25%,transparent 25%,transparent 75%,#2a2d33 75%)',
  backgroundSize: '8px 8px',
  backgroundPosition: '0 0,4px 4px',
}

function useSprites() {
  const [sprites, setSprites] = useState([])
  const [error, setError] = useState(null)

  const reload = useCallback(async () => {
    try {
      const data = await apiFetch('/api/sprites')
      setSprites(data.sprites)
      setError(null)
    } catch (err) {
      setError(err)
    }
  }, [])

  useEffect(() => {
    reload()
  }, [reload])

  return { sprites, error, reload }
}

/** Conta regressiva enquanto o servidor espera para tirar o print. */
function useCountdown() {
  const [left, setLeft] = useState(0)
  const timer = useRef(null)

  const run = useCallback(async (seconds, task) => {
    setLeft(seconds)
    clearInterval(timer.current)
    timer.current = setInterval(() => setLeft((s) => Math.max(0, s - 1)), 1000)
    try {
      return await task()
    } finally {
      clearInterval(timer.current)
      setLeft(0)
    }
  }, [])

  useEffect(() => () => clearInterval(timer.current), [])
  return [left, run]
}

function SpriteThumb({ sprite, size = 44 }) {
  const [src, setSrc] = useState(null)

  useEffect(() => {
    let url
    let cancelled = false
    apiFetchImage(`/api/sprites/${sprite.id}/image`)
      .then((u) => {
        url = u
        if (!cancelled) setSrc(u)
      })
      .catch(() => {})
    return () => {
      cancelled = true
      if (url) URL.revokeObjectURL(url)
    }
  }, [sprite.id])

  return (
    <div
      className="flex shrink-0 items-center justify-center overflow-hidden rounded-lg border border-base-700"
      style={{ ...checkerboard, width: size, height: size }}
    >
      {src && (
        <img
          src={src}
          alt={sprite.name}
          className="max-h-full max-w-full"
          style={{ imageRendering: 'pixelated', width: Math.min(size - 6, sprite.width * 1.5) }}
        />
      )}
    </div>
  )
}

function SpriteRow({ sprite, onChanged }) {
  const [name, setName] = useState(sprite.name)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [countdown, runCountdown] = useCountdown()
  const testing = countdown > 0

  const patch = async (fields) => {
    try {
      await apiFetch(`/api/sprites/${sprite.id}`, { method: 'PATCH', body: JSON.stringify(fields) })
      setError(null)
      onChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  const test = async () => {
    setResult(null)
    setError(null)
    try {
      const data = await runCountdown(CAPTURE_DELAY_S, () =>
        apiFetch(`/api/sprites/${sprite.id}/test`, { method: 'POST', body: JSON.stringify({ delay_s: CAPTURE_DELAY_S }) }),
      )
      setResult(data)
    } catch (err) {
      setError(err.message)
    }
  }

  const remove = async () => {
    if (!window.confirm(`Remover "${sprite.name}"?`)) return
    try {
      await apiFetch(`/api/sprites/${sprite.id}`, { method: 'DELETE' })
      onChanged()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <li className="py-3">
      <div className="flex items-center gap-3">
        <SpriteThumb sprite={sprite} />
        <div className="min-w-0 flex-1">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={() => name.trim() && name !== sprite.name && patch({ name: name.trim() })}
            className="w-full rounded-md border border-transparent bg-transparent px-1.5 py-0.5 text-sm text-base-100 hover:border-base-700 focus:border-accent-500 focus:outline-none"
            aria-label="Nome do item"
          />
          <p className="px-1.5 text-[11px] text-base-500">
            {sprite.width}×{sprite.height} px · reconhece com {Math.round(sprite.threshold * 100)}% de semelhança
          </p>
        </div>
        <KeyPicker value={sprite.key} onChange={(key) => patch({ key })} />
        <button
          type="button"
          onClick={test}
          disabled={testing}
          title="Tira um print e procura o item"
          className="inline-flex items-center gap-1.5 rounded-lg border border-base-700 px-3 py-1.5 text-xs text-base-200 transition-colors hover:bg-base-800 disabled:opacity-60"
        >
          <Icon name="search" className="h-3.5 w-3.5" />
          {testing ? `Mude para o jogo… ${countdown}` : 'Testar'}
        </button>
        <button
          type="button"
          onClick={remove}
          aria-label={`Remover ${sprite.name}`}
          className="rounded-lg p-2 text-base-500 transition-colors hover:bg-red-500/10 hover:text-red-300"
        >
          <Icon name="trash" className="h-4 w-4" />
        </button>
      </div>
      {result && (
        <p className={`mt-2 pl-[56px] text-xs ${result.found ? 'text-emerald-300' : 'text-amber-300'}`}>
          {result.found
            ? `Encontrado ${result.matches.length}× na tela (melhor semelhança ${Math.round(result.best_score * 100)}%).`
            : `Não encontrado. Melhor semelhança ${Math.round(result.best_score * 100)}% (precisa de ${Math.round(sprite.threshold * 100)}%). Deixe o item visível na tela e teste de novo.`}
        </p>
      )}
      {error && <p className="mt-2 pl-[56px] text-xs text-red-400">{error}</p>}
    </li>
  )
}

function RegionSelector({ src, size, region, onChange }) {
  // Monitores largos (ex: 3440px) abrem afastados para caber; o jogador aproxima para recortar
  const [zoom, setZoom] = useState(size.w > 1600 ? 0.5 : 1)
  const surface = useRef(null)
  const start = useRef(null)

  const toPoint = (event) => {
    const rect = surface.current.getBoundingClientRect()
    return {
      x: Math.min(size.w, Math.max(0, Math.round((event.clientX - rect.left) / zoom))),
      y: Math.min(size.h, Math.max(0, Math.round((event.clientY - rect.top) / zoom))),
    }
  }

  const onPointerDown = (event) => {
    event.preventDefault()
    surface.current.setPointerCapture(event.pointerId)
    start.current = toPoint(event)
    onChange({ ...start.current, w: 0, h: 0 })
  }
  const onPointerMove = (event) => {
    if (!start.current) return
    const p = toPoint(event)
    const s = start.current
    onChange({ x: Math.min(s.x, p.x), y: Math.min(s.y, p.y), w: Math.abs(p.x - s.x), h: Math.abs(p.y - s.y) })
  }
  const onPointerUp = () => {
    start.current = null
  }

  return (
    <div>
      <div className="mb-2 flex items-center justify-between">
        <p className="text-xs text-base-400">Arraste um retângulo em volta do item. Use o zoom para acertar.</p>
        <div className="inline-flex gap-1 rounded-lg border border-base-800 bg-base-950 p-1">
          {[0.5, 1, 2, 3].map((z) => (
            <button
              key={z}
              type="button"
              onClick={() => setZoom(z)}
              className={`rounded-md px-2.5 py-1 font-mono text-[11px] ${
                z === zoom ? 'bg-accent-500/15 text-accent-300' : 'text-base-400 hover:bg-base-800'
              }`}
            >
              {z * 100}%
            </button>
          ))}
        </div>
      </div>
      <div className="scrollbar-thin max-h-[52vh] overflow-auto rounded-lg border border-base-800 bg-base-950">
        <div
          ref={surface}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          className="relative cursor-crosshair touch-none select-none"
          style={{ width: size.w * zoom, height: size.h * zoom }}
        >
          <img
            src={src}
            alt="Print da tela"
            draggable={false}
            className="absolute inset-0 h-full w-full"
            style={{ imageRendering: zoom > 1 ? 'pixelated' : 'auto' }}
          />
          {region && region.w > 0 && (
            <div
              className="pointer-events-none absolute border-2 border-accent-400 bg-accent-400/10"
              style={{ left: region.x * zoom, top: region.y * zoom, width: region.w * zoom, height: region.h * zoom }}
            />
          )}
        </div>
      </div>
    </div>
  )
}

function CropPreview({ image, region }) {
  const canvas = useRef(null)
  const valid = image && region && region.w >= 1 && region.h >= 1
  const scale = valid ? Math.max(1, Math.floor(96 / Math.max(region.w, region.h))) : 1

  useEffect(() => {
    if (!valid || !canvas.current) return
    const ctx = canvas.current.getContext('2d')
    ctx.imageSmoothingEnabled = false
    ctx.clearRect(0, 0, canvas.current.width, canvas.current.height)
    ctx.drawImage(image, region.x, region.y, region.w, region.h, 0, 0, region.w * scale, region.h * scale)
  }, [image, region, scale, valid])

  return (
    <div className="flex h-28 w-28 items-center justify-center rounded-lg border border-base-700" style={checkerboard}>
      {valid ? (
        <canvas ref={canvas} width={region.w * scale} height={region.h * scale} />
      ) : (
        <span className="px-2 text-center text-[11px] text-base-500">prévia do recorte</span>
      )}
    </div>
  )
}

function AddSpriteModal({ initialCategory, onClose, onSaved }) {
  const [shot, setShot] = useState(null) // { src, image, size }
  const [upload, setUpload] = useState(null) // { src, base64 }
  const [region, setRegion] = useState(null)
  const [name, setName] = useState('')
  const [category, setCategory] = useState(initialCategory)
  const [key, setKey] = useState('')
  const [error, setError] = useState(null)
  const [saving, setSaving] = useState(false)
  const [countdown, runCountdown] = useCountdown()
  const fileInput = useRef(null)

  useEffect(() => {
    const onKeyDown = (event) => event.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [onClose])

  useEffect(() => () => shot && URL.revokeObjectURL(shot.src), [shot])

  const capture = async () => {
    setError(null)
    try {
      const src = await runCountdown(CAPTURE_DELAY_S, () =>
        apiFetchImage('/api/screenshot', { method: 'POST', body: JSON.stringify({ delay_s: CAPTURE_DELAY_S }) }),
      )
      const image = new Image()
      image.onload = () => {
        setUpload(null)
        setRegion(null)
        setShot({ src, image, size: { w: image.naturalWidth, h: image.naturalHeight } })
      }
      image.src = src
    } catch (err) {
      setError(err.message)
    }
  }

  const pickFile = (event) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file) return
    const reader = new FileReader()
    reader.onload = () => {
      setShot(null)
      setRegion(null)
      setUpload({ src: reader.result, base64: reader.result })
      if (!name) setName(file.name.replace(/\.[^.]+$/, ''))
    }
    reader.readAsDataURL(file)
  }

  const regionOk = region && region.w >= MIN_SIDE && region.h >= MIN_SIDE
  const canSave = name.trim() && (upload || (shot && regionOk)) && !saving

  const save = async () => {
    setSaving(true)
    setError(null)
    const body = { name: name.trim(), category, key }
    if (upload) body.image_base64 = upload.base64
    else body.region = [region.x, region.y, region.w, region.h]
    try {
      await apiFetch('/api/sprites', { method: 'POST', body: JSON.stringify(body) })
      onSaved()
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-6"
      onMouseDown={(e) => e.target === e.currentTarget && onClose()}
    >
      <div role="dialog" aria-label="Adicionar sprite" className="flex max-h-full w-full max-w-5xl flex-col rounded-2xl border border-base-700 bg-base-900 shadow-panel">
        <header className="flex items-center justify-between border-b border-base-800 px-5 py-4">
          <div>
            <h2 className="text-sm font-semibold text-base-100">Adicionar sprite</h2>
            <p className="mt-0.5 text-xs text-base-400">Tire um print do jogo e recorte o item, ou envie a imagem do item.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Fechar" className="rounded-lg p-2 text-base-400 hover:bg-base-800">
            <Icon name="x" className="h-4 w-4" />
          </button>
        </header>

        <div className="scrollbar-thin flex-1 space-y-5 overflow-y-auto px-5 py-5">
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={capture}
              disabled={countdown > 0}
              className="inline-flex items-center gap-2 rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-base-950 transition-colors hover:bg-accent-400 disabled:opacity-70"
            >
              <Icon name="camera" className="h-4 w-4" />
              {countdown > 0 ? `Mude para o jogo… ${countdown}` : shot ? 'Tirar outro print' : `Tirar print da tela (${CAPTURE_DELAY_S}s)`}
            </button>
            <button
              type="button"
              onClick={() => fileInput.current?.click()}
              className="inline-flex items-center gap-2 rounded-lg border border-base-700 px-4 py-2 text-sm text-base-200 hover:bg-base-800"
            >
              <Icon name="upload" className="h-4 w-4" />
              Enviar imagem
            </button>
            <input ref={fileInput} type="file" accept="image/png,image/jpeg,image/gif,image/bmp" className="hidden" onChange={pickFile} />
          </div>

          {!shot && !upload && (
            <p className="rounded-lg border border-dashed border-base-700 px-4 py-8 text-center text-sm text-base-500">
              Deixe o item visível no jogo (mochila ou hotbar), clique em <b className="text-base-300">Tirar print</b> e volte
              para o jogo em até {CAPTURE_DELAY_S} segundos.
            </p>
          )}

          {shot && <RegionSelector src={shot.src} size={shot.size} region={region} onChange={setRegion} />}

          {(shot || upload) && (
            <div className="flex flex-wrap items-start gap-6">
              {upload ? (
                <div className="flex h-28 w-28 items-center justify-center rounded-lg border border-base-700" style={checkerboard}>
                  <img src={upload.src} alt="Imagem enviada" className="h-24 w-24 object-contain" style={{ imageRendering: 'pixelated' }} />
                </div>
              ) : (
                <div>
                  <CropPreview image={shot.image} region={region} />
                  <p className="mt-1 text-center font-mono text-[11px] text-base-500">
                    {region ? `${region.w}×${region.h}` : '—'}
                  </p>
                </div>
              )}

              <div className="min-w-[18rem] flex-1 space-y-4">
                <label className="block">
                  <span className="mb-1 block text-xs text-base-400">Nome do item</span>
                  <input
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="ex: Ultra Potion"
                    className="w-full rounded-lg border border-base-700 bg-base-950 px-3 py-2 text-sm text-base-100 placeholder:text-base-600 focus:border-accent-500 focus:outline-none"
                  />
                </label>
                <div>
                  <span className="mb-1 block text-xs text-base-400">Categoria</span>
                  <Segmented value={category} onChange={setCategory} options={CATEGORY_OPTIONS} />
                </div>
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <span className="block text-xs text-base-400">Tecla no jogo (opcional)</span>
                    <span className="text-[11px] text-base-500">A hotkey que usa este item.</span>
                  </div>
                  <KeyPicker value={key} onChange={setKey} />
                </div>
                {shot && region && !regionOk && region.w > 0 && (
                  <p className="text-xs text-amber-300">O recorte precisa ter pelo menos {MIN_SIDE}×{MIN_SIDE} pixels.</p>
                )}
              </div>
            </div>
          )}

          {error && <p className="text-sm text-red-400">{error}</p>}
        </div>

        <footer className="flex items-center justify-between gap-4 border-t border-base-800 px-5 py-4">
          <p className="text-xs text-base-500">Dica: recorte só o desenho do item, sem o número de quantidade.</p>
          <div className="flex gap-2">
            <button type="button" onClick={onClose} className="rounded-lg px-4 py-2 text-sm text-base-300 hover:bg-base-800">
              Cancelar
            </button>
            <button
              type="button"
              onClick={save}
              disabled={!canSave}
              className="rounded-lg bg-accent-500 px-4 py-2 text-sm font-medium text-base-950 transition-colors hover:bg-accent-400 disabled:opacity-40"
            >
              {saving ? 'Salvando…' : 'Salvar sprite'}
            </button>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default function ItemsTab() {
  const { sprites, error, reload } = useSprites()
  const [adding, setAdding] = useState(null) // categoria do modal aberto

  return (
    <div className="space-y-5">
      <Card>
        <div className="flex flex-wrap items-start justify-between gap-4 px-5 py-4">
          <div className="max-w-2xl">
            <h3 className="text-sm font-semibold text-base-100">Como funciona</h3>
            <p className="mt-1 text-xs leading-relaxed text-base-400">
              Você recorta a imagem de cada item direto da tela do jogo. O bot passa a procurar essa imagem na tela para saber
              onde o item está e se ele ainda existe. Use <b className="text-base-300">Testar</b> para conferir se o bot está
              enxergando.
            </p>
            <ul className="mt-2 space-y-0.5 text-xs text-base-500">
              <li>• Recorte só o desenho do item, sem o número de quantidade (ele muda e atrapalha).</li>
              <li>• Mantenha o mesmo zoom/tamanho da janela do jogo de quando recortou.</li>
            </ul>
          </div>
          <div className="flex flex-col items-end gap-1.5">
            <span className="flex items-center gap-2 text-[11px] text-base-500">
              Reconhecimento <StatusBadge status="ativo" />
            </span>
            <span className="flex items-center gap-2 text-[11px] text-base-500">
              Uso automático <StatusBadge status="planejado" />
            </span>
          </div>
        </div>
      </Card>

      {error && <p className="text-sm text-red-400">Não foi possível carregar os sprites ({error.message}).</p>}

      <div className="grid items-start gap-5 xl:grid-cols-2">
        {CATEGORIES.map((category) => {
          const items = sprites.filter((s) => s.category === category.id)
          return (
            <Card key={category.id} title={`${category.label} (${items.length})`} description={category.hint}>
              <div className="px-5">
                {items.length > 0 && (
                  <ul className="divide-y divide-base-800/70">
                    {items.map((sprite) => (
                      <SpriteRow key={sprite.id} sprite={sprite} onChanged={reload} />
                    ))}
                  </ul>
                )}
                <button
                  type="button"
                  onClick={() => setAdding(category.id)}
                  className={`my-3 flex w-full items-center justify-center gap-2 rounded-lg border border-dashed border-base-700 py-2.5 text-sm text-base-400 transition-colors hover:border-accent-500/50 hover:text-accent-300 ${
                    items.length > 0 ? '' : 'mt-4'
                  }`}
                >
                  <Icon name="plus" className="h-4 w-4" />
                  Adicionar {category.label.toLowerCase()}
                </button>
              </div>
            </Card>
          )
        })}
      </div>

      {adding && <AddSpriteModal initialCategory={adding} onClose={() => setAdding(null)} onSaved={reload} />}
    </div>
  )
}
