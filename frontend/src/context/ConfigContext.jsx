import { createContext, useContext } from 'react'
import { useBotConfig } from '../hooks/useBotConfig.js'
import { getPath } from '../lib/config.js'

const ConfigContext = createContext(null)

export function ConfigProvider({ children }) {
  const value = useBotConfig()
  return <ConfigContext.Provider value={value}>{children}</ConfigContext.Provider>
}

export function useConfig() {
  return useContext(ConfigContext)
}

/** [valor, setter, desabilitado] de um campo do config.json. */
export function useConfigField(path, fallback) {
  const { config, setValue } = useConfig()
  const value = getPath(config, path)
  return [value === undefined ? fallback : value, (next) => setValue(path, next), !config]
}
