import react from '@vitejs/plugin-react'
import { seedDesignPlugin } from '@seed-design/vite-plugin'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), seedDesignPlugin({ colorMode: 'light-only' })],
  server: {
    // 개발 서버에서만 사용 — 배포는 nginx가 /api를 프록시한다 (web/nginx.conf)
    proxy: { '/api': 'http://localhost:8000' },
  },
})
