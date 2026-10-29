# 衣溯 · 华夏衣冠志

> AI 驱动的历代服饰数字化溯源、复原与传承平台

**衣冠有史，华服可溯。**

从先秦的冕服深衣，到清代的旗装补褂；从出土实物到传世文献，每一件华夏服饰都有迹可循、有史可查。

## 项目简介

「衣溯」是面向中国传统服饰文化的 AI Web 应用，通过大语言模型、多模态视觉识别和 Three.js 3D 技术，构建一套可交互的华夏服饰数字档案与复原体验系统。

## 核心功能

| 模块 | 说明 |
|---|---|
| 📜 档案 | 9 朝服饰时间轴，93 条服饰与配饰档案，含形制、材质、源流、文化寓意 |
| 🧵 面料 | 31 种传统面料工艺档案，含工艺流程、诗文、实物图 |
| 🏺 纹样 | 传统纹样库，AI 识纹样（上传图片自动识别朝代/形制/纹样） |
| 👘 衣冠 | 服饰与配饰九卷图谱：服饰、衣制、头饰、手饰、颈饰、随身、耳饰、足饰、腰佩 |
| 🏛️ 博物馆 | Three.js 3D 虚拟展厅，漫游式浏览历代服饰复原 |
| 👗 虚拟试穿 | MediaPipe 实时试穿，上传照片试穿汉服 |
| 🕐 时空图谱 | 朝代时间轴交互图谱 |
| 💬 溯源问答 | 接入豆包大模型，多轮对话解答服饰文化问题 |
| 👥 社区 | 用户发帖、评论、点赞，管理员审核下架机制 |
| 🎭 传承 | 6 项非遗技艺档案，含完整工序、传承人信息 |

## 技术架构

```
┌─────────────────────────────────────────┐
│            前端 (Vue 3 + Vite)          │
│  Element Plus / Tailwind / Three.js    │
│  MediaPipe / GSAP / ECharts            │
├─────────────────────────────────────────┤
│           后端 (FastAPI + Python)       │
│  SQLAlchemy / PyMySQL / JWT 鉴权       │
│  火山方舟豆包大模型 (LLM + Vision)      │
├─────────────────────────────────────────┤
│         数据层 (MySQL 8.0)             │
│  服饰档案 / 用户 / 社区 / 问答记录      │
└─────────────────────────────────────────┘
```

- **前端**：Vue 3 + Vite + Vue Router + Pinia + Element Plus + Tailwind CSS + Three.js + MediaPipe
- **后端**：FastAPI + Uvicorn + SQLAlchemy + PyMySQL + JWT + OpenAI SDK（兼容火山方舟）
- **AI**：火山方舟豆包大模型（`doubao-seed-character-260628`）+ 视觉模型（`doubao-seed-1.6-vision-250815`）
- **部署**：阿里云 ECS + Nginx + systemd

## 环境要求

- Node.js >= 18
- Python >= 3.10
- MySQL >= 8.0
- 推荐使用虚拟环境（venv）

## 快速启动

### 1. 克隆仓库

```bash
git clone <仓库地址>
cd yisu-ai-platform
```

### 2. 后端

```bash
cd backend
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt

# 复制环境变量模板并填写
cp .env.example .env
```

编辑 `.env`：

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

启动后端：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
```

### 3. 前端

```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173 即可预览。

### 4. 独立页面

衣冠（accessories）、传承（heritage）、博物馆（museum）为独立静态页面，位于 `frontend/public/` 下，部署时直接拷贝到 Nginx 静态目录即可。

## 目录结构

```
yisu-ai-platform/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── api/             # 路由：档案/面料/纹样/社区/用户/AI问答/识纹样
│   │   ├── core/            # 配置、安全、数据库
│   │   ├── models/          # SQLAlchemy 数据模型
│   │   └── services/         # 业务逻辑
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   ├── components/      # 通用组件
│   │   ├── store/           # Pinia 状态管理
│   │   ├── router/          # 路由
│   │   └── assets/          # 样式、图片
│   ├── public/
│   │   ├── accessories/       # 衣冠独立页
│   │   ├── heritage/        # 传承独立页
│   │   └── museum/          # 博物馆 Three.js 子项目
│   └── package.json
└── README.md
```

## 账号体系

| 角色 | 权限 |
|---|---|
| 普通用户 | 浏览、发帖、问答、收藏 |
| 管理员 | 普通用户权限 + 下架/恢复帖子 + 用户管理 |
| 超级管理员 | 全部权限 + 任命/降级管理员 + 不可被降级 |

## 团队

**衣溯项目组**

- 项目定位：传智杯 AI Web 应用挑战赛参赛作品
- 主题：华夏服饰文化数字化溯源与复原

## 开源协议

本项目仅用于学习交流与比赛展示，不用于商业用途。
