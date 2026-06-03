import path from "node:path"
import react from "@vitejs/plugin-react"
import { defineConfig, loadEnv } from "vite"

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const apiBaseUrl = env.VITE_API_BASE_URL || DEFAULT_API_BASE_URL

  return {
    plugins: [react()],
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
    },
    server: {
      proxy: {
        "/ask": apiBaseUrl,
        "/health": apiBaseUrl,
      },
    },
  }
})
