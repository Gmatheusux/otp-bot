import { useCallback, useEffect, useRef, useState } from 'react'
import { apiFetch } from '../lib/api.js'
import { setPath } from '../lib/config.js'

const CONFIG_URL = '/api/config'
const SAVE_DEBOUNCE_MS = 400

/**
 * Lê o config.json via FastAPI (GET) e persiste alterações (POST).
 * O backend sobrescreve o arquivo inteiro, então sempre enviamos o objeto completo.
 * Edições seguidas (digitação, sliders) são agrupadas num único POST.
 */
export function useBotConfig() {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [saveState, setSaveState] = useState('idle') // idle | saving | saved | error
  const latest = useRef(null)
  const timer = useRef(null)

  useEffect(() => {
    let cancelled = false

    async function fetchConfig() {
      try {
        const data = await apiFetch(CONFIG_URL)
        if (!cancelled) {
          latest.current = data
          setConfig(data)
        }
      } catch (err) {
        if (!cancelled) setError(err)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    fetchConfig()
    return () => {
      cancelled = true
      clearTimeout(timer.current)
    }
  }, [])

  const setValue = useCallback((path, value) => {
    const next = setPath(latest.current ?? {}, path, value)
    latest.current = next
    setConfig(next)
    setSaveState('saving')

    clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      try {
        await apiFetch(CONFIG_URL, { method: 'POST', body: JSON.stringify(latest.current) })
        setError(null)
        setSaveState('saved')
      } catch (err) {
        setError(err)
        setSaveState('error')
      }
    }, SAVE_DEBOUNCE_MS)
  }, [])

  /** Relê do servidor quando ele mesmo altera o config (ex: nova referência de calibração). */
  const reload = useCallback(async () => {
    try {
      const data = await apiFetch(CONFIG_URL)
      latest.current = data
      setConfig(data)
    } catch (err) {
      setError(err)
    }
  }, [])

  return { config, loading, error, saveState, setValue, reload }
}
