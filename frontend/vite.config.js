import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Em dev (npm run dev) o Vite repassa /api e /ws para o bot, mantendo a mesma origem.
const BOT_API = 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '127.0.0.1',
    proxy: {
      '/api': BOT_API,
      '/ws': { target: BOT_API, ws: true },
    },
  },
})
