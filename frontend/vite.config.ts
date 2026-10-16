import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  optimizeDeps: {
    include: ["markdown-it"],
  },
  server: {
    port: 5173,
    proxy: {
      // 试穿 sidecar 的接口前缀必须排在 "/api" 之前：vite 按声明顺序取第一个匹配的 context
      "/api/v1": { target: "http://127.0.0.1:8000", changeOrigin: true },
      // 试穿素材图/示例图与结果图分别由 sidecar 挂载（见后端 asset_url_prefix / results_url_prefix）
      "/tryon-assets": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/tryon-results": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/uploads": { target: "http://127.0.0.1:8765", changeOrigin: true },
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
});
