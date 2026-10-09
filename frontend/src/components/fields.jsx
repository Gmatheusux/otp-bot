import { useEffect, useState } from 'react'
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

function Segmented({ value, onChange, options, disabled, columns }) {
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

function KeyCapture({ value, onChange, disabled }) {
  const [listening, setListening] = useState(false)

  useEffect(() => {
    if (!listening) return
    const onKeyDown = (event) => {
      event.preventDefault()
      event.stopPropagation()
      if (event.key === 'Escape' && !event.ctrlKey && !event.altKey) {
        setListening(false)
        return
      }
      const name = toKeyName(event)
      if (name) {
        onChange(name)
        setListening(false)
      }
    }
    window.addEventListener('keydown', onKeyDown, true)
    return () => window.removeEventListener('keydown', onKeyDown, true)
  }, [listening, onChange])

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={() => setListening((v) => !v)}
      onBlur={() => setListening(false)}
      className={`min-w-[7rem] rounded-lg border px-3 py-1.5 font-mono text-sm transition-colors disabled:opacity-40 ${
        listening
          ? 'animate-pulse border-accent-500 bg-accent-500/10 text-accent-300'
          : 'border-base-700 bg-base-950 text-base-100 hover:border-base-600'
      }`}
    >
      {listening ? 'aperte a tecla…' : (value || 'definir').toUpperCase()}
    </button>
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
      control = <KeyCapture value={value} onChange={setValue} disabled={disabled} />
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
    default:
      control = null
  }

  return (
    <FieldRow label={field.label} hint={field.hint} restart={field.restart} stacked={stacked}>
      {control}
    </FieldRow>
  )
}
