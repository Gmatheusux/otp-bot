// Ícones de traço (24x24), no estilo dos ícones de linha, sem dependência externa.
const PATHS = {
  home: ['M3 10.5 12 3l9 7.5', 'M5 9.5V20h5v-6h4v6h5V9.5'],
  swords: ['M14.5 17.5 3 6V3h3l11.5 11.5', 'M13 19l6-6', 'M16 16l4 4', 'M19 21l2-2', 'M9.5 6.5 14 2h7v3l-4.5 4.5'],
  heart: ['M12 20s-7-4.35-7-10a4 4 0 0 1 7-2.65A4 4 0 0 1 19 10c0 5.65-7 10-7 10Z'],
  route: ['M6 19a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z', 'M18 9a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z', 'M8 17h7.5a3.5 3.5 0 0 0 0-7h-7a3.5 3.5 0 0 1 0-7H16'],
  ball: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M3 12h6', 'M15 12h6', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  shield: ['M12 21s7-3 7-9V5l-7-2-7 2v7c0 6 7 9 7 9Z', 'M9 12l2 2 4-4'],
  sparkles: ['M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8Z', 'M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8Z'],
  users: ['M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M2 21v-1a6 6 0 0 1 12 0v1', 'M16 3.5a4 4 0 0 1 0 7', 'M18 14.5a6 6 0 0 1 4 5.5v1'],
  keyboard: ['M3 6h18v12H3Z', 'M7 10h.01', 'M11 10h.01', 'M15 10h.01', 'M7 14h10'],
  settings: ['M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1Z'],
  play: ['M7 4.5v15l12-7.5Z'],
  pause: ['M7 4h3v16H7Z', 'M14 4h3v16h-3Z'],
  power: ['M12 3v9', 'M6.3 6.3a8 8 0 1 0 11.4 0'],
  record: ['M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  stop: ['M6 6h12v12H6Z'],
  alert: ['M12 3 2 20h20Z', 'M12 10v4', 'M12 17h.01'],
  check: ['M5 12l5 5 9-10'],
  x: ['M6 6l12 12', 'M18 6 6 18'],
  chevron: ['M9 6l6 6-6 6'],
  flask: ['M9 3h6', 'M10 3v6.5L4.6 18.2A2 2 0 0 0 6.3 21h11.4a2 2 0 0 0 1.7-2.8L14 9.5V3', 'M7.5 15h9'],
  plus: ['M12 5v14', 'M5 12h14'],
  camera: ['M4 8h3l2-3h6l2 3h3v11H4Z', 'M12 17a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z'],
  upload: ['M12 15V4', 'M7 9l5-5 5 5', 'M5 15v4h14v-4'],
  trash: ['M4 7h16', 'M9 7V4h6v3', 'M6 7l1 13h10l1-13'],
  search: ['M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14Z', 'M20 20l-4-4'],
}

export default function Icon({ name, className = 'h-4 w-4', filled = false }) {
  return (
    <svg
      viewBox="0 0 24 24"
      className={className}
      fill={filled ? 'currentColor' : 'none'}
      stroke="currentColor"
      strokeWidth={filled ? 0 : 1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name].map((d) => (
        <path key={d} d={d} />
      ))}
    </svg>
  )
}
