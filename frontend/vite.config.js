import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // 允许通过 IP 访问（方便局域网测试）
    port: 5173, // 指定端口
  }
})