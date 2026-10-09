import { useEffect, useState } from 'react'
import { logsSocketUrl } from '../lib/api.js'

const MAX_LOGS = 200
const RECONNECT_MS = 2000

/** Assina o stream /ws/logs e reconecta sozinho se o backend reiniciar. */
export function useBotLogs() {
  const [logs, setLogs] = useState([])
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    let socket
    let reconnectTimer
    let closed = false

    function connect() {
      socket = new WebSocket(logsSocketUrl())
      socket.onopen = () => {
        setConnected(true)
        // O servidor reenvia o histórico a cada conexão
        setLogs([])
      }
      socket.onmessage = (event) => {
        const entry = JSON.parse(event.data)
        setLogs((prev) => [...prev, entry].slice(-MAX_LOGS))
      }
      socket.onclose = () => {
        setConnected(false)
        if (!closed) reconnectTimer = setTimeout(connect, RECONNECT_MS)
      }
    }

    connect()
    return () => {
      closed = true
      clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [])

  return { logs, connected }
}
