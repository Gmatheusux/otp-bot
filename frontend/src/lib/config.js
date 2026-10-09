/** Lê um valor aninhado por caminho com pontos: getPath(cfg, 'features.combat.auto_combo'). */
export function getPath(obj, path) {
  return path.split('.').reduce((node, key) => (node == null ? undefined : node[key]), obj)
}

/** Devolve uma cópia de obj com o valor trocado no caminho (imutável, para o React). */
export function setPath(obj, path, value) {
  const [head, ...rest] = path.split('.')
  const base = obj && typeof obj === 'object' && !Array.isArray(obj) ? obj : {}
  return { ...base, [head]: rest.length ? setPath(base[head], rest.join('.'), value) : value }
}
