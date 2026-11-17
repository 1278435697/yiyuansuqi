# 衣源溯起 · 华夏衣冠志

> AI 驱动的历代服饰数字化溯源、复原与传承平台

**衣冠有史，华服可溯。**

从先秦的冕服深衣，到清代的旗装补褂；从出土实物到传世文献，每一件华夏服饰都有迹可循、有史可查。

线上地址：<http://47.93.14.11>

## 项目简介

「衣源溯起」是面向中国传统服饰文化的 AI Web 应用。平台以九朝服饰档案为骨、以纹样与面料为肌理，用大模型、多模态视觉识别与 Three.js 三维技术，把「可查、可看、可试」串成一条完整的溯源路径。

上线版本包含三部分：

| 部分 | 技术 | 端口 | 说明 |
|---|---|---|---|
| 主站 | Vue 3 + Vite 构建，Nginx 静态托管 | 80 | 档案、时空图谱、面料、纹样、衣冠、社区、AI 问答 |
| 后端 API | FastAPI + Uvicorn | 8765 | `/api/*` 全部业务接口 |
| 试穿旧版 | FastAPI sidecar | 8010 | `/tryon`，MediaPipe 姿态 + TPS 变形 + 阿里云 Aidge 云端换装 |
| 试穿新版 | 纯 Node 内置模块 | 8787 | `/fitview`，豆包 Seedream 换装重绘 + Tripo/混元生 3D + three.js 渲染 |
| 三维馆 | 独立静态子站 | — | `frontend/public/mus3d`，Three.js 漫游展厅 |

## 核心模块

| 模块 | 入口 | 内容 |
|---|---|---|
| 档案 | `/archive` | 9 朝卷帙、96 件文物实例、46 款款式类型、8 个阅读板块；支持按朝代/馆藏筛选、按编号（1–96）检索 |
| 时空图谱 | `/timeline`、`/geomap` | 朝代时间轴 + 出土地点地图（Leaflet），标注模式与热力模式、按朝代分布与出土热点柱状图 |
| 面料 | `/fabric` | 63 条传统面料词条，编号 NO.01–NO.63；含工艺流程、诗文、实物图、常见搭配 |
| 纹样 | `/pattern` | 纹样库与 AI 识纹样：上传图片输出朝代/形制/纹样与置信度；纹样与面料、服饰双向关联 |
| 衣冠 | `/heritage`、`/accessories` | 服饰与配饰九卷图谱，形制结构对比表 |
| 博物馆 | `/museum` | Three.js 三维展厅，展品资料卡 |
| 虚拟试穿（新版） | `/fitview` | 上传照片 → 豆包 Seedream 生成正面换装照 → Tripo（可切混元）生成 `.glb` → 模型可旋转、可下载 |
| 虚拟试穿（旧版） | `/tryon` | 本地 MediaPipe 分割/姿态 + TPS 变形 + Aidge 云端换装，输出 2D 换装图 |
| AI 问答 | `/aiqa` | 接入豆包大模型，多轮问答 + 推荐问题 |
| 社区 | `/community` | 发帖、评论、点赞；管理员下架/恢复，超管任命管理员 |
| 传承 | `/heritage` | 非遗技艺档案，含工序与传承人信息 |

## 两套虚拟试穿

线上同时保留两条链路，页面互不影响。

**旧版 `/tryon`（2D，8010）** — `tryon_service/`

```
上传照片 → 前景分割 → 姿态估计 → VTON 换装 → 后处理 → 落盘
```

- 供应商按 `aidge → hrviton → tps → mock` 顺序降级，任一层缺失自动回退
- `aidge.py` 对接阿里云 Aidge AiTryOn（`API_VERSION=2026-04-28`，只接受公网可访问的图片 URL）
- 全链路本地可跑，无 3D 能力

**新版 `/fitview`（2D + 3D，8787）** — `fitview-server/`

```
上传照片 → 豆包 Seedream 重绘正面换装照（可选三视图）→ 3D 供应商生成 .glb → three.js 渲染旋转
```

- 图像模型：`doubao-seedream-5-0-flash-260915`（2K，约 ¥0.12/张）
- 3D 供应商可切换：`tripo`（`v3.1-20260211`，8K 贴图 + detailed 几何，约 ¥3.5–4.9/次）、`hunyuan`（混元生 3D 3.0，约 ¥2.4/次）、`hitem3d`（已暂停，约 ¥10/次）、`off`（本地三视图雕刻，不产生费用）
- 接口：`/api/health`、`/api/tryon`、`/api/tryon-views`、`/api/3d`、`/api/3d/{id}/model`、`/api/3d/{id}`、`/api/asset`
- 对外经 Nginx 重写：`/fitview-api/*` → `127.0.0.1:8787/api/*`

## 技术栈

- **前端**：Vue 3、Vite、Vue Router、Pinia、Element Plus、Tailwind CSS、Three.js、MediaPipe、ECharts、Leaflet、GSAP
- **后端**：FastAPI、Uvicorn、SQLAlchemy、PyMySQL、JWT、OpenAI SDK（兼容火山方舟）
- **试穿旧版**：FastAPI、OpenCV、MediaPipe、NumPy、Pillow、阿里云 Aidge SDK
- **试穿新版**：Node 18+ 内置模块（`http`/`fetch`/`fs`），零第三方依赖
- **数据**：MySQL 8.0（线上）、SQLite（本地开发与演示）、ChromaDB（纹样检索）
- **部署**：阿里云 ECS + Nginx + systemd

## 目录结构

```
yisu-ai-platform/
├── frontend/                 # Vue 3 主站
│   ├── src/                  # views / components / store / router / api
│   ├── public/               # 静态资源与独立子站
│   │   ├── mus3d/            # 三维展馆
│   │   ├── pattern-assets/   # 纹样图片
│   │   ├── images/fabrics/craft/  # 面料工艺流程图
│   │   └── accessories / heritage / museum
│   └── package.json
├── backend/                  # FastAPI 主服务
│   ├── app/
│   │   ├── main.py           # 入口，挂载 /api/archive、/api/fabrics、/api/aiqa 等
│   │   ├── api/              # 档案 / 面料 / 纹样 / 社区 / 用户 / 问答 / 识别
│   │   ├── core/             # 配置、安全、数据库
│   │   ├── models/           # SQLAlchemy 模型
│   │   └── services/         # 业务逻辑
│   ├── data/                 # SQLite 演示库
│   └── requirements.txt
├── tryon_service/            # 试穿旧版（2D sidecar）
│   ├── app/                  # pipeline / providers(aidge,hrviton,tps,mock)
│   ├── scripts/
│   └── docs/
├── fitview-server/           # 试穿新版（2D + 3D）
│   ├── index.mjs             # 714 行，全部接口
│   ├── .env.example          # 只含键名，无真实密钥
│   └── README.md
├── database/                 # 建表与种子 SQL
├── frontend/dist/            # 构建产物（线上同版）
├── yisu_nginx.conf           # Nginx 站点配置
├── yisu-backend.service      # systemd 单元（8765）
├── yisu-tryon.service        # systemd 单元（8010）
├── 启动衣溯AI.bat / 关闭衣溯AI.bat
└── README.md
```

## 环境要求

- Node.js >= 18
- Python >= 3.10
- MySQL >= 8.0（本地也可直接用 SQLite）

## 快速启动

### 后端

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
# source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

`.env` 关键项：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DB=yisu_ai

LLM_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
LLM_API_KEY=你的火山方舟API Key
LLM_MODEL=doubao-seed-character-260628

JWT_SECRET=随机字符串
```

### 前端

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173
npm run build    # 产物在 dist/
```

### 试穿旧版（8010）

```bash
cd tryon_service
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-core.txt
cp .env.example .env      # 填 Aidge 的 AccessKey / 公网回调地址
uvicorn app.main:app --host 0.0.0.0 --port 8010
```

未配置云端密钥时走 `mock` 供应商，仍可跑通全流程。

### 试穿新版（8787）

```bash
cd fitview-server
cp .env.example .env      # 填 ARK_API_KEY；要 3D 再填 TRIPO_API_KEY 或 HUNYUAN_API_KEY
node index.mjs
```

`MODEL3D_PROVIDER` 可选 `tripo` / `hunyuan` / `hitem3d` / `off`；`off` 时不调用任何付费 3D 接口。

## 环境配置与依赖清单

三个服务各有一份变量模板，复制为 `.env` 后填写即可；仓库内不含任何真实密钥。

| 服务 | 模板 | 复制为 | 启动端口 |
|---|---|---|---|
| 主站后端 | `backend/.env.example` | `backend/.env` | 8765 |
| 试穿旧版 | `tryon_service/.env.example` | `tryon_service/.env` | 8010 |
| 试穿新版 | `fitview-server/.env.example` | `fitview-server/.env` | 8787 |

### backend/.env

| 变量 | 用途 | 必填 |
|---|---|---|
| `MYSQL_HOST` `MYSQL_PORT` `MYSQL_USER` `MYSQL_PASSWORD` `MYSQL_DB` | 主数据库 | 是 |
| `LLM_BASE_URL` `LLM_API_KEY` `LLM_MODEL` | 火山方舟豆包大模型（问答） | 是 |
| `JWT_SECRET` | 登录令牌签名 | 是 |
| `REDIS_URL` | 缓存（缺省走内存） | 否 |
| `CHROMA_PERSIST_DIR` `CHROMA_COLLECTION` | 纹样向量库 | 否 |
| `EMBED_API_KEY` | 向量化接口 | 否 |
| `SD_API_URL` `VIDEO_GEN_API_URL` `VIDEO_GEN_API_KEY` | 生图/生视频扩展 | 否 |

### tryon_service/.env

| 变量 | 用途 | 必填 |
|---|---|---|
| `YISU_VTON_BACKEND` | `auto` / `aidge` / `hrviton` / `tps` / `mock` | 是（auto 即自动降级） |
| `YISU_AIDGE_ACCESS_KEY_ID` `YISU_AIDGE_ACCESS_KEY_SECRET` | 阿里云 Aidge 试衣凭据 | 用云端时必填 |
| `YISU_PUBLIC_BASE_URL` | 厂商能回访到的本服务地址 | 用云端时必填 |
| `YISU_AIDGE_RESOLUTION` `YISU_AIDGE_TIMEOUT_SECONDS` `YISU_OUTBOX_TTL_SECONDS` | 出图档位、超时、一次性图片有效期 | 否 |
| `YISU_DATABASE_URL` | 留空复用 `backend/data/yisu_prod.db`；生产填 MySQL | 否 |
| `YISU_VITONGPU_ONNX` `YISU_U2NET_ONNX` `YISU_HRVITON_CKPT_DIR` | 本地模型权重路径，缺文件自动降级 | 否 |
| `YISU_ASSET_URL_PREFIX` `YISU_RESULTS_URL_PREFIX` `YISU_RESULTS_ROOT` | 素材/结果图对外路径 | 否 |
| `YISU_MAX_UPLOAD_MB` `YISU_OUTPUT_LONG_SIDE` `YISU_ENABLE_DISK_CACHE` | 上传上限、输出长边、结果缓存 | 否 |
| `YISU_CORS_ORIGINS` | 跨域来源，同源部署留空 | 否 |

### fitview-server/.env

| 变量 | 用途 | 必填 |
|---|---|---|
| `PORT` | 服务端口，默认 8787 | 否 |
| `ARK_API_KEY` `ARK_BASE_URL` `ARK_IMAGE_MODEL` `ARK_IMAGE_SIZE` | 豆包 Seedream 换装重绘 | 是（2D 链路） |
| `MODEL3D_PROVIDER` | `tripo` / `hunyuan` / `hitem3d` / `off` | 是 |
| `TRIPO_API_KEY` `TRIPO_MODEL` `TRIPO_TEXTURE_QUALITY` `TRIPO_GEOMETRY_QUALITY` `TRIPO_FACE_LIMIT` `TRIPO_SKIP_SIDE` | Tripo 生 3D 参数 | 用 tripo 时必填 KEY |
| `HUNYUAN_API_KEY` `HUNYUAN_BASE_URL` `HUNYUAN_MODEL` `HUNYUAN_FACE` | 混元生 3D 参数 | 用 hunyuan 时必填 KEY |

### 依赖清单

| 模块 | 清单文件 | 主要依赖 |
|---|---|---|
| 前端 | `frontend/package.json` + `package-lock.json` | Vue 3、Vite、Element Plus、Tailwind、Three.js、MediaPipe、ECharts、Leaflet |
| 主站后端 | `backend/requirements.txt` | FastAPI、Uvicorn、SQLAlchemy、PyMySQL、JWT、OpenAI SDK、Redis、ChromaDB |
| 试穿旧版 | `tryon_service/requirements-core.txt` / `-ai.txt` / `-gpu.txt` / `-mysql.txt` / `-dev.txt` | FastAPI、OpenCV、MediaPipe、NumPy、Pillow、aiomysql、onnxruntime |
| 试穿新版 | 无 | Node 18+ 内置模块（`http`/`fetch`/`fs`），零第三方依赖 |

安装命令：

```bash
cd frontend && npm ci                 # 或 npm install
cd backend && pip install -r requirements.txt
cd tryon_service && pip install -r requirements-core.txt
# 需要 GPU 推理时再加 -r requirements-gpu.txt；接 MySQL 时加 -r requirements-mysql.txt
```

## 生产部署

Nginx 关键规则（节选自 `yisu_nginx.conf`，与线上实况镜像）：

```nginx
server {
    listen 80;
    server_name 47.93.14.11;
    root /www/wwwroot/yisu/frontend/dist;
    client_max_body_size 20m;

    # 试穿旧版 sidecar：前缀比 /api/ 长，nginx 取最长匹配，平台接口不受影响
    location /api/v1/outbox/ { limit_req zone=tryon_outbox burst=20 nodelay;
                               proxy_pass http://127.0.0.1:8010/api/v1/outbox/; }
    location /api/v1/        { limit_req zone=tryon burst=5 nodelay;          # 20r/m 按 IP 限流
                               proxy_pass http://127.0.0.1:8010/api/v1/;
                               proxy_read_timeout 300s; }
    location /tryon-assets/  { proxy_pass http://127.0.0.1:8010/tryon-assets/; expires 7d; }

    location /api/           { proxy_pass http://127.0.0.1:8765/api/;
                               proxy_read_timeout 120s; }
    location /uploads/       { alias /www/wwwroot/yisu/backend/uploads/; }
    location /museum/api/    { proxy_pass http://127.0.0.1:8000/api/; }
    location /               { try_files $uri $uri/ /index.html; }
}
```

- 试穿新版走 `/fitview-api/*` → `127.0.0.1:8787/api/*`，该 location 写在服务器那份配置里（本仓镜像未含），本地调试可直接访问 `http://127.0.0.1:8787/api/health`
- 前端构建产物与服务器 `dist` 逐字节一致（入口 `assets/index-sdE5I1_y.js`）
- `yisu-backend`（8765）、`yisu-tryon`（8010）为 systemd 常驻服务，改动后 `systemctl restart yisu-backend yisu-tryon`
- 静态资源改动只需替换 `dist` 与 `public`，无需重启；`yisu_nginx.conf` 是从服务器回拉的镜像，**不要整体推回服务器**（服务器版另有 `/museum/api/`、`/fitview-api/` 等 location）

## 账号体系

| 角色 | 权限 |
|---|---|
| 普通用户 | 浏览、发帖、问答、收藏 |
| 管理员 | 普通用户权限 + 下架/恢复帖子 + 用户管理 |
| 超级管理员 | 全部权限 + 任命/降级管理员，且不可被降级 |

## 开发过程与提交历史

仓库保留完整线性历史，未压缩、未重写：**36 条提交**（2026-10-15 至 2026-11-17），里程碑 tag `pre-tryon-merge`。

| 阶段 | 时间 | 提交 | 内容 |
|---|---|---|---|
| 基线 | 10-15 | `e09964a` | 平台既有功能入库（534 文件 / +35185 行） |
| 试穿集成 P1–P5 | 10-16 | `25aede9` → `cfa3cff` | 独立 sidecar → 数据库合表 → 前端接入 → 静态面拆分 `/tryon-assets`、`/tryon-results` → 文档 |
| 上线部署 | 10-16/17 | `7688442`、`607a6e2` | 生产 MySQL 打通、CV 依赖锁定、`person_source` 下架与删除链路、结果 TTL 清理 timer |
| 功能迭代 | 10-29/30 | `df49579` → `1a61bc4` | 导航统一、社区权限、AI 识纹样、改名「衣源溯起」与新 logo、hero 视频去 poster |
| 11 月收尾 | 11-17 | `c80097e` → `88aac30` | 地理口径与古图面板、纹样搭配过滤、面料编号体系、档案编号越界修复、工艺流程图补齐、`fitview-server` 入仓 |

完整清单见 [衣源溯起_Git提交历史.txt] 或执行：

```bash
git log --oneline --date=short --pretty="%ad %h %s"
```

## 团队

**衣源溯起项目组**

- 项目定位：传智杯 AI Web 应用挑战赛参赛作品
- 主题：华夏服饰文化数字化溯源与复原

## 说明

本项目仅用于学习交流与比赛展示，不用于商业用途。仓库不含任何真实密钥，`.env` 需按 `.env.example` 自行配置。
