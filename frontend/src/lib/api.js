const TOKEN_KEY = 'otp-session-token'

/**
 * O backend gera um token novo a cada execução e abre o console com ?token=...
 * Guardamos na sessão e limpamos da barra de endereço.
 */
function resolveToken() {
  const params = new URLSearchParams(window.location.search)
  const fromUrl = params.get('token')
  if (fromUrl) {
    try {
      sessionStorage.setItem(TOKEN_KEY, fromUrl)
    } catch {
      // sessionStorage indisponível: o token segue só em memória
    }
    params.delete('token')
    const query = params.toString()
    window.history.replaceState(null, '', window.location.pathname + (query ? `?${query}` : ''))
    return fromUrl
  }
  try {
    return sessionStorage.getItem(TOKEN_KEY) ?? ''
  } catch {
    return ''
  }
}

export const sessionToken = resolveToken()

export async function apiFetch(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'X-OTP-Token': sessionToken,
      ...(options.headers ?? {}),
    },
  })
  if (!response.ok) throw new Error(`${options.method ?? 'GET'} ${path} falhou: ${response.status}`)
  return response.json()
}

export function logsSocketUrl() {
  const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${window.location.host}/ws/logs?token=${encodeURIComponent(sessionToken)}`
}
