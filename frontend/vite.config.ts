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
      // 试穿素材图/结果图目前由 sidecar 的 /static 挂载提供
      "/static": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/uploads": { target: "http://127.0.0.1:8765", changeOrigin: true },
      "/api": {
        target: "http://127.0.0.1:8765",
        changeOrigin: true,
      },
    },
  },
});
