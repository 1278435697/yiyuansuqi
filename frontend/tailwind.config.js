/** @type {import('tailwindcss').Config} */
export default {
  // 仅扫描 src 下的 .vue / .ts 文件，生成用到的工具类
  content: ["./index.html", "./src/**/*.{vue,ts,tsx}"],
  // 禁用 preflight，避免重置 Element Plus 与既有国风样式
  corePlugins: { preflight: false },
  theme: {
    extend: {
      colors: {
        yisu: {
          bg: "#f7f2e9",
          card: "#fdfbf5",
          line: "#e4d9c6",
          ink: "#3a2f25",
          accent: "#9c2f1e",
          gold: "#b98a2f",
          jade: "#2f6b5e",
        },
      },
      fontFamily: {
        serif: ['"Noto Serif SC"', "STSong", "SimSun", "serif"],
      },
    },
  },
  plugins: [],
};
