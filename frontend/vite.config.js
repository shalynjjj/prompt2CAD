import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173, // 前端运行端口
    proxy: {
      // 代理配置：将 /api 开头的请求转发到本地后端
      '/api': {
        target: 'http://127.0.0.1:8000', // 你的 FastAPI 本地运行地址
        changeOrigin: true,
        secure: false,
      }
    }
  }
})