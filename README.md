# 衣溯AI · 华夏服饰溯源与复原平台

AI 驱动、史料约束、可溯源、可复原、可交互式创作的华夏历代服饰数字溯源与文化复原平台  
（AI Web 网页开发挑战赛作品）。

## 技术栈

| 层级 | 技术                                                                                         |
| -- | ------------------------------------------------------------------------------------------ |
| 前端 | Vue 3 + Vite + TypeScript、Element Plus、Pinia、Vue Router、Three.js、ECharts、Leaflet + D3、GSAP |
| 后端 | FastAPI + SQLAlchemy 2.0 + JWT/bcrypt + Celery + Redis                                     |
| 数据 | MySQL 8.0（19 张表）、ChromaDB（向量检索）、Neo4j（知识图谱，可选）                                             |
| AI | DeepSeek / 通义千问（OpenAI 兼容）、Stable Diffusion + ControlNet、HanLP NER                         |

## 目录结构

```
yisu-ai-platform/
├── backend/
│   ├── app/
│   │   ├── main.py            # FastAPI 入口（九大模块路由装配）
│   │   ├── api/               # 九大模块 + 时空推演模拟器路由
│   │   ├── ai_engine/         # GraphRAG/第一人称对话/版型校验/时空推演/多模态复原/NER/Celery
│   │   ├── core/              # 配置、鉴权
│   │   ├── db/                # 数据库引擎、19 张表模型
│   │   └── services/          # 业务服务（预留）
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/             # 九大模块页面
│   │   ├── components/        # SimulatorPanel 等公共组件
│   │   ├── utils/             # Canvas纸样编辑 / Three.js试穿 / ECharts推演
│   │   ├── api/               # axios 封装
│   │   ├── store/             # Pinia
│   │   └── router/
│   └── package.json
└── database/
    └── init.sql               # 建库建表 + 种子数据
```

## 九大模块 ↔ 路由 ↔ 页面

| # | 模块                 | 后端前缀             | 前端页面                            |
| - | ------------------ | ---------------- | ------------------------------- |
| 1 | 文博资讯溯源首页           | `/api/home`      | `views/HomeIndex.vue`           |
| 2 | 衣溯AI核心档案（AI第一人称对话） | `/api/archive`   | `views/CostumeArchive.vue`      |
| 3 | 千年衣脉时间轴            | `/api/timeline`  | `views/TimeLine.vue`            |
| 4 | 服饰出土地理热力图          | `/api/geomap`    | `views/GeoHeatMap.vue`          |
| 5 | 交互式服饰版型制作工坊        | `/api/workshop`  | `views/PatternWorkshop.vue`     |
| 6 | AI 智能溯源问答          | `/api/aiqa`      | `views/AiQaPage.vue`            |
| 7 | 国风文化共治社区           | `/api/community` | `views/CommunityIndex.vue`      |
| 8 | 用户中心与权限体系          | `/api/user`      | `views/UserCenter.vue`          |
| 9 | 文化传承生成模块           | `/api/heritage`  | `views/HeritageGenerate.vue`    |
| ＋ | 时空推演模拟器（创新点四）      | `/api/simulator` | `components/SimulatorPanel.vue` |

## 快速启动

### 方式 A · 演示模式（免安装 MySQL，即开即用）

> 当前工程已切换为**正式模式**（`USE_DEMO_DATA=false`）。演示模式作为开发调试用，
> 将 `.env` 中 `USE_DEMO_DATA` 改回 `true` 即可回退（SQLite 演示库，含种子数据）。

### 方式 B · 正式模式（当前运行方式 · MySQL 8.0 已启用）

本机已安装 MySQL 8.0.44（`C:\mysql`，数据目录 `C:\mysql\data`），
`backend/.env` 当前配置：

```ini
USE_DEMO_DATA=false     # 关闭演示
USE_SQLITE_PROD=false   # 连接 MySQL 8.0（本机已装好，端口 3306）
MYSQL_PASSWORD=yisu_ai_2026
```

数据库 `yisu_ai`（19 张表 + 权威初始数据）在启动时由后端自动建表导入（幂等）。
MySQL 未运行时执行 `启动衣溯AI.bat` 会自动拉起。

> 若部署环境没有 MySQL：把 `USE_SQLITE_PROD` 改回 `true` 即退回本地正式库
> （`backend/data/yisu_prod.db`），功能一致。

### 大模型 Key（可选，正式模式强烈建议）

在 `backend/.env` 填写 `LLM_API_KEY`（DeepSeek 或通义千问，`sk-` 开头）。
未配置时 AI 以**离线知识库模式**运行：ChromaDB 向量检索 + 史料切片直答，
回答仍可溯源、不编造；配置后由 DeepSeek/通义千问生成完整回答。

### 演示账号

| 用户名 | 密码 | 角色 |
| -- | -- | -- |
| `admin` | `yisu2026` | 管理员（内容审核、用户管理） |
| `demo` | `yisu2026` | 普通用户 |

### 冒烟测试

```bash
cd backend
.\.venv\Scripts\python.exe _smoke_demo.py   # 19 项全接口测试（后端需已启动）
```

## AI 能力接入说明

| 能力       | 配置项（.env）                      | 未配置时的行为             |
| -------- | ------------------------------ | ------------------- |
| 大模型问答/摘要 | `LLM_API_KEY` / `LLM_BASE_URL` | 离线知识库直答：ChromaDB 检索 + 史料切片拼接，可溯源不编造 |
| 向量检索     | `EMBED_API_KEY`                | 本地哈希向量（确定性检索，链路可用）       |
| 复原图像     | `SD_API_URL`                   | 返回 mock 图地址与溯源档案卡   |
| 视频生成     | `VIDEO_GEN_API_URL`            | 留空                  |
| 资讯 NER   | spaCy 模型 + 词典双引擎          | 模型未下载时自动回退词典规则 |

## 12 分钟答辩演示链路

1. 首页（模块1）→ 2. 唐代大袖衫档案 + AI 第一人称对话（模块2）→ 3. 时间轴（模块3）  
   → 4. 出土地图（模块4）→ 5. 版型工坊：编辑纸样 → 史料校验 → 3D 试穿 → AI 复原（模块5）  
   → 6. 问答对比宋褙子/唐大袖衫（模块6）→ 7. 社区作品与勘误（模块7）→ 8. 用户中心（模块8）  
   → 9. 学习方案与分享卡片（模块9）；其间插入时空推演模拟器拖动参数（创新点四）。
