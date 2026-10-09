import { useCallback, useEffect, useState } from 'react'
import { apiFetch } from '../lib/api.js'

const POLL_MS = 1000

/** Lê /api/status a cada segundo e expõe os comandos de controle do bot. */
export function useBotStatus() {
  const [status, setStatus] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    async function poll() {
      try {
        const data = await apiFetch('/api/status')
        if (!cancelled) {
          setStatus(data)
          setError(null)
        }
      } catch (err) {
        if (!cancelled) setError(err)
      }
    }

    poll()
    const timer = setInterval(poll, POLL_MS)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  const control = useCallback(async (action) => {
    try {
      await apiFetch('/api/control', { method: 'POST', body: JSON.stringify({ action }) })
      // Atualiza logo após o comando em vez de esperar o próximo poll
      setStatus(await apiFetch('/api/status'))
    } catch (err) {
      setError(err)
    }
  }, [])

  return { status, error, control }
}
