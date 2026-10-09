import { Field } from './fields.jsx'
import { useConfig } from '../context/ConfigContext.jsx'
import { getPath } from '../lib/config.js'

const BADGES = {
  ativo: { label: 'Funcionando', className: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300' },
  planejado: { label: 'Em breve', className: 'border-base-700 bg-base-800 text-base-400' },
}

export function StatusBadge({ status }) {
  const badge = BADGES[status]
  if (!badge) return null
  return (
    <span className={`shrink-0 rounded-full border px-2.5 py-0.5 text-[11px] font-medium ${badge.className}`}>
      {badge.label}
    </span>
  )
}

export function Card({ title, description, status, children, footer }) {
  return (
    // Sem overflow-hidden: o seletor de tecla abre por cima da borda do cartão
    <section className="rounded-2xl border border-base-800 bg-base-900 shadow-panel">
      {title && (
        <header className="flex items-start justify-between gap-4 border-b border-base-800 px-5 py-4">
          <div className="min-w-0">
            <h3 className="text-sm font-semibold text-base-100">{title}</h3>
            {description && <p className="mt-1 text-xs leading-relaxed text-base-400">{description}</p>}
          </div>
          <StatusBadge status={status} />
        </header>
      )}
      {children}
      {footer}
    </section>
  )
}

export default function Section({ section }) {
  const { config } = useConfig()
  // showIf: campo só aparece quando outro campo tem um valor (ex: teclas só no modo "Tecla")
  const fields = section.fields.filter(
    (f) => !f.showIf || getPath(config, f.showIf.path) === f.showIf.equals,
  )
  const Extra = section.extra
  return (
    <Card
      title={section.title}
      description={section.description}
      status={section.status}
      footer={
        section.status === 'planejado' && (
          <p className="rounded-b-2xl border-t border-base-800 bg-base-950/40 px-5 py-3 text-xs text-base-500">
            Suas escolhas já ficam salvas. O bot passa a usar quando esta função for implementada.
          </p>
        )
      }
    >
      <div className="divide-y divide-base-800/70 px-5">
        {fields.map((field) => (
          <Field key={`${field.path}-${field.label}`} field={field} />
        ))}
      </div>
      {Extra && <Extra />}
    </Card>
  )
}
