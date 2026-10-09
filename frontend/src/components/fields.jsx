import { useEffect, useRef, useState } from 'react'
import { useConfigField } from '../context/ConfigContext.jsx'
import Icon from './Icon.jsx'

const inputBase =
  'rounded-lg border border-base-700 bg-base-950 px-2.5 py-1.5 text-sm text-base-100 transition-colors ' +
  'placeholder:text-base-600 focus:border-accent-500 focus:outline-none disabled:opacity-40'

export function Toggle({ checked, onChange, disabled = false, label }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => onChange(!checked)}
      className={`relative inline-flex h-6 w-11 shrink-0 items-center rounded-full transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-accent-400/60 disabled:opacity-40 ${
        checked ? 'bg-accent-500' : 'bg-base-700'
      }`}
    >
      <span
        className={`inline-block h-5 w-5 rounded-full bg-white shadow transition-transform duration-200 ${
          checked ? 'translate-x-[22px]' : 'translate-x-0.5'
        }`}
      />
    </button>
  )
}

function clamp(n, min, max) {
  return Math.min(max ?? Infinity, Math.max(min ?? -Infinity, n))
}

/** Mantém o texto digitado enquanto o campo está em foco; só grava números válidos. */
function NumberInput({ value, onChange, min, max, step = 1, unit, disabled }) {
  const [draft, setDraft] = useState(String(value ?? ''))
  const [focused, setFocused] = useState(false)

  useEffect(() => {
    if (!focused) setDraft(String(value ?? ''))
  }, [value, focused])

  const handleChange = (event) => {
    const raw = event.target.value
    setDraft(raw)
    const n = Number(raw)
    if (raw !== '' && !Number.isNaN(n) && n === clamp(n, min, max)) onChange(n)
  }

  const handleBlur = () => {
    setFocused(false)
    const n = Number(draft)
    if (draft !== '' && !Number.isNaN(n)) onChange(clamp(n, min, max))
  }

  return (
    <div className="flex items-center gap-2">
      <input
        type="number"
        inputMode="decimal"
        value={draft}
        min={min}
        max={max}
        step={step}
        disabled={disabled}
        onFocus={() => setFocused(true)}
        onBlur={handleBlur}
        onChange={handleChange}
        className={`${inputBase} w-20 text-right font-mono`}
      />
      {unit && <span className="w-8 text-xs text-base-500">{unit}</span>}
    </div>
  )
}

function Slider({ value, onChange, min, max, step = 1, unit = '', scale = 1, disabled }) {
  const shown = Math.round(value * scale * 100) / 100
  return (
    <div className="flex w-56 items-center gap-3">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={shown}
        disabled={disabled}
        onChange={(event) => onChange(Number(event.target.value) / scale)}
        className="h-1.5 flex-1 cursor-pointer accent-accent-500 disabled:opacity-40"
      />
      <span className="w-14 text-right font-mono text-sm text-base-200">
        {shown}
        {unit}
      </span>
    </div>
  )
}

function TextInput({ value, onChange, placeholder, disabled, wide = false }) {
  return (
    <input
      type="text"
      value={value ?? ''}
      placeholder={placeholder}
      disabled={disabled}
      onChange={(event) => onChange(event.target.value)}
      className={`${inputBase} ${wide ? 'w-64' : 'w-44'}`}
    />
  )
}

export function Segmented({ value, onChange, options, disabled, columns }) {
  return (
    <div
      className={columns ? 'grid gap-1.5' : 'inline-flex flex-wrap gap-1 rounded-lg border border-base-800 bg-base-950 p-1'}
      style={columns ? { gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))` } : undefined}
    >
      {options.map((option) => {
        const active = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            disabled={disabled}
            onClick={() => onChange(option.value)}
            className={`rounded-md px-3 py-1.5 text-xs font-medium transition-colors disabled:opacity-40 ${
              columns ? 'border' : ''
            } ${
              active
                ? 'border-accent-500/60 bg-accent-500/15 text-accent-300'
                : 'border-base-800 text-base-400 hover:bg-base-800 hover:text-base-200'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}

function Tags({ value, onChange, placeholder, disabled }) {
  const [draft, setDraft] = useState('')
  const items = Array.isArray(value) ? value : []

  const add = () => {
    const item = draft.trim()
    if (item && !items.includes(item)) onChange([...items, item])
    setDraft('')
  }

  return (
    <div className="flex flex-wrap items-center gap-1.5 rounded-lg border border-base-700 bg-base-950 p-1.5">
      {items.map((item) => (
        <span key={item} className="inline-flex items-center gap-1 rounded-md bg-base-800 py-1 pl-2.5 pr-1 text-xs text-base-200">
          {item}
          <button
            type="button"
            aria-label={`Remover ${item}`}
            disabled={disabled}
            onClick={() => onChange(items.filter((i) => i !== item))}
            className="rounded p-0.5 text-base-500 hover:bg-base-700 hover:text-base-200"
          >
            <Icon name="x" className="h-3 w-3" />
          </button>
        </span>
      ))}
      <input
        type="text"
        value={draft}
        disabled={disabled}
        placeholder={placeholder ?? 'Digite e aperte Enter'}
        onChange={(event) => setDraft(event.target.value)}
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            event.preventDefault()
            add()
          }
        }}
        onBlur={add}
        className="min-w-[10rem] flex-1 bg-transparent px-1.5 py-1 text-sm text-base-100 placeholder:text-base-600 focus:outline-none"
      />
    </div>
  )
}

const KEY_NAMES = {
  ' ': 'space', Escape: 'esc', Enter: 'enter', Tab: 'tab', Backspace: 'backspace', Delete: 'delete',
  Insert: 'insert', Home: 'home', End: 'end', PageUp: 'page up', PageDown: 'page down',
  ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right',
}
const MODIFIERS = ['Control', 'Shift', 'Alt', 'Meta']

/** Converte o evento do navegador para o nome que a lib `keyboard` do Python entende. */
function toKeyName(event) {
  if (MODIFIERS.includes(event.key)) return null
  let name
  if (/^F\d{1,2}$/.test(event.key)) name = event.key.toLowerCase()
  else if (/^Numpad\d$/.test(event.code)) name = `num ${event.code.slice(6)}`
  else if (event.key.length === 1) name = event.key.toLowerCase()
  else name = KEY_NAMES[event.key]
  if (!name) return null
  const mods = [event.ctrlKey && 'ctrl', event.altKey && 'alt', event.shiftKey && name.length > 1 && 'shift'].filter(Boolean)
  return [...mods, name].join('+')
}

const range = (n) => Array.from({ length: n }, (_, i) => i + 1)
const KEY_GROUPS = [
  { label: 'Teclas F', keys: range(12).map((i) => `f${i}`) },
  { label: 'Ctrl + F', keys: range(12).map((i) => `ctrl+f${i}`) },
  { label: 'Shift + F', keys: range(12).map((i) => `shift+f${i}`) },
  { label: 'Números', keys: [...range(9).map(String), '0'] },
]

function keyLabel(key) {
  return key.split('+').map((part) => part.toUpperCase()).join(' + ')
}

/** Escolha a tecla numa lista ou aperte a tecla desejada. */
export function KeyPicker({ value, onChange, disabled }) {
  const [open, setOpen] = useState(false)
  const [listening, setListening] = useState(false)
  const rootRef = useRef(null)

  const close = () => {
    setOpen(false)
    setListening(false)
  }
  const pick = (key) => {
    onChange(key)
    close()
  }

  // Fecha ao clicar fora
  useEffect(() => {
    if (!open) return
    const onMouseDown = (event) => {
      if (!rootRef.current?.contains(event.target)) close()
    }
    document.addEventListener('mousedown', onMouseDown)
    return () => document.removeEventListener('mousedown', onMouseDown)
  }, [open])

  // Esc fecha; no modo captura, a próxima tecla vira a escolhida
  useEffect(() => {
    if (!open) return
    const onKeyDown = (event) => {
      if (event.key === 'Escape' && !event.ctrlKey && !event.altKey) {
        event.preventDefault()
        event.stopPropagation() // não fecha junto um modal que esteja por trás
        close()
        return
      }
      if (!listening) return
      event.preventDefault()
      event.stopPropagation()
      const name = toKeyName(event)
      if (name) pick(name)
    }
    window.addEventListener('keydown', onKeyDown, true)
    return () => window.removeEventListener('keydown', onKeyDown, true)
  }, [open, listening])

  const unset = !value

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        disabled={disabled}
        aria-haspopup="dialog"
        aria-expanded={open}
        onClick={() => (open ? close() : setOpen(true))}
        className={`inline-flex min-w-[8rem] items-center justify-between gap-2 rounded-lg border px-3 py-1.5 text-sm transition-colors disabled:opacity-40 ${
          unset
            ? 'border-amber-500/50 bg-amber-500/10 text-amber-200 hover:bg-amber-500/15'
            : 'border-base-700 bg-base-950 font-mono text-base-100 hover:border-base-600'
        }`}
      >
        {unset ? 'Escolher tecla' : keyLabel(value)}
        <Icon name="chevron" className={`h-3.5 w-3.5 text-base-500 transition-transform ${open ? '-rotate-90' : 'rotate-90'}`} />
      </button>

      {open && (
        <div
          role="dialog"
          aria-label="Escolher tecla"
          className="absolute right-0 z-20 mt-2 w-80 rounded-xl border border-base-700 bg-base-900 p-3 shadow-panel"
        >
          <button
            type="button"
            onClick={() => setListening((v) => !v)}
            className={`mb-3 w-full rounded-lg border px-3 py-2 text-sm transition-colors ${
              listening
                ? 'animate-pulse border-accent-500 bg-accent-500/10 text-accent-300'
                : 'border-base-700 text-base-200 hover:bg-base-800'
            }`}
          >
            {listening ? 'Aperte a tecla agora…' : 'Apertar a tecla no teclado'}
          </button>

          <div className="space-y-3">
            {KEY_GROUPS.map((group) => (
              <div key={group.label}>
                <p className="mb-1.5 text-[11px] font-medium uppercase tracking-wider text-base-500">{group.label}</p>
                <div className="grid grid-cols-6 gap-1">
                  {group.keys.map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => pick(key)}
                      title={keyLabel(key)}
                      className={`rounded-md border px-1 py-1.5 font-mono text-[11px] transition-colors ${
                        key === value
                          ? 'border-accent-500/60 bg-accent-500/15 text-accent-300'
                          : 'border-base-800 text-base-300 hover:bg-base-800 hover:text-base-100'
                      }`}
                    >
                      {key.replace('ctrl+', '').replace('shift+', '').toUpperCase()}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          {!unset && (
            <button
              type="button"
              onClick={() => pick('')}
              className="mt-3 w-full rounded-lg px-3 py-1.5 text-xs text-base-500 hover:bg-base-800 hover:text-base-300"
            >
              Deixar sem tecla (o bot não usa esta ação)
            </button>
          )}
        </div>
      )}
    </div>
  )
}

/** Sequência de teclas em ordem (ex: rotação de cura). */
function KeyList({ value, onChange, disabled, addLabel = 'Adicionar tecla' }) {
  const keys = Array.isArray(value) ? value : []
  return (
    <div className="space-y-2">
      {keys.length === 0 && <p className="text-xs text-amber-300">Nenhuma tecla ainda. Adicione na ordem em que o bot deve apertar.</p>}
      <ol className="flex flex-wrap items-center gap-2">
        {keys.map((key, i) => (
          <li key={i} className="flex items-center gap-1.5">
            <span className="font-mono text-[11px] text-base-500">{i + 1}.</span>
            <KeyPicker value={key} disabled={disabled} onChange={(next) => onChange(keys.map((k, j) => (j === i ? next : k)))} />
            <button
              type="button"
              disabled={disabled}
              aria-label={`Remover tecla ${i + 1}`}
              onClick={() => onChange(keys.filter((_, j) => j !== i))}
              className="rounded p-1 text-base-500 hover:bg-base-800 hover:text-red-300"
            >
              <Icon name="x" className="h-3.5 w-3.5" />
            </button>
            {i < keys.length - 1 && <Icon name="chevron" className="h-3.5 w-3.5 text-base-600" />}
          </li>
        ))}
        <li>
          <button
            type="button"
            disabled={disabled}
            onClick={() => onChange([...keys, ''])}
            className="inline-flex items-center gap-1.5 rounded-lg border border-dashed border-base-700 px-3 py-1.5 text-xs text-base-400 hover:border-accent-500/50 hover:text-accent-300"
          >
            <Icon name="plus" className="h-3.5 w-3.5" />
            {addLabel}
          </button>
        </li>
      </ol>
    </div>
  )
}

function RoiInput({ value, onChange, disabled }) {
  const roi = Array.isArray(value) && value.length === 4 ? value : [0, 0, 0, 0]
  const labels = ['X', 'Y', 'Largura', 'Altura']
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {labels.map((label, i) => (
        <label key={label} className="flex flex-col gap-1">
          <span className="text-[11px] uppercase tracking-wider text-base-500">{label}</span>
          <NumberInput
            value={roi[i]}
            min={0}
            max={10000}
            disabled={disabled}
            onChange={(n) => onChange(roi.map((v, j) => (j === i ? Math.round(n) : v)))}
          />
        </label>
      ))}
    </div>
  )
}

export function FieldRow({ label, hint, restart = false, stacked = false, children }) {
  return (
    <div className={`flex py-3.5 ${stacked ? 'flex-col gap-3' : 'items-center justify-between gap-6'}`}>
      <div className="min-w-0">
        <p className="text-sm text-base-100">
          {label}
          {restart && (
            <span className="ml-2 rounded bg-base-800 px-1.5 py-0.5 align-middle text-[10px] font-medium uppercase tracking-wider text-base-400">
              vale ao reiniciar
            </span>
          )}
        </p>
        {hint && <p className="mt-0.5 max-w-prose text-xs leading-relaxed text-base-500">{hint}</p>}
      </div>
      <div className={stacked ? '' : 'shrink-0'}>{children}</div>
    </div>
  )
}

/** Renderiza um campo descrito no schema (src/schema/features.js) ligado ao config.json. */
export function Field({ field }) {
  const [value, setValue, disabled] = useConfigField(field.path, field.default)

  let control
  let stacked = false
  switch (field.type) {
    case 'toggle':
      control = <Toggle checked={Boolean(value)} onChange={setValue} disabled={disabled} label={field.label} />
      break
    case 'number':
      control = <NumberInput value={value} onChange={setValue} min={field.min} max={field.max} step={field.step} unit={field.unit} disabled={disabled} />
      break
    case 'slider':
      control = <Slider value={value} onChange={setValue} min={field.min} max={field.max} step={field.step} unit={field.unit} scale={field.scale} disabled={disabled} />
      break
    case 'text':
      control = <TextInput value={value} onChange={setValue} placeholder={field.placeholder} disabled={disabled} wide={field.wide} />
      break
    case 'key':
      control = <KeyPicker value={value} onChange={setValue} disabled={disabled} />
      break
    case 'segmented':
      stacked = Boolean(field.columns)
      control = <Segmented value={value} onChange={setValue} options={field.options} columns={field.columns} disabled={disabled} />
      break
    case 'tags':
      stacked = true
      control = <Tags value={value} onChange={setValue} placeholder={field.placeholder} disabled={disabled} />
      break
    case 'roi':
      stacked = true
      control = <RoiInput value={value} onChange={setValue} disabled={disabled} />
      break
    case 'keylist':
      stacked = true
      control = <KeyList value={value} onChange={setValue} disabled={disabled} addLabel={field.addLabel} />
      break
    default:
      control = null
  }

  return (
    <FieldRow label={field.label} hint={field.hint} restart={field.restart} stacked={stacked}>
      {control}
    </FieldRow>
  )
}
