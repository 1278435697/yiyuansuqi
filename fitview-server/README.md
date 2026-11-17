# fitview-server · 虚拟试穿新版（2D 换装 + 3D 建模）后端

`/fitview` 页面（前端 `dist/fitview` 的 React 应用）背后调用的 Node 服务。只做两件事：
用豆包 Seedream 生成正面换装照（及三视图），再把图送进 Tripo / 混元生 3D 得到可旋转的
`.glb` 模型，前端用 three.js 渲染。

## 技术栈与依赖

- 纯 Node 内置模块（`node:http` / `node:zlib` / 内置 `fetch`），**没有任何 npm 依赖**，
  不需要 `npm install`，也没有 `node_modules`。
- 要求 Node ≥ 18（依赖内置 fetch）。
- 单文件入口 `index.mjs`，`PORT` 默认 8787。

## 启动

```bash
cp .env.example .env      # 填入 ARK_API_KEY / TRIPO_API_KEY 等密钥
node index.mjs            # 或 node --watch index.mjs
```

生产环境由 nginx 把 `/fitview-api/*` 重写为 `/api/*` 后转发到 `127.0.0.1:8787`，
因此前端代码里写的是 `/fitview-api/tryon`，服务端只认 `/api/tryon`。

## 接口

| 方法 | 路径 | 作用 |
| --- | --- | --- |
| GET | `/api/health` | 健康检查，返回启用中的图像模型与 3D 供应商 |
| POST | `/api/tryon` | 人像 + 服装参考 → 豆包重绘的正面换装照 |
| POST | `/api/tryon-views` | 人像 + 服装参考 → 正面 / 侧面 / 背面三视图（正面作锚点，侧面与背面据它对齐） |
| POST | `/api/3d` | 三视图（或单图）→ 提交生成式 3D 任务，返回任务 id |
| GET | `/api/3d/{id}` | 轮询任务状态 |
| GET | `/api/3d/{id}/model` | 下载生成的 `.glb` 模型 |
| GET | `/api/asset` | 代理读取外部图片资源 |

## 环境变量与费用

- `ARK_IMAGE_MODEL`：默认 `doubao-seedream-5-0-flash-260915`；`ARK_IMAGE_SIZE=2K` 约 ¥0.12/张。
- `MODEL3D_PROVIDER=tripo` 时用 Tripo H 系列（默认 `v3.1-20260211`，8K 贴图 + detailed 几何，
  单次约 ¥3.5～4.9）；改成 `hunyuan` 走腾讯混元生 3D（约 ¥2.4/次）；`hitem3d` 已暂停。
- 设成 `off` 则完全不产生 3D 费用，前端改走本地三视图雕刻。
- 无 `ARK_API_KEY` 或 `ARK_MOCK=1` 时服务自动进入 mock 模式，便于联调。

## 与 tryon_service 的区别

仓库里的 `tryon_service`（Python，8010）是**上一版 2D 试穿**：MediaPipe 姿态 + 分割，
换装后端按 `aidge → HR-VITON → TPS → mock` 降级，入口是 `/tryon`。
本服务是**新版**：豆包重绘 + 生成式 3D，入口是 `/fitview`。两者并存，互不替代。

## 安全

`.env` 保存 API 密钥，已被 `.gitignore` 忽略，禁止提交；仓库只保留 `.env.example`。
人像经服务端转出时使用一次性 URL（短 TTL），调用结束即回收。
